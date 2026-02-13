"""
Utility script to run SQL schema files against Supabase.
"""

import psycopg2
import sys
from pathlib import Path

# Connection config
DB_CONFIG = {
    "host": "db.pdbmcskznoaiybdiobje.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "guid-saltation-covet",
    "sslmode": "require"
}

def run_schema_file(file_path: Path):
    """Execute a SQL schema file."""
    print(f"Running: {file_path.name}")
    print("-" * 50)

    # Read SQL
    sql = file_path.read_text()

    # Connect and execute
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("SUCCESS!")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        return False
    finally:
        conn.close()

    return True

def main():
    schema_dir = Path(__file__).parent / "schema"

    # Get schema files in order
    schema_files = sorted(schema_dir.glob("*.sql"))

    if len(sys.argv) > 1:
        # Run specific file
        file_num = sys.argv[1]
        matching = [f for f in schema_files if f.name.startswith(file_num)]
        if matching:
            run_schema_file(matching[0])
        else:
            print(f"No schema file found starting with: {file_num}")
    else:
        # List available files
        print("Available schema files:")
        for f in schema_files:
            print(f"  {f.name}")
        print("\nUsage: python run_schema.py <number>")
        print("Example: python run_schema.py 01")

if __name__ == "__main__":
    main()
