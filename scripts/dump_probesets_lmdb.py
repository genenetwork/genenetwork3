import MySQLdb
import numpy as np
import lmdb
import json
import click
import logging
import os
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional
from collections import defaultdict
from multiprocessing import Pool, cpu_count
import time
from datetime import datetime, date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DTYPE = np.float64
MISSING_VALUE = "x"
LMDB_MAP_SIZE = 10 * 1024**3  # 10 GB
DEFAULT_PORT = 3306


@dataclass(frozen=True)
class ProbeSetMatrix:
    """Immutable container for the ProbeSet expression matrix and its labels.

    Rows = traits (ProbeSets), columns = strains (row-major / C-order in memory).
    """
    matrix: np.ndarray  # shape (n_traits, n_strains), dtype <f8
    traits: list[str]  # ProbeSet IDs or Names
    strains: list[str]  # Strain IDs
    se_matrix: Optional[np.ndarray] = None  # optional SE values, same shape


@dataclass(frozen=True)
class SerializedProbeSetMatrix:
    """Byte-level representation ready to be written to LMDB."""
    matrix_bytes: bytes
    metadata_bytes: bytes
    se_matrix_bytes: Optional[bytes] = None


@dataclass(frozen=True)
class DBConnectionParams:
    """Parsed connection parameters — never printed in full."""
    host: str
    user: str
    password: str
    database: str
    port: int


@dataclass(frozen=True)
class DatasetInfo:
    """Dataset metadata from ProbeSetFreeze table."""
    id: int
    name: str
    full_name: str
    short_name: str
    create_time: str  # ISO format date string
    public: int  # 0 or 1


def parse_connection_params(sql_uri: str) -> DBConnectionParams:
    """Parse a mysql:// URI into connection parameters."""
    parsed = urlparse(sql_uri)
    host = parsed.hostname or "127.0.0.1"

    # Force TCP if localhost to avoid unix socket connection
    if host == "localhost":
        host = "127.0.0.1"

    return DBConnectionParams(
        host=host,
        user=parsed.username or "",
        password=parsed.password or "",
        database=parsed.path.lstrip("/"),
        port=parsed.port or DEFAULT_PORT,
    )


def open_db_connection(params: DBConnectionParams):
    """Open a MySQL connection from parsed parameters."""
    logger.info(
        "Connecting to %s@%s:%s/%s",
        params.user,
        params.host,
        params.port,
        params.database,
    )

    return MySQLdb.connect(
        host=params.host,
        user=params.user,
        passwd=params.password,
        db=params.database,
        port=params.port
    )


def open_lmdb(db_path: str, *, create: bool = False) -> lmdb.Environment:
    """Open (or create) an LMDB environment."""
    return lmdb.open(db_path, map_size=LMDB_MAP_SIZE, create=create)


def fetch_all_probeset_datasets(sql_uri: str) -> list[DatasetInfo]:
    """Query MySQL for all available public ProbeSet datasets.

    Returns:
        List of DatasetInfo objects with full metadata.
    """
    params = parse_connection_params(sql_uri)
    datasets = []

    query = """
        SELECT 
            Id,
            Name,
            FullName,
            ShortName,
            CreateTime,
            public
        FROM ProbeSetFreeze
        ORDER BY Id
    
    """

    with open_db_connection(params) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        for dataset_id, name, full_name, short_name, create_time, public in cursor.fetchall():
            # Convert date to ISO format string
            if isinstance(create_time, date):
                create_time_str = create_time.isoformat()
            else:
                create_time_str = str(create_time) if create_time else None

            datasets.append(DatasetInfo(
                id=dataset_id,
                name=name,
                full_name=full_name or name,
                short_name=short_name or name,
                create_time=create_time_str,
                public=public
            ))

    return datasets


