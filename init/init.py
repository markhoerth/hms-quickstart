"""
hms-quickstart / init/init.py

Creates 6 assets in proof_db on a single HMS (thrift://hms:9083)
using Trino SQL only — no Spark, no S3A classloader issues.

Assets:
  1. trips_parquet    Hive managed table, Parquet format
  2. trips_orc        Hive managed table, ORC format
  3. trips_csv        Hive external table, CSV (raw file in MinIO)
  4. trips_iceberg    Iceberg managed table
  5. v_expensive      Hive view  (trips_parquet WHERE amount > 20)
  6. v_iceberg_rides  Iceberg view (trips_iceberg with renamed columns)
"""

import trino
import time

SEP = "=" * 62

def banner(msg):
    print(f"\n{SEP}\n  {msg}\n{SEP}")

def run(cur, sql, label):
    try:
        cur.execute(sql)
        cur.fetchall()
        print(f"  [ok] {label}")
    except Exception as e:
        msg = str(e).lower()
        if "already exists" in msg or "already has rows" in msg:
            print(f"  [skip] {label} (already exists)")
        else:
            print(f"  [err] {label}: {e}")
            raise

def connect():
    return trino.dbapi.connect(
        host="trino",
        port=8080,
        user="admin",
        http_scheme="http",
    )

banner("HMS QUICKSTART — Init")
print("Trino:  http://trino:8080")
print("HMS:    thrift://hms:9083  (PostgreSQL backend)")
print("Store:  s3a://warehouse/   (MinIO)")


# ── Setup: schemas ────────────────────────────────────────────────────

conn = connect()
cur = conn.cursor()

banner("Creating schemas")
run(cur, "CREATE SCHEMA IF NOT EXISTS hive_catalog.proof_db "
         "WITH (location = 's3a://warehouse/proof_db')",
    "hive_catalog.proof_db")
run(cur, "CREATE SCHEMA IF NOT EXISTS iceberg_catalog.proof_db",
    "iceberg_catalog.proof_db")


# ── 1. Parquet table ──────────────────────────────────────────────────

banner("1. trips_parquet  (Hive / Parquet)")
run(cur, """
    CREATE TABLE IF NOT EXISTS hive_catalog.proof_db.trips_parquet (
        id     BIGINT,
        event  VARCHAR,
        amount DOUBLE
    ) WITH (format = 'PARQUET')
""", "create trips_parquet")
run(cur, """
    INSERT INTO hive_catalog.proof_db.trips_parquet VALUES
        (1, 'login',    0.00),
        (2, 'purchase', 49.99),
        (3, 'refund',  -49.99),
        (4, 'purchase', 89.99),
        (5, 'logout',   0.00)
""", "insert rows")


# ── 2. ORC table ──────────────────────────────────────────────────────

banner("2. trips_orc  (Hive / ORC)")
run(cur, """
    CREATE TABLE IF NOT EXISTS hive_catalog.proof_db.trips_orc (
        id     BIGINT,
        event  VARCHAR,
        amount DOUBLE
    ) WITH (format = 'ORC')
""", "create trips_orc")
run(cur, """
    INSERT INTO hive_catalog.proof_db.trips_orc
    SELECT * FROM hive_catalog.proof_db.trips_parquet
""", "insert rows from trips_parquet")


# ── 3. External CSV table ─────────────────────────────────────────────
banner("3. trips_csv  (Hive external / CSV)")
run(cur, """
    CREATE TABLE IF NOT EXISTS hive_catalog.proof_db.trips_csv (
        id     VARCHAR,
        event  VARCHAR,
        amount VARCHAR
    ) WITH (
        format = 'CSV',
        external_location = 's3a://warehouse/proof_db/trips_csv/',
        csv_separator = ','
    )
""", "create trips_csv (external)")
run(cur, """
    INSERT INTO hive_catalog.proof_db.trips_csv
    SELECT CAST(id AS VARCHAR), event, CAST(amount AS VARCHAR)
    FROM hive_catalog.proof_db.trips_parquet
""", "insert rows")


