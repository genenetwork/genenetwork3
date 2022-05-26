"""Menu generation code for the data in the dropdowns in the index page."""

from typing import Tuple
from functools import reduce

from gn3.db.species import get_all_species

def gen_dropdown_json(conn):
    """
    Generates and outputs (as json file) the data for the main dropdown menus on
    the home page.
    """
    species = get_all_species(conn)
    groups = get_groups(conn, tuple(row[0] for row in species))
    types = get_types(conn, groups)
    datasets = get_datasets(conn, types)
    return dict(species=species,
                groups=groups,
                types=types,
                datasets=datasets)

def get_groups(conn, species_names: Tuple[str, ...]):
    """Build groups list"""
    with conn.cursor() as cursor:
        query = (
            "SELECT InbredSet.Name, InbredSet.FullName, "
            "IFNULL(InbredSet.Family, 'None'), "
            "Species.Name AS species_name "
            "FROM Species "
            "INNER JOIN InbredSet ON InbredSet.SpeciesId = Species.Id "
            "WHERE Species.Name IN "
            f"({', '.join(['%s']*len(species_names))}) "
            "GROUP BY InbredSet.Name "
            "ORDER BY IFNULL(InbredSet.FamilyOrder, InbredSet.FullName) ASC, "
            "IFNULL(InbredSet.Family, InbredSet.FullName) ASC, "
            "InbredSet.FullName ASC, "
            "InbredSet.MenuOrderId ASC")
        cursor.execute(query, tuple(species_names))
        results = cursor.fetchall()

    def __organise_by_species(acc, row):
        family_name = f"Family:{str(row[2])}"
        species_name = row[3]
        key_exists = bool(acc.get(species_name, False))
        if not key_exists:
            return {
                **acc,
                species_name: [[str(row[0]), str(row[1]), family_name],]
            }

        return {
            **acc,
            species_name: acc[species_name] + [
                [str(row[0]), str(row[1]), family_name],]
        }

    return reduce(__organise_by_species, results, {})

def get_types(conn, groups):
    """Build types list"""
    types = {}

    for species, group_dict in list(groups.items()):
        types[species] = {}
        for group_name, _group_full_name, _family_name in group_dict:
            if phenotypes_exist(conn, group_name):
                types[species][group_name] = [
                    ("Phenotypes", "Traits and Cofactors", "Phenotypes")]
            if genotypes_exist(conn, group_name):
                if group_name in types[species]:
                    types[species][group_name] += [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
                else:
                    types[species][group_name] = [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
            if group_name in types[species]:
                types_list = build_types(conn, species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] += types_list
            else:
                types_list = build_types(conn, species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] = types_list
                else:
                    types[species].pop(group_name, None)
                    groups[species] = list(
                        group for group in groups[species]
                        if group[0] != group_name)
    return types

def phenotypes_exist(conn, group_name):
    "Check whether phenotypes exist for the given group"
    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Name FROM PublishFreeze "
             "WHERE PublishFreeze.Name = %s"),
            (group_name + "Publish",))
        results = cursor.fetchone()
        return bool(results)

def genotypes_exist(conn, group_name):
    "Check whether genotypes exist for the given group"
    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Name FROM GenoFreeze " +
             "WHERE GenoFreeze.Name = %s"),
            (group_name + "Geno",))
        results = cursor.fetchone()
        return bool(results)

def build_types(conn, species, group):
    """Fetches tissues

    Gets the tissues with data for this species/group
    (all types except phenotype/genotype are tissues)
    """
    query = (
        "SELECT DISTINCT Tissue.Name "
        "FROM ProbeFreeze, ProbeSetFreeze, InbredSet, "
        "Tissue, Species WHERE Species.Name = %s "
        "AND Species.Id = InbredSet.SpeciesId AND "
        "InbredSet.Name = %s AND ProbeFreeze.TissueId = "
        "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id "
        "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
        "ORDER BY Tissue.Name")
    results = []
    with conn.cursor() as cursor:
        cursor.execute(query, (species, group))
        for result in cursor.fetchall():
            if bool(result):
                these_datasets = build_datasets(conn, species, group, result[0])
                if len(these_datasets) > 0:
                    results.append([
                        str(result[0]), str(result[0]), "Molecular Traits"])

    return results