def fetch_dataset_info(dataset_id: int, sql_uri: str) -> Optional[DatasetInfo]:
    """Fetch metadata for a specific dataset.

    Returns:
        DatasetInfo object or None if not found.
    """
    params = parse_connection_params(sql_uri)

    query = """
        SELECT 
            Id,
            Name,
            FullName,
            ShortName,
            CreateTime,
            public
        FROM ProbeSetFreeze
        WHERE Id = %s
    """

    with open_db_connection(params) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (dataset_id,))
        result = cursor.fetchone()

        if result is None:
            return None

        dataset_id, name, full_name, short_name, create_time, public = result

        # Convert date to ISO format string
        if isinstance(create_time, date):
            create_time_str = create_time.isoformat()
        else:
            create_time_str = str(create_time) if create_time else None

        return DatasetInfo(
            id=dataset_id,
            name=name,
            full_name=full_name or name,
            short_name=short_name or name,
            create_time=create_time_str,
            public=public
        )


def fetch_dataset_range(dataset_id: int, sql_uri: str) -> tuple[int, int, int]:
    """Get the DataId range for a dataset.

    Returns:
        (min_data_id, max_data_id, total_count)
    """
    params = parse_connection_params(sql_uri)

    query = """
        SELECT 
            MIN(psxr.DataId), 
            MAX(psxr.DataId), 
            COUNT(DISTINCT psxr.DataId)
        FROM ProbeSetXRef psxr
        WHERE psxr.ProbeSetFreezeId = %s
    """

    with open_db_connection(params) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (dataset_id,))
        result = cursor.fetchone()

    return result if result[0] is not None else (None, None, 0)


