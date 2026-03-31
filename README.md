# hms-quickstart

A minimal proof environment demonstrating that a single Hive Metastore (HMS)
can hold multiple table formats simultaneously, queryable by both Trino and Spark
through a single catalog connection.

## What this proves

> "Spark and Trino do not enforce one table type per catalog connection.
> The metastore is completely format-agnostic. Routing is handled transparently
> at the connector layer."

## Assets

All assets live in `proof_db` on a single HMS instance (`thrift://hms:9083`):

| Asset | Type | Format |
|-------|------|--------|
| `trips_parquet` | Managed table | Parquet |
| `trips_orc` | Managed table | ORC |
| `trips_csv` | External table | CSV |
| `trips_iceberg` | Managed table | Iceberg |
| `v_expensive` | View | Hive view over `trips_parquet` |
| `v_iceberg_rides` | View | Iceberg view over `trips_iceberg` |

## Services

| Service | Port | Description |
|---------|------|-------------|
| HMS | 9083 | Hive Metastore (PostgreSQL backend) |
| Trino | 8080 | Query engine |
| MinIO | 9001 | Object storage console (gravitino / gravitino123) |
| Spark | — | Proof job, exits after running queries |

## Trino catalogs (both point to the same HMS)

| Catalog | Connector | Notes |
|---------|-----------|-------|
| `hive_catalog` | `hive` | Parquet, ORC, CSV tables + views. Redirects Iceberg tables to `iceberg_catalog` automatically. |
| `iceberg_catalog` | `iceberg` | Iceberg table + Iceberg view |

## Quickstart

```bash
make up          # build, start, create all tables (~3 min first run)
make trino-sql   # open Trino shell
make spark-proof # run Spark proof queries against the same HMS
```

## Trino proof queries

```sql
-- Both catalogs see the same HMS namespace
SHOW TABLES FROM hive_catalog.proof_db;
SHOW TABLES FROM iceberg_catalog.proof_db;

-- Each format queryable
SELECT * FROM hive_catalog.proof_db.trips_parquet;
SELECT * FROM hive_catalog.proof_db.trips_orc;
SELECT * FROM hive_catalog.proof_db.trips_csv;
SELECT * FROM iceberg_catalog.proof_db.trips_iceberg;

-- Views
SELECT * FROM hive_catalog.proof_db.v_expensive;
SELECT * FROM iceberg_catalog.proof_db.v_iceberg_rides;

-- Cross-format join (the key result)
SELECT p.id, p.event, p.amount AS parquet_amt, i.amount AS iceberg_amt
FROM hive_catalog.proof_db.trips_parquet p
JOIN iceberg_catalog.proof_db.trips_iceberg i ON p.id = i.id;
```

## Spark proof

`make spark-proof` runs `spark/query.py` which connects via a single
`SparkSessionCatalog` to the same HMS and queries all 4 tables including
a cross-format JOIN between the Parquet and Iceberg tables.

Views are excluded from the Spark proof — views created by Trino are stored
in Presto wire format and are not readable by Spark. This is a cross-engine
view portability limitation, separate from the table format question.
Cross-engine view portability requires an Iceberg REST Catalog (IRC) in the path.

## Makefile targets

```
make up                   # build + start + create all tables
make up-quick             # start without rebuilding
make init                 # recreate all tables from scratch
make spark-proof          # run Spark proof queries
make trino-sql            # Trino interactive shell
make logs-svc SVC=hms     # tail a specific service log
make clean                # remove containers + volumes
```

## Relationship to Gravitino

This environment is intentionally Gravitino-free. It isolates the engine-layer
question from the catalog-layer question.

**What this proves:** Spark and Trino have no architectural constraint preventing
them from serving multiple table formats from a single HMS connection.

**Separate finding:** Gravitino's current HMS catalog connector enforces a single
table type per catalog connection. The target behavior for HMS and Glue catalogs in Gravitino
is what this environment demonstrates.
