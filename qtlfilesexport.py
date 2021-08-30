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
    # strains = list(set([k for td in traits_data_list for k in td["data"].keys()]))
    strains = [# Use only the strains in the BXD.geno genotype file
        "BXD1", "BXD2", "BXD5", "BXD6", "BXD8", "BXD9", "BXD11", "BXD12",
        "BXD13", "BXD14", "BXD15", "BXD16", "BXD18", "BXD19", "BXD20", "BXD21",
        "BXD22", "BXD23", "BXD24", "BXD24a", "BXD25", "BXD27", "BXD28", "BXD29",
        "BXD30", "BXD31", "BXD32", "BXD33", "BXD34", "BXD35", "BXD36", "BXD37",
        "BXD38", "BXD39", "BXD40", "BXD41", "BXD42", "BXD43", "BXD44", "BXD45",
        "BXD48", "BXD48a", "BXD49", "BXD50", "BXD51", "BXD52", "BXD53", "BXD54",
        "BXD55", "BXD56", "BXD59", "BXD60", "BXD61", "BXD62", "BXD63", "BXD64",
        "BXD65", "BXD65a", "BXD65b", "BXD66", "BXD67", "BXD68", "BXD69",
        "BXD70", "BXD71", "BXD72", "BXD73", "BXD73a", "BXD73b", "BXD74",
        "BXD75", "BXD76", "BXD77", "BXD78", "BXD79", "BXD81", "BXD83", "BXD84",
        "BXD85", "BXD86", "BXD87", "BXD88", "BXD89", "BXD90", "BXD91", "BXD93",
        "BXD94", "BXD95", "BXD98", "BXD99", "BXD100", "BXD101", "BXD102",
        "BXD104", "BXD105", "BXD106", "BXD107", "BXD108", "BXD109", "BXD110",
        "BXD111", "BXD112", "BXD113", "BXD114", "BXD115", "BXD116", "BXD117",
        "BXD119", "BXD120", "BXD121", "BXD122", "BXD123", "BXD124", "BXD125",
        "BXD126", "BXD127", "BXD128", "BXD128a", "BXD130", "BXD131", "BXD132",
        "BXD133", "BXD134", "BXD135", "BXD136", "BXD137", "BXD138", "BXD139",
        "BXD141", "BXD142", "BXD144", "BXD145", "BXD146", "BXD147", "BXD148",
        "BXD149", "BXD150", "BXD151", "BXD152", "BXD153", "BXD154", "BXD155",
        "BXD156", "BXD157", "BXD160", "BXD161", "BXD162", "BXD165", "BXD168",
        "BXD169", "BXD170", "BXD171", "BXD172", "BXD173", "BXD174", "BXD175",
        "BXD176", "BXD177", "BXD178", "BXD180", "BXD181", "BXD183", "BXD184",
        "BXD186", "BXD187", "BXD188", "BXD189", "BXD190", "BXD191", "BXD192",
        "BXD193", "BXD194", "BXD195", "BXD196", "BXD197", "BXD198", "BXD199",
        "BXD200", "BXD201", "BXD202", "BXD203", "BXD204", "BXD205", "BXD206",
        "BXD207", "BXD208", "BXD209", "BXD210", "BXD211", "BXD212", "BXD213",
        "BXD214", "BXD215", "BXD216", "BXD217", "BXD218", "BXD219", "BXD220"
    ]
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