# ── 4. Iceberg table ──────────────────────────────────────────────────

banner("4. trips_iceberg  (Iceberg)")
run(cur, """
    CREATE TABLE IF NOT EXISTS iceberg_catalog.proof_db.trips_iceberg (
        id     BIGINT,
        event  VARCHAR,
        amount DOUBLE
    )
""", "create trips_iceberg")
run(cur, """
    INSERT INTO iceberg_catalog.proof_db.trips_iceberg
    SELECT * FROM hive_catalog.proof_db.trips_parquet
""", "insert rows from trips_parquet")


# ── 5. Hive view ──────────────────────────────────────────────────────

banner("5. v_expensive  (Hive view)")
run(cur, """
    CREATE OR REPLACE VIEW hive_catalog.proof_db.v_expensive AS
    SELECT id, event, amount
    FROM hive_catalog.proof_db.trips_parquet
    WHERE amount > 20
""", "create v_expensive")


# ── 6. Iceberg view ───────────────────────────────────────────────────

banner("6. v_iceberg_rides  (Iceberg view)")
run(cur, """
    CREATE OR REPLACE VIEW iceberg_catalog.proof_db.v_iceberg_rides AS
    SELECT id AS ride_id, event AS activity, amount AS fare
    FROM iceberg_catalog.proof_db.trips_iceberg
""", "create v_iceberg_rides")


# ── Verification ──────────────────────────────────────────────────────

banner("Verification — querying all 6 assets")

def query(sql, label):
    cur.execute(sql)
    rows = cur.fetchall()
    print(f"\n  [{label}]  ({len(rows)} rows)")
    for r in rows:
        print(f"    {r}")

query("SHOW TABLES FROM hive_catalog.proof_db",    "hive_catalog.proof_db tables  [connector: hive]")
query("SHOW TABLES FROM iceberg_catalog.proof_db", "iceberg_catalog.proof_db tables  [connector: iceberg]")
query("SELECT * FROM hive_catalog.proof_db.trips_parquet ORDER BY id",    "trips_parquet   [hive connector / Parquet format]")
query("SELECT * FROM hive_catalog.proof_db.trips_orc ORDER BY id",        "trips_orc       [hive connector / ORC format]")
query("SELECT * FROM hive_catalog.proof_db.trips_csv ORDER BY id",        "trips_csv       [hive connector / CSV external]")
query("SELECT * FROM iceberg_catalog.proof_db.trips_iceberg ORDER BY id", "trips_iceberg   [iceberg connector / Iceberg format]")
query("SELECT * FROM hive_catalog.proof_db.v_expensive ORDER BY id",      "v_expensive     [hive connector / Hive view over trips_parquet]")
query("SELECT * FROM iceberg_catalog.proof_db.v_iceberg_rides ORDER BY ride_id", "v_iceberg_rides [iceberg connector / Iceberg view over trips_iceberg]")
query("""
    SELECT p.id, p.event, p.amount AS parquet_amt, i.amount AS iceberg_amt
    FROM hive_catalog.proof_db.trips_parquet p
    JOIN iceberg_catalog.proof_db.trips_iceberg i ON p.id = i.id
    ORDER BY p.id
""", "cross-format JOIN  [hive connector × iceberg connector, same HMS]")

banner("INIT COMPLETE")
print("""
  All 6 assets registered in thrift://hms:9083 / proof_db.

  Trino shells:
    hive_catalog.proof_db.trips_parquet
    hive_catalog.proof_db.trips_orc
    hive_catalog.proof_db.trips_csv
    iceberg_catalog.proof_db.trips_iceberg
    hive_catalog.proof_db.v_expensive
    iceberg_catalog.proof_db.v_iceberg_rides

  Run: make trino-sql
""")

cur.close()
conn.close()
