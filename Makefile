.PHONY: up up-quick down restart logs logs-svc ps clean reset \
        init spark-proof trino-sql help

COMPOSE = docker compose

# ============================================================
# HMS Quickstart — Makefile
# ============================================================

## Build images and start all services (runs table init automatically)
up:
	$(COMPOSE) up -d --build
	@echo ""
	@echo "  Services starting (~2 min on first run):"
	@echo "    HMS    → localhost:9083  (thrift)"
	@echo "    Trino  → http://localhost:8080"
	@echo "    MinIO  → http://localhost:9001  (gravitino / gravitino123)"
	@echo ""
	@echo "  Table init runs automatically. Watch progress:"
	@echo "    make logs-svc SVC=init"
	@echo ""
	@echo "  Once init completes:"
	@echo "    make trino-sql"

## Start services without rebuilding or re-running init
up-quick:
	$(COMPOSE) up -d hms trino postgres minio
	@echo "Started. Run 'make init' to (re)create tables."

## Re-run the init container (recreates all tables from scratch)
init:
	$(COMPOSE) run --rm init

## Run the Spark proof — queries all 6 assets via single SparkSessionCatalog
spark-proof:
	$(COMPOSE) run --rm spark

## Stop all containers
down:
	$(COMPOSE) down

## Restart all services
restart:
	$(COMPOSE) restart

## Tail logs for all services
logs:
	$(COMPOSE) logs -f

## Tail logs for a specific service  (usage: make logs-svc SVC=init)
logs-svc:
	$(COMPOSE) logs -f $(SVC)

## Show running containers
ps:
	$(COMPOSE) ps

# -------------------------------------------------------
# SQL Shells
# -------------------------------------------------------

## Launch Trino SQL shell
trino-sql:
	docker exec -it hmsqs-trino \
	  trino --server http://localhost:8080 \
	        --user admin

# -------------------------------------------------------
# Cleanup
# -------------------------------------------------------

## Remove all containers and named volumes
clean:
	$(COMPOSE) down -v --remove-orphans

## Full reset: clean + prune dangling images
reset: clean
	docker image prune -f

# -------------------------------------------------------
# Help
# -------------------------------------------------------
help:
	@echo ""
	@echo "HMS Quickstart"
	@echo "=============="
	@echo ""
	@grep -E '^##' Makefile | sed 's/## /  /'
	@echo ""
	@echo "Examples:"
	@echo "  make up                   # build + start + init tables"
	@echo "  make up-quick             # start without rebuilding"
	@echo "  make init                 # recreate all tables"
	@echo "  make spark-proof          # run Spark proof queries"
	@echo "  make trino-sql            # Trino shell"
	@echo "  make logs-svc SVC=init    # watch init progress"
	@echo "  make logs-svc SVC=hms     # tail HMS logs"
	@echo "  make clean                # remove everything"
	@echo ""
