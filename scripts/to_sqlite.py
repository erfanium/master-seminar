import os
import sys
from core import sql
from cutevariant.core.readerfactory import create_reader

if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]


# File paths
IN_PATH = f"{BASE_PATH}/02_filtered/data.vcf"

OUT_DIR = f"{BASE_PATH}/04_sqlite"
os.makedirs(OUT_DIR, exist_ok=True)


OUT_PATH = os.path.join(OUT_DIR, "data.db")


conn = sql.get_sql_connection(OUT_PATH)
with create_reader(IN_PATH) as reader:
    sql.import_reader(conn, reader, None, None, None, [], [], print)
