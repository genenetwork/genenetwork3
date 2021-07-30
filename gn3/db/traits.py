"""This class contains functions relating to trait data manipulation"""
from typing import Any, Dict, Union


def get_trait_csv_sample_data(conn: Any,
                              trait_name: int, phenotype_id: int):
    """Fetch a trait and return it as a csv string"""
    sql = ("SELECT  Strain.Id, PublishData.Id, Strain.Name, "
           "PublishData.value, "
           "PublishSE.error, NStrain.count FROM "
           "(PublishData, Strain, PublishXRef, PublishFreeze) "
           "LEFT JOIN PublishSE ON "
           "(PublishSE.DataId = PublishData.Id AND "
           "PublishSE.StrainId = PublishData.StrainId) "
           "LEFT JOIN NStrain ON (NStrain.DataId = PublishData.Id AND "
           "NStrain.StrainId = PublishData.StrainId) WHERE "
           "PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND "
           "PublishData.Id = PublishXRef.DataId AND "
           "PublishXRef.Id = %s AND PublishXRef.PhenotypeId = %s "
           "AND PublishData.StrainId = Strain.Id Order BY Strain.Name")
    csv_data = ["Strain Id,Strain Name,Value,SE,Count"]
    publishdata_id = ""
    with conn.cursor() as cursor:
        cursor.execute(sql, (trait_name, phenotype_id,))
        for record in cursor.fetchall():
            (strain_id, publishdata_id,
             strain_name, value, error, count) = record
            csv_data.append(
                ",".join([str(val) if val else "x"
                          for val in (strain_id, strain_name,
                                      value, error, count)]))
    return f"# Publish Data Id: {publishdata_id}\n\n" + "\n".join(csv_data)


def update_sample_data(conn: Any,
                       strain_name: str,
                       strain_id: int,
                       publish_data_id: int,
                       value: Union[int, float, str],
                       error: Union[int, float, str],
                       count: Union[int, str]):
    """Given the right parameters, update sample-data from the relevant
    table."""
    STRAIN_ID_SQL: str = "UPDATE Strain SET Name = %s WHERE Id = %s"
    PUBLISH_DATA_SQL: str = ("UPDATE PublishData SET value = %s "
                             "WHERE StrainId = %s AND Id = %s")
    PUBLISH_SE_SQL: str = ("UPDATE PublishSE SET error = %s "
                           "WHERE StrainId = %s AND DataId = %s")
    N_STRAIN_SQL: str = ("UPDATE NStrain SET count = %s "
                         "WHERE StrainId = %s AND DataId = %s")

    updated_strains: int = 0
    updated_published_data: int = 0
    updated_se_data: int = 0
    updated_n_strains: int = 0

    with conn.cursor() as cursor:
        # Update the Strains table
        cursor.execute(STRAIN_ID_SQL, (strain_name, strain_id))
        updated_strains: int = cursor.rowcount
        # Update the PublishData table
        cursor.execute(PUBLISH_DATA_SQL,
                       (None if value == "x" else value,
                        strain_id, publish_data_id))
        updated_published_data: int = cursor.rowcount
        # Update the PublishSE table
        cursor.execute(PUBLISH_SE_SQL,
                       (None if error == "x" else error,
                        strain_id, publish_data_id))
        updated_se_data: int = cursor.rowcount
        # Update the NStrain table
        cursor.execute(N_STRAIN_SQL,
                       (None if count == "x" else count,
                        strain_id, publish_data_id))
        updated_n_strains: int = cursor.rowcount
    return (updated_strains, updated_published_data,
            updated_se_data, updated_n_strains)


def retrieve_trait_dataset_name(
        trait_type: str, threshold: int, name: str, connection: Any):
    """
    Retrieve the name of a trait given the trait's name

    This is extracted from the `webqtlDataset.retrieveName` function as is
    implemented at
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlDataset.py#L140-L169
    """
    columns = "Id, Name, FullName, ShortName{}".format(
        ", DataScale" if trait_type == "ProbeSet" else "")
    query = (
        "SELECT {columns} "
        "FROM {trait_type}Freeze "
        "WHERE "
        "public > %(threshold)s "
        "AND "
        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)").format(
            columns=columns, trait_type=trait_type)
    with connection.cursor() as cursor:
        cursor.execute(query, {"threshold": threshold, "name": name})
        return cursor.fetchone()