def get_datasets(conn, types):
    """Build datasets list"""
    datasets = {}
    for species, group_dict in list(types.items()):
        datasets[species] = {}
        for group, type_list in list(group_dict.items()):
            datasets[species][group] = {}
            for type_name in type_list:
                these_datasets = build_datasets(
                    conn, species, group, type_name[0])
                if bool(these_datasets):
                    datasets[species][group][type_name[0]] = these_datasets

    return datasets

def build_datasets(conn, species, group, type_name):
    """Gets dataset names from database"""
    dataset_text = dataset_value = None
    datasets = []
    with conn.cursor() as cursor:
        if type_name == "Phenotypes":
            cursor.execute(
                ("SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, "
                 "PublishFreeze.FullName FROM InfoFiles, PublishFreeze, "
                 "InbredSet WHERE InbredSet.Name = %s AND "
                 "PublishFreeze.InbredSetId = InbredSet.Id AND "
                 "InfoFiles.InfoPageName = PublishFreeze.Name "
                 "ORDER BY PublishFreeze.CreateTime ASC"), (group,))
            results = cursor.fetchall()
            if bool(results):
                for result in results:
                    dataset_id = str(result[0])
                    dataset_value = str(result[1])
                    dataset_text = str(result[2])
                    if group == 'MDP':
                        dataset_text = "Mouse Phenome Database"

                    datasets.append([dataset_id, dataset_value, dataset_text])
            else:
                cursor.execute(
                    ("SELECT PublishFreeze.Name, PublishFreeze.FullName "
                     "FROM PublishFreeze, InbredSet "
                     "WHERE InbredSet.Name = %s AND "
                     "PublishFreeze.InbredSetId = InbredSet.Id "
                     "ORDER BY PublishFreeze.CreateTime ASC"), (group,))
                result = cursor.fetchone()
                dataset_id = "None"
                dataset_value = str(result[0])
                dataset_text = str(result[1])
                datasets.append([dataset_id, dataset_value, dataset_text])

        elif type_name == "Genotypes":
            cursor.execute(
                ("SELECT InfoFiles.GN_AccesionId "
                 "FROM InfoFiles, GenoFreeze, InbredSet "
                 "WHERE InbredSet.Name = %s AND "
                 "GenoFreeze.InbredSetId = InbredSet.Id AND "
                 "InfoFiles.InfoPageName = GenoFreeze.ShortName "
                 "ORDER BY GenoFreeze.CreateTime "
                 "DESC"), (group,))
            results = cursor.fetchone()
            dataset_id = "None"
            if bool(results):
                dataset_id = str(results[0])

            dataset_value = f"{group}Geno"
            dataset_text = f"{group} Genotypes"
            datasets.append([dataset_id, dataset_value, dataset_text])

        else:  # for mRNA expression/ProbeSet
            cursor.execute(
                ("SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, "
                 "ProbeSetFreeze.FullName FROM ProbeSetFreeze, "
                 "ProbeFreeze, InbredSet, Tissue, Species WHERE "
                 "Species.Name = %s AND Species.Id = "
                 "InbredSet.SpeciesId AND InbredSet.Name = %s "
                 "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                 "AND Tissue.Name = %s AND ProbeFreeze.TissueId = "
                 "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id "
                 "AND ProbeSetFreeze.public > 0 "
                 "ORDER BY -ProbeSetFreeze.OrderList DESC, "
                 "ProbeSetFreeze.CreateTime "
                 "DESC"), (species, group, type_name))
            results = cursor.fetchall()
            datasets = []
            for dataset_info in results:
                this_dataset_info = []
                for info in dataset_info:
                    this_dataset_info.append(str(info))
                datasets.append(this_dataset_info)

    return datasets