def process_batch(args):
    """Process a single batch of DataIds in parallel.

    Returns dict with batch info and data.
    """
    dataset_id, start_id, end_id, batch_num, sql_uri = args

    params = parse_connection_params(sql_uri)
    conn = MySQLdb.connect(
        host=params.host,
        user=params.user,
        passwd=params.password,
        db=params.database,
        port=params.port
    )
    cursor = conn.cursor()

    try:
        # Fetch expression values
        value_query = """
            SELECT 
                psd.Id as DataId,
                psd.StrainId,
                psd.value
            FROM ProbeSetXRef psxr
            JOIN ProbeSetData psd ON psxr.DataId = psd.Id
            WHERE psxr.ProbeSetFreezeId = %s
              AND psxr.DataId BETWEEN %s AND %s
            ORDER BY psd.Id, psd.StrainId
        """

        batch_start = time.time()
        cursor.execute(value_query, (dataset_id, start_id, end_id))
        value_results = cursor.fetchall()

        # Fetch SE values
        se_query = """
            SELECT 
                psse.DataId,
                psse.StrainId,
                psse.error
            FROM ProbeSetXRef psxr
            JOIN ProbeSetSE psse ON psxr.DataId = psse.DataId
            WHERE psxr.ProbeSetFreezeId = %s
              AND psxr.DataId BETWEEN %s AND %s
            ORDER BY psse.DataId, psse.StrainId
        """

        cursor.execute(se_query, (dataset_id, start_id, end_id))
        se_results = cursor.fetchall()

        batch_time = time.time() - batch_start

        return {
            'batch_num': batch_num,
            'start_id': start_id,
            'end_id': end_id,
            'value_data': value_results,
            'se_data': se_results,
            'time': batch_time,
            'success': True
        }

    except Exception as e:
        return {
            'batch_num': batch_num,
            'start_id': start_id,
            'end_id': end_id,
            'value_data': [],
            'se_data': [],
            'time': 0,
            'success': False,
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()


def fetch_probeset_data(
    dataset_id: int,
    sql_uri: str,
    batch_size: int = 5000,
    num_workers: int = 4
) -> tuple[set[str], dict[int, dict[str, float]], dict[int, dict[str, float]], dict[int, str]]:
    """Fetch all ProbeSet expression values and SE for a dataset using parallel processing.

    Returns:
        strains     – set of all strain IDs encountered
        datasets    – {data_id: {strain_id: value}}
        se_data     – {data_id: {strain_id: se_value}}
        trait_names – {data_id: probeset_name}
    """
    logger.info(f"Fetching ProbeSet data for dataset {dataset_id}...")

    # Get the range of DataIds
    min_data_id, max_data_id, total_data_ids = fetch_dataset_range(
        dataset_id, sql_uri)

    if min_data_id is None:
        logger.warning(f"No data found for dataset {dataset_id}")
        return set(), {}, {}, {}

    logger.info(
        f"DataId range: {min_data_id:,} to {max_data_id:,} ({total_data_ids:,} traits)")

    # Create batch ranges
    batch_ranges = []
    current_id = min_data_id
    batch_num = 0

    while current_id <= max_data_id:
        batch_end = min(current_id + batch_size - 1, max_data_id)
        batch_num += 1
        batch_ranges.append(
            (dataset_id, current_id, batch_end, batch_num, sql_uri))
        current_id = batch_end + 1

    total_batches = len(batch_ranges)
    logger.info(
        f"Processing {total_batches:,} batches with {num_workers} workers...")

    # Process batches in parallel
    datasets: dict[int, dict[str, float]] = defaultdict(dict)
    se_data: dict[int, dict[str, float]] = defaultdict(dict)
    strains: set[str] = set()
    batches_processed = 0
    start_time = time.time()

    with Pool(processes=num_workers) as pool:
        for result in pool.imap_unordered(process_batch, batch_ranges, chunksize=1):
            batches_processed += 1

            if result['success']:
                # Process value data
                for data_id, strain_id, value in result['value_data']:
                    datasets[data_id][str(strain_id)] = float(value)
                    strains.add(str(strain_id))

                # Process SE data
                for data_id, strain_id, se_value in result['se_data']:
                    se_data[data_id][str(strain_id)] = float(se_value)

                # Progress tracking
                elapsed = time.time() - start_time
                batches_remaining = total_batches - batches_processed

                if batches_processed > 0:
                    avg_time_per_batch = elapsed / batches_processed
                    eta_seconds = avg_time_per_batch * batches_remaining
                    eta_time = datetime.now().timestamp() + eta_seconds
                    eta_str = datetime.fromtimestamp(
                        eta_time).strftime('%H:%M:%S')
                else:
                    eta_str = "calculating..."

                logger.info(
                    f"Batch {batches_processed}/{total_batches} | "
                    f"DataIds: {result['start_id']:,}-{result['end_id']:,} | "
                    f"Time: {result['time']:.2f}s | "
                    f"ETA: {eta_str}"
                )
            else:
                logger.error(
                    f"Batch {result['batch_num']} FAILED: {result['error']}")

    # Fetch ProbeSet names (trait names)
    logger.info("Fetching ProbeSet names...")
    params = parse_connection_params(sql_uri)
    trait_names = {}

    with open_db_connection(params) as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                psxr.DataId,
                ps.Name
            FROM ProbeSetXRef psxr
            JOIN ProbeSet ps ON psxr.ProbeSetId = ps.Id
            WHERE psxr.ProbeSetFreezeId = %s
        """
        cursor.execute(query, (dataset_id,))
        for data_id, probeset_name in cursor.fetchall():
            trait_names[data_id] = probeset_name

    # Fetch strain ID to name mapping
    logger.info("Fetching strain names...")
    strain_id_to_name: dict[str, str] = {}
    with open_db_connection(params) as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT s.Id, s.Name
            FROM Strain s
            JOIN ProbeSetData psd ON psd.StrainId = s.Id
            JOIN ProbeSetXRef psxr ON psd.Id = psxr.DataId
            WHERE psxr.ProbeSetFreezeId = %s
        """
        cursor.execute(query, (dataset_id,))
        for strain_id, strain_name in cursor.fetchall():
            strain_id_to_name[str(strain_id)] = strain_name

    total_time = time.time() - start_time
    logger.info(f"Fetch complete in {total_time/60:.2f} minutes")
    logger.info(f"Found {len(strains)} strains, {len(datasets)} traits")

    return strains, dict(datasets), dict(se_data), trait_names, strain_id_to_name


def _to_float(value) -> float:
    """Cast a single value to float64, defaulting to NaN on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return float("nan")


def _fill_missing(
    trait_data: dict[str, float],
    strains: list[str],
    default: str = MISSING_VALUE,
) -> list[float]:
    """Return one row (all strains) for a trait, filling gaps with *default*."""
    return [_to_float(trait_data.get(s, default)) for s in strains]


def build_probeset_matrix(
    datasets: dict[int, dict[str, float]],
    se_data: dict[int, dict[str, float]],
    trait_names: dict[int, str],
    strains: set[str],
) -> ProbeSetMatrix:
    """Convert the raw dataset dict into a ProbeSetMatrix with optional SE values."""
    sorted_strains = sorted(strains)  # deterministic column order
    data_ids = sorted(datasets.keys())  # deterministic row order

    # Map DataIds to ProbeSet names
    traits = [trait_names.get(data_id, str(data_id)) for data_id in data_ids]

    # Build value matrix
    value_rows = [_fill_missing(datasets[data_id], sorted_strains)
                  for data_id in data_ids]

    # Build SE matrix if we have SE data
    se_matrix = None
    if se_data:
        se_rows = [_fill_missing(se_data.get(
            data_id, {}), sorted_strains) for data_id in data_ids]
        se_matrix = np.array(se_rows, dtype=DTYPE)

    return ProbeSetMatrix(
        matrix=np.array(value_rows, dtype=DTYPE),
        traits=traits,
        strains=sorted_strains,
        se_matrix=se_matrix,
    )


def build_metadata(probeset: ProbeSetMatrix, dataset_info: DatasetInfo, strain_id_to_name: dict[str, str] = None) -> dict:
    """Derive metadata from the ProbeSetMatrix and dataset info."""
    rows, columns = probeset.matrix.shape
    
    # Build strain index mapping for fast lookup
    strain_indices = {strain: idx for idx, strain in enumerate(probeset.strains)}
    
    metadata = {
        "rows": rows,
        "columns": columns,
        "dtype": str(probeset.matrix.dtype),
        "order": "C",
        "endian": "little",
        "traits": probeset.traits,
        "strains": [strain_id_to_name.get(s, s) for s in probeset.strains] if strain_id_to_name else probeset.strains,
        "strain_indices": strain_indices,
        "transposed": False,
        "has_se": probeset.se_matrix is not None,
        "dataset_id": dataset_info.id,
        "dataset_name": dataset_info.name,
        "dataset_fullname": dataset_info.full_name,
        "dataset_shortname": dataset_info.short_name,
        "create_time": dataset_info.create_time,
        "public": dataset_info.public,
    }
    
    # Optionally include ID to name mapping for reference
    if strain_id_to_name:
        metadata["strain_id_to_name"] = strain_id_to_name
    
    return metadata


def serialize(probeset: ProbeSetMatrix, dataset_info: DatasetInfo, strain_id_to_name: dict[str, str] = None) -> SerializedProbeSetMatrix:
    """Serialize a ProbeSetMatrix into the byte-blobs LMDB will store."""
    se_bytes = None
    if probeset.se_matrix is not None:
        se_bytes = probeset.se_matrix.tobytes(order="C")

    return SerializedProbeSetMatrix(
        matrix_bytes=probeset.matrix.tobytes(order="C"),
        metadata_bytes=json.dumps(build_metadata(
            probeset, dataset_info, strain_id_to_name)).encode("utf-8"),
        se_matrix_bytes=se_bytes,
    )


def read_metadata(txn: lmdb.Transaction) -> dict:
    """Read and decode the metadata JSON from an open transaction."""
    raw = txn.get(b"probeset_metadata")
    if raw is None:
        raise KeyError("Key 'probeset_metadata' not found in LMDB")
    return json.loads(raw.decode("utf-8"))


def reconstruct_matrix(txn: lmdb.Transaction) -> ProbeSetMatrix:
    """Reconstruct a ProbeSetMatrix from an open LMDB transaction."""
    metadata = read_metadata(txn)
    raw_bytes = txn.get(b"probeset_matrix")
    if raw_bytes is None:
        raise KeyError("Key 'probeset_matrix' not found in LMDB")

    matrix = np.frombuffer(raw_bytes, dtype=metadata["dtype"]).reshape(
        metadata["rows"], metadata["columns"]
    )

    # Try to load SE matrix if it exists
    se_matrix = None
    if metadata.get("has_se", False):
        se_raw = txn.get(b"probeset_se_matrix")
        if se_raw is not None:
            se_matrix = (
                np.frombuffer(se_raw, dtype=metadata["dtype"])
                .reshape(metadata["rows"], metadata["columns"])
                .copy()
            )

    return ProbeSetMatrix(
        matrix=matrix.copy(),
        traits=metadata["traits"],
        strains=metadata["strains"],
        se_matrix=se_matrix,
    )


def write_to_lmdb(lmdb_path: str, serialized: SerializedProbeSetMatrix) -> None:
    """Persist the serialized matrix + metadata into LMDB."""
    with open_lmdb(lmdb_path, create=True) as env:
        with env.begin(write=True) as txn:
            txn.put(b"probeset_matrix", serialized.matrix_bytes)
            txn.put(b"probeset_metadata", serialized.metadata_bytes)
            if serialized.se_matrix_bytes is not None:
                txn.put(b"probeset_se_matrix", serialized.se_matrix_bytes)
    logger.info("Matrix written to %s", lmdb_path)


def prepare_and_dump(
    dataset_id: int,
    sql_uri: str,
    lmdb_path: str,
    batch_size: int = 5000,
    num_workers: int = 4
) -> ProbeSetMatrix:
    """Orchestrate fetch → build → serialize → write."""
    # Fetch dataset info
    dataset_info = fetch_dataset_info(dataset_id, sql_uri)
    if dataset_info is None:
        raise ValueError(f"Dataset ID {dataset_id} not found")

    logger.info(
        f"Dataset: {dataset_info.name} (Created: {dataset_info.create_time}, Public: {dataset_info.public})")

    # Fetch data
    strains, datasets, se_data, trait_names, strain_id_to_name = fetch_probeset_data(
        dataset_id, sql_uri, batch_size, num_workers
    )

    # Build matrix
    probeset = build_probeset_matrix(datasets, se_data, trait_names, strains)

    # Serialize and write (lmdb_path should already include dataset name)
    write_to_lmdb(lmdb_path, serialize(probeset, dataset_info, strain_id_to_name))

    return probeset


def load_from_lmdb(lmdb_path: str) -> ProbeSetMatrix:
    """Read and reconstruct the full ProbeSetMatrix from LMDB."""
    with open_lmdb(lmdb_path) as env:
        with env.begin() as txn:
            return reconstruct_matrix(txn)


def fetch_single_trait(lmdb_path: str, trait_name: str) -> dict[str, float]:
    """Fetch one trait's values for all strains without rebuilding the full matrix."""
    with open_lmdb(lmdb_path) as env:
        with env.begin() as txn:
            metadata = read_metadata(txn)
            traits = metadata["traits"]

            if trait_name not in traits:
                raise KeyError(
                    f"Trait '{trait_name}' not found in stored metadata")

            row_idx = traits.index(trait_name)
            dtype = np.dtype(metadata["dtype"])
            bytes_per_row = metadata["columns"] * dtype.itemsize
            start = row_idx * bytes_per_row

            raw = txn.get(b"probeset_matrix")
            row_values = np.frombuffer(
                raw, dtype=dtype, count=metadata["columns"], offset=start
            )

    return dict(zip(metadata["strains"], row_values.tolist()))


# CLI Commands

@click.group()
def cli():
    """ProbeSet LMDB toolbox."""


@cli.command("list-datasets")
@click.argument("sql_uri")
def list_datasets_cmd(sql_uri: str) -> None:
    """List all available public ProbeSet datasets in the database."""
    datasets = fetch_all_probeset_datasets(sql_uri)

    if not datasets:
        logger.warning("No public datasets found")
        return

    logger.info("Found %d public dataset(s):", len(datasets))

    # Print in a table format
    max_name_len = max(len(d.name) for d in datasets)
    max_short_len = max(len(d.short_name) for d in datasets)

    header = f"{'ID':<6}  {'Name':<{max_name_len}}  {'Short Name':<{max_short_len}}  {'Created':<12}  {'Public':<6}  Full Name"
    print(header)
    print("-" * len(header))

    for dataset in datasets:
        public_str = "Yes" if dataset.public else "No"
        create_str = dataset.create_time[:10] if dataset.create_time else "N/A"
        print(
            f"{dataset.id:<6}  "
            f"{dataset.name:<{max_name_len}}  "
            f"{dataset.short_name:<{max_short_len}}  "
            f"{create_str:<12}  "
            f"{public_str:<6}  "
            f"{dataset.full_name}"
        )


@cli.command("dump-dataset")
@click.argument("sql_uri")
@click.argument("lmdb_path", type=click.Path(file_okay=False, path_type=str))
@click.argument("dataset_id", type=int)
@click.option("--batch-size", default=5000, help="Batch size for processing (default: 5000)")
@click.option("--workers", default=4, help="Number of parallel workers (default: 4)")
def dump_dataset_cmd(
    sql_uri: str,
    lmdb_path: str,
    dataset_id: int,
    batch_size: int,
    workers: int
) -> None:
    """Fetch ProbeSet data from MySQL and write the matrix to LMDB.

    Example:
        python lmdb_probeset_matrix.py dump-dataset \\
            "mysql://user:pass@localhost/db_webqtl" \\
            /path/to/lmdb \\
            206 \\
            --batch-size 5000 \\
            --workers 4
    """
    # Get dataset info to construct proper path
    dataset_info = fetch_dataset_info(dataset_id, sql_uri)
    if dataset_info is None:
        logger.error(f"Dataset ID {dataset_id} not found")
        return
    
    # Construct path: lmdb_path/dataset_name
    lmdb_path = os.path.join(lmdb_path, dataset_info.name)
    os.makedirs(lmdb_path, exist_ok=True)
    
    prepare_and_dump(dataset_id, sql_uri, lmdb_path, batch_size, workers)


@cli.command("dump-all-datasets")
@click.argument("sql_uri")
@click.argument("lmdb_base_path", type=click.Path(file_okay=False, path_type=str))
@click.option("--batch-size", default=5000, help="Batch size for processing")
@click.option("--workers", default=4, help="Number of parallel workers")
@click.option("--skip-existing/--no-skip-existing", default=True)
def dump_all_datasets_cmd(
    sql_uri: str,
    lmdb_base_path: str,
    batch_size: int,
    workers: int,
    skip_existing: bool
) -> None:
    """Fetch all  ProbeSet datasets and dump each to its own LMDB directory."""
    datasets = fetch_all_probeset_datasets(sql_uri)

    if not datasets:
        logger.warning("No public datasets found")
        return

    logger.info("Found %d dataset(s) to dump", len(datasets))

    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, dataset_info in enumerate(datasets, 1):
        dataset_id = dataset_info.id
        lmdb_path = os.path.join(lmdb_base_path, dataset_info.name)

        logger.info("[%d/%d] Processing dataset: %s (ID: %d)",
                    idx, len(datasets), dataset_info.name, dataset_info.id)

        # Check if already exists
        if skip_existing and os.path.exists(lmdb_path):
            logger.info(
                "  → Skipping (directory already exists): %s", lmdb_path)
            skip_count += 1
            continue

        try:
            # Create the directory if needed
            os.makedirs(lmdb_path, exist_ok=True)

            # Dump this dataset
            prepare_and_dump(dataset_id, sql_uri,
                             lmdb_path, batch_size, workers)
            success_count += 1
        except Exception as e:
            logger.error("  → Failed to dump %s -id %s: %s",
                         dataset_info.name, dataset_info.id, e, exc_info=True)
            fail_count += 1

    # Summary
    logger.info("=" * 70)
    logger.info("Dump Summary:")
    logger.info("  Success: %d", success_count)
    logger.info("  Skipped: %d", skip_count)
    logger.info("  Failed:  %d", fail_count)
    logger.info("=" * 70)


@cli.command("print-matrix")
@click.argument("lmdb_path", type=click.Path(exists=True, file_okay=False, path_type=str))
def print_matrix_cmd(lmdb_path: str) -> None:
    """Read and print the ProbeSet matrix stored in LMDB."""
    probeset = load_from_lmdb(lmdb_path)
    rows, cols = probeset.matrix.shape
    logger.info("ProbeSetMatrix  rows(traits)=%d  cols(strains)=%d", rows, cols)
    print(probeset.matrix)


@cli.command("show-metadata")
@click.argument("lmdb_path", type=click.Path(exists=True, file_okay=False, path_type=str))
def show_metadata_cmd(lmdb_path: str) -> None:
    """Show the metadata stored in LMDB."""
    with open_lmdb(lmdb_path) as env:
        with env.begin() as txn:
            metadata = read_metadata(txn)

    print("Dataset Metadata:")
    print("=" * 60)
    print(f"Dataset ID:       {metadata.get('dataset_id', 'N/A')}")
    print(f"Dataset Name:     {metadata.get('dataset_name', 'N/A')}")
    print(f"Full Name:        {metadata.get('dataset_fullname', 'N/A')}")
    print(f"Short Name:       {metadata.get('dataset_shortname', 'N/A')}")
    print(f"Created:          {metadata.get('create_time', 'N/A')}")
    print(f"Public:           {'Yes' if metadata.get('public') else 'No'}")
    print()
    print(
        f"Matrix Shape:     {metadata['rows']} traits × {metadata['columns']} strains")
    print(f"Data Type:        {metadata['dtype']}")
    print(f"Has SE Matrix:    {'Yes' if metadata.get('has_se') else 'No'}")
    print(f"Transposed:       {'Yes' if metadata.get('transposed') else 'No'}")
    print("=" * 60)


@cli.command("list-traits")
@click.argument("lmdb_path", type=click.Path(exists=True, file_okay=False, path_type=str))
def list_traits_cmd(lmdb_path: str) -> None:
    """Print every trait name stored in the LMDB metadata."""
    with open_lmdb(lmdb_path) as env:
        with env.begin() as txn:
            metadata = read_metadata(txn)

    for trait in metadata["traits"]:
        click.echo(trait)


@cli.command("fetch-trait")
@click.argument("lmdb_path", type=click.Path(exists=True, file_okay=False, path_type=str))
@click.argument("trait_name")
@click.option("--json/--no-json", "as_json", default=False)
def fetch_trait_cmd(lmdb_path: str, trait_name: str, as_json: bool) -> None:
    """Fetch and print values for a single trait across all strains."""
    result = fetch_single_trait(lmdb_path, trait_name)

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        max_strain_len = max(len(s) for s in result)
        click.echo(f"{'Strain':<{max_strain_len}}  Value")
        click.echo(f"{'-' * max_strain_len}  -----")
        for strain, value in result.items():
            click.echo(f"{strain:<{max_strain_len}}  {value}")


if __name__ == "__main__":
    cli()
