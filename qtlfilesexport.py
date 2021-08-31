"""
Test the qtlfiles export of traits files

Run with:

    env SQL_URI="mysql://<user>:<password>@<host>:<port>/db_webqtl" python3 qtlfilesexport.py

replacing the variables in the angled brackets with the appropriate values
"""
from gn3.computations.slink import slink
from gn3.db_utils import database_connector
from gn3.computations.heatmap import export_trait_data
from gn3.db.traits import retrieve_trait_data, retrieve_trait_info
from gn3.db.genotypes import build_genotype_file, load_genotype_samples
from gn3.computations.qtlreaper import random_string, generate_traits_file
from gn3.computations.heatmap import (
    cluster_traits,
    compute_heatmap_order,
    retrieve_strains_and_values)

TMPDIR = "tmp/qtltests"

def trait_fullnames():
    """Return sample names for traits"""
    return [
        "UCLA_BXDBXH_CARTILAGE_V2::ILM103710672",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM2260338",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM3140576",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM5670577",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM2070121",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM103990541",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM1190722",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM6590722",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM4200064",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM3140463"]

def main():
    """entrypoint function"""
    conn = database_connector()[0]
    threshold = 0
    traits = [
        retrieve_trait_info(threshold, fullname, conn)
        for fullname in trait_fullnames()]
    traits_data_list = [retrieve_trait_data(t, conn) for t in traits]
    genotype_filename = build_genotype_file(traits[0]["riset"])
    strains = load_genotype_samples(genotype_filename)
    exported_traits_data_list = [
        export_trait_data(td, strains) for td in traits_data_list]
    slinked = slink(cluster_traits(exported_traits_data_list))
    orders = compute_heatmap_order(slinked)
    strains_and_values = retrieve_strains_and_values(
        orders, strains, exported_traits_data_list)
    strains_values = strains_and_values[0][1]
    trait_values = [t[2] for t in strains_and_values]
    traits_filename = "{}/traits_test_file_{}.txt".format(
        TMPDIR, random_string(10))
    generate_traits_file(strains_values, trait_values, traits_filename)
    print("Generated file: {}".format(traits_filename))

if __name__ == "__main__":
    main()
