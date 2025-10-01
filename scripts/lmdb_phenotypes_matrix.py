"""
Script file dumps classical phenotypes  to lmdb.
"""
"""
# create a temporary guix environment with all the dependencies
guix shell python-wrapper  python-mysql-connector-python python-lmdb  python-lmdb python-click python-numpy
# to dump the phenotypes to lmdb
python  dump_phenos_matrix.py  dump-phenotypes "mysql://webqtlout:webqtlout@localhost/db_webqtl"  "/home/kabui/test_lmdb_data"
# to print the phenotype matrix and metadata
python  dump_phenos_matrix.py   print-phenotype-matrix    "/home/kabui/test_lmdb_data"
"""
from numpy.testing import assert_array_equal
import numpy as np
import lmdb
import mysql.connector
from urllib.parse import urlparse
from pprint import pprint
from collections import defaultdict
from collections import OrderedDict
import click
import json


def make_db_connection(sql_uri, port=3306):
    """Function to create make a db_connection"""
    parsed_uri = urlparse(sql_uri)
    hostname = parsed_uri.hostname
    user = parsed_uri.username
    password = parsed_uri.password
    database = parsed_uri.path[1:]
    print(
        f"the hostname is {hostname} and the user is {user} password {password} and the db {database}")
    try:
        connection = mysql.connector.connect(
            host=hostname,
            user=user,
            password=password,
            database=database,
            port=port
        )
        return connection
    except mysql.connector.Error as err:
        raise err


def create_database(db_path: str) -> lmdb.Environment:
    """Create or open an LMDB environment."""
    return lmdb.open(db_path, map_size=100 * 1024 * 1024 * 1024, create=False)


def test_make_db_connection():
    """Test function to check in urlparse for the sql_uri works correctly."""
    assert make_db_connection(
        "mysql://webqtlout:webqtlout@localhost/db_webqtl") == {
            "host":  "localhost",
            "password":  "webqtlout",
            "user": "webqtlout",
            "database":  "db_webqtl"
    }


def sql_fetch():
    """Test sql fetch function to get all classical phenotype datasets """
    with make_db_connection("mysql://webqtlout:webqtlout@localhost/db_webqtl", "3306") as connect:
        cursor = connect.cursor()
        cursor.execute("""SELECT
        * FROM  PublishFreeze LIMIT 2""")
        return cursor.fetchall()


def fetch_phenotypes(dataset: str, sql_uri: str):
    """Functions queries for phenotypes belonging to a specific dataset
    TODO! make this generic
    """
    query = """
    SELECT PublishXRef.Id, Strain.Name, PublishData.Value
FROM
    PublishData
    INNER JOIN Strain ON PublishData.StrainId = Strain.Id
    INNER JOIN PublishXRef ON PublishData.Id = PublishXRef.DataId
    INNER JOIN PublishFreeze ON PublishXRef.InbredSetId = PublishFreeze.InbredSetId
LEFT JOIN PublishSE ON
    PublishSE.DataId = PublishData.Id AND
    PublishSE.StrainId = PublishData.StrainId
LEFT JOIN NStrain ON
    NStrain.DataId = PublishData.Id AND
    NStrain.StrainId = PublishData.StrainId
WHERE
    PublishFreeze.Name = "BXDPublish"  AND
    PublishFreeze.public > 0 AND
    PublishData.value IS NOT NULL AND
    PublishFreeze.confidentiality < 1
ORDER BY
    LENGTH(Strain.Name), Strain.Name
    """
    datasets = defaultdict(dict)
    strains = set()
    with make_db_connection(sql_uri) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        for (trait_id, strain_name, value) in results:
            # TODO  store the trait_ids as strings not ints
            datasets[trait_id][strain_name] = value
            strains.add(strain_name)
        return (strains, datasets)


def parse_phenotypes(data: dict, strains: list, missing_default="X"):
    """ Parse the strain if any is missing replacing with X.
    returns a key value with key as traits and values
    as an ordered dict of strains and values.
    """
    traits = []
    results = defaultdict(OrderedDict)
    for trait in data.keys():
        trait_strains = {}
        for strain in strains:
            trait_strains[strain] = data[trait].get(strain, missing_default)
        results[trait] = trait_strains
        traits.append(trait)
    return (generate_strain_rows(results), traits, strains)