def retrieve_publish_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Publish` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L399-L421"""
    keys = (
        "Id", "PubMed_ID", "Pre_publication_description",
        "Post_publication_description", "Original_description",
        "Pre_publication_abbreviation", "Post_publication_abbreviation",
        "Lab_code", "Submitter", "Owner", "Authorized_Users", "Authors",
        "Title", "Abstract", "Journal", "Volume", "Pages", "Month", "Year",
        "Sequence", "Units", "comments")
    columns = (
        "PublishXRef.Id, Publication.PubMed_ID, "
        "Phenotype.Pre_publication_description, "
        "Phenotype.Post_publication_description, "
        "Phenotype.Original_description, "
        "Phenotype.Pre_publication_abbreviation, "
        "Phenotype.Post_publication_abbreviation, "
        "Phenotype.Lab_code, Phenotype.Submitter, Phenotype.Owner, "
        "Phenotype.Authorized_Users, CAST(Publication.Authors AS BINARY), "
        "Publication.Title, Publication.Abstract, Publication.Journal, "
        "Publication.Volume, Publication.Pages, Publication.Month, "
        "Publication.Year, PublishXRef.Sequence, Phenotype.Units, "
        "PublishXRef.comments")
    query = (
        "SELECT "
        "{columns} "
        "FROM "
        "PublishXRef, Publication, Phenotype, PublishFreeze "
        "WHERE "
        "PublishXRef.Id = %(trait_name)s AND "
        "Phenotype.Id = PublishXRef.PhenotypeId AND "
        "Publication.Id = PublishXRef.PublicationId AND "
        "PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND "
        "PublishFreeze.Id =%(trait_dataset_id)s").format(
            columns = columns)
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_id"]
            })
        return dict(zip((k.lower() for k in keys), cursor.fetchone()))

def retrieve_probeset_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `ProbeSet` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L424-L435"""
    keys = (
        "name", "symbol", "description", "probe_target_description", "chr",
        "mb", "alias", "geneid", "genbankid", "unigeneid", "omim",
        "refseq_transcriptid", "blatseq", "targetseq", "chipid", "comments",
        "strand_probe", "strand_gene", "probe_set_target_region", "proteinid",
        "probe_set_specificity", "probe_set_blat_score",
        "probe_set_blat_mb_start", "probe_set_blat_mb_end", "probe_set_strand",
        "probe_set_note_by_rw", "flag")
    query = (
        "SELECT "
        "{columns} "
        "FROM "
        "ProbeSet, ProbeSetFreeze, ProbeSetXRef "
        "WHERE "
        "ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND "
        "ProbeSetXRef.ProbeSetId = ProbeSet.Id AND "
        "ProbeSetFreeze.Name = %(trait_dataset_name)s AND "
        "ProbeSet.Name = %(trait_name)s").format(
            columns = ", ".join(["ProbeSet.{}".format(x) for x in keys]))
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_name"]
            })
        return dict(zip(keys, cursor.fetchone()))

def retrieve_geno_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Geno` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L438-L449"""
    keys = ("name", "chr", "mb", "source2", "sequence")
    query = (
        "SELECT "
        "{columns} "
        "FROM "
        "Geno, GenoFreeze, GenoXRef "
        "WHERE "
        "GenoXRef.GenoFreezeId = GenoFreeze.Id AND GenoXRef.GenoId = Geno.Id AND "
        "GenoFreeze.Name = %(trait_dataset_name)s AND "
        "Geno.Name = %(trait_name)s").format(
            columns = ", ".join(["Geno.{}".format(x) for x in keys]))
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name", "trait_dataset_name"]
            })
        return dict(zip(keys, cursor.fetchone()))

def retrieve_temp_trait_info(trait_data_source: Dict[str, Any], conn: Any):
    """Retrieve trait information for type `Temp` traits.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L450-452"""
    keys = ("name", "description")
    query = (
        "SELECT {columns} FROM Temp "
        "WHERE Name = %(trait_name)s").format(columns = ", ".join(keys))
    with conn.cursor() as cursor:
        cursor.execute(
            query,
            {
                k:v for k, v in trait_data_source.items()
                if k in ["trait_name"]
            })
        return dict(zip(keys, cursor.fetchone()))

def retrieve_trait_info(
        trait_type: str, trait_name: str, trait_dataset_id: int,
        trait_dataset_name: str, conn: Any, QTL = None):
    """Retrieves the trait information.

    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/base/webqtlTrait.py#L397-L456

    This function, or the dependent functions, might be incomplete as they are
    currently."""
    trait_info_function_table = {
        "Publish": retrieve_publish_trait_info,
        "ProbeSet": retrieve_probeset_trait_info,
        "Geno": retrieve_geno_trait_info,
        "Temp": retrieve_temp_trait_info
    }
    return trait_info_function_table[trait_type](
        {
            "trait_name": trait_name,
            "trait_dataset_id": trait_dataset_id,
            "trait_dataset_name":trait_dataset_name
        },
        conn)