def generate_strain_rows(data):
    """generate strain rows from strain dict """
    # target  [INNER loop] [OUTER loop]

    return [list(map(to_float, [strain_value for strain_name, strain_value in strain_dict.items()]))
            for trait, strain_dict in data.items()]


def to_float(x):
    """ Cast to floats64 or float.nan """
    try:
        return float(x)
    except ValueError:
        return float("nan")


@click.command(help="Dump the phenotypes  to lmdb requirements are sql db_path and the lmdb_path")
@click.argument(
    "sql_uri"
)
@click.argument(
    "lmdb_path",
    type=click.Path(exists=True, file_okay=False,
                    readable=True, path_type=str),
)
def dump_phenotypes(sql_uri: str, lmdb_path: str):
    """
    Function to dump the matrix to lmdb together with the metadata
    metadata expects traits treated as col_names and
    strains /individuals  treated as  row_names
    """
    # TODO~ assert that this is in the db for example assert db_name in bxdpublish else raise errors
    strains, dataset = fetch_phenotypes(
        "BXDPublish", sql_uri)
    matrix_rows, traits, strains = parse_phenotypes(
        data=dataset, strains=list(strains))
    matrix = np.matrix(matrix_rows, dtype="<f8")
    rows, columns = matrix.shape
    matrix_bytes = matrix.tobytes(order="C")
    metadata = {
        "rows": rows,
        "columns": columns,
        "dtype": "<f8",
        "order": "C",
        "endian": "little",
        "traits": traits,
        "transposed": False,
        "strains": strains  # mmmh! should these two be rows names / col_names generic???

    }
    with create_database(lmdb_path) as db:
        with db.begin(write=True) as txn:
            txn.put(b"pheno_matrix", matrix_bytes)
            txn.put(b"pheno_metadata", json.dumps(metadata).encode("utf-8"))
    return matrix


@click.command(help="Print the lmdb pheno dataset. ")
@click.argument(
    "lmdb_path",
    type=click.Path(exists=True, file_okay=False,
                    readable=True, path_type=str),
)
def print_phenotype_matrix(lmdb_path):
    """Function to print phenotype matrix"""
    with create_database(lmdb_path) as db:
        with db.begin(write=False) as txn:
            pheno_matrix_bytes = txn.get(b"pheno_matrix")
            pheno_metadata = txn.get(b"pheno_metadata").decode("utf-8")
            pheno_metadata = json.loads(pheno_metadata)
            rows, columns, dtype = (
                pheno_metadata["rows"],
                pheno_metadata["columns"],
                pheno_metadata.get("dtype", "<f8"))
            pheno_rows = np.frombuffer(pheno_matrix_bytes, dtype=dtype)
            pheno_matrix = pheno_rows.reshape(
                rows, columns)
            print(f"A Summary of the pheno  rows:{rows} and  cols:{columns}")
            pprint(pheno_matrix)
            return pheno_matrix


@click.command(help="Sanity check if the original matrix is same as reconstructed_matrix")
@click.argument(
    "sql_uri"
)
@click.argument(
    "lmdb_path",
    type=click.Path(exists=True, file_okay=False,
                    readable=True, path_type=str),


)
def sanity_check(sql_uri, lmdb_path):
    """Sanity check if dumped matrix is same as fetched matrix"""
    from click.testing import CliRunner
    runner = CliRunner()
    # to hacky probably separate logic from cli_tooling
    # TODO! add versioning  for the db
    dumped_matrix = runner.invoke(
        dump_phenotypes, [sql_uri, lmdb_path], standalone_mode=False)
    pprint_matrix = runner.invoke(print_phenotype_matrix, [
                                  lmdb_path], standalone_mode=False)
    assert_array_equal(dumped_matrix.return_value,
                       pprint_matrix.return_value)


@click.group()
def cli():
    pass


cli.add_command(dump_phenotypes)
cli.add_command(print_phenotype_matrix)
cli.add_command(sanity_check)

if __name__ == "__main__":
    cli()
