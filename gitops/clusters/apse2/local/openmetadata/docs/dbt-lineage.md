# dbt transformation and lineage

A dbt project builds analytics models in Oracle from the `APP` tables. OpenMetadata ingests the
dbt artifacts and draws table- and column-level lineage between them.

```text
APP.CUSTOMERS ───▶ stg_customers ───┬──▶ FCT_ORDERS ───▶ DIM_CUSTOMERS
APP.ORDERS ──────▶ stg_orders ──────┤         ▲
APP.ORDER_ITEMS ─▶ stg_order_items ─┴─────────┼──────▶ FCT_PRODUCT_SALES
APP.PRODUCTS ────▶ stg_products ──────────────┴──────────────▲
              (materialized views)             (tables, schema ANALYTICS)
```

The transformation lives in its own Argo CD app (`gitops/clusters/apse2/local/dbt`, namespace
`dbt`), next to `oracle`. OpenMetadata ingestion only reads the artifacts it publishes.

## Pieces

| What | Where |
|------|-------|
| Argo CD app `dbt` | `dbt/app.yaml` |
| dbt project (`dbt_project.yml`, `profiles.yml`) | `dbt/manifests/project/` → ConfigMap `dbt-project` |
| dbt models, sources, descriptions | `dbt/manifests/models/` → ConfigMap `dbt-models` |
| dbt runner | CronJob `dbt-run` (`dbt/manifests/cronjob.yaml`) |
| Cached virtualenv + published artifacts | PVC `dbt-data` (`venv/` and `artifacts/` subPaths) |
| Artifact server | Deployment + Service `dbt-artifacts` (`dbt/manifests/artifacts.yaml`) |
| Oracle + dbt ingestion workflows | `openmetadata/ingestion/oracle-workflow.yaml` |
| Ingestion runner | CronJob `oracle-metadata-ingestion` (`openmetadata/ingestion/oracle-cronjob.yaml`) |
| Oracle schema `ANALYTICS` | `oracle/manifests/initdb-configmap.yaml` (`03-analytics-schema.sh`) |
| `ANALYTICS` password | `ANALYTICS_PASSWORD` in `oracle/manifests/secrets.enc.yaml`, same value as `DBT_ORACLE_PASSWORD` in `dbt/manifests/secrets.enc.yaml` |

## Flow (both CronJobs run every 5 minutes)

1. **`dbt-run`** (namespace `dbt`, `python:3.12-slim`): installs `dbt-oracle==1.9.4` into `/venv`
   on the first run only, then `dbt run` + `dbt docs generate` as Oracle user `ANALYTICS`. The
   staging models are materialized views, recreated on every run; the marts are tables. On success
   `manifest.json` and `catalog.json` are moved into the artifacts directory; a failed run leaves
   the previous artifacts in place.
2. **`dbt-artifacts`** serves them at
   `http://dbt-artifacts.dbt.svc.cluster.local/{manifest,catalog}.json`.
3. **`oracle-metadata-ingestion`** (namespace `openmetadata`):
   - Oracle metadata workflow: ingests schemas `APP` and `ANALYTICS` into service `oracle_local`.
   - dbt workflow: downloads the artifacts over HTTP, matches dbt nodes to those tables and adds
     lineage (from `depends_on` and the compiled SQL), column lineage, model SQL and descriptions
     from `models.yml`.

`dbt-data` is a `local-path` (ReadWriteOnce) volume shared by the CronJob and the artifact server.
This works because the cluster has a single node; on a multi-node cluster use an RWX volume or
object storage instead.

## One-time setup on an existing Oracle database

`03-analytics-schema.sh` only runs when the Oracle volume is empty. On the current database, create
the user once (already done on the local cluster):

```bash
export SOPS_AGE_KEY_FILE=$PWD/sops-age-key.txt
PW=$(sops decrypt --extract '["stringData"]["ANALYTICS_PASSWORD"]' \
  gitops/clusters/apse2/local/oracle/manifests/secrets.enc.yaml)
kubectl -n oracle exec -i oracle-0 -- sqlplus -s / as sysdba <<EOF
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;
CREATE USER ANALYTICS IDENTIFIED BY "$PW" QUOTA UNLIMITED ON USERS;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE MATERIALIZED VIEW TO ANALYTICS;
GRANT SELECT ON APP.CUSTOMERS TO ANALYTICS;
GRANT SELECT ON APP.PRODUCTS TO ANALYTICS;
GRANT SELECT ON APP.ORDERS TO ANALYTICS;
GRANT SELECT ON APP.ORDER_ITEMS TO ANALYTICS;
EXIT
EOF
unset PW
```

Adding `ANALYTICS_PASSWORD` to the StatefulSet restarts the Oracle pod once when Argo CD syncs.

## Adding or changing a model

1. Add the `.sql` file to `dbt/manifests/models/` (models are materialized views by default; use
   `{{ config(materialized='table') }}` for tables). Reference upstreams with `ref()` / `source()`
   so lineage is captured.
2. List the file under `dbt-models` in `dbt/manifests/kustomization.yaml`.
3. A new `APP` source table also needs `GRANT SELECT ON APP.<table> TO ANALYTICS` and an entry in
   `models/sources.yml`.
4. Push; the next `dbt-run` builds it and the next ingestion run picks it up.

## Viewing the lineage

In OpenMetadata open `oracle_local > freepdb1 > analytics > FCT_ORDERS` (or `DIM_CUSTOMERS`,
`FCT_PRODUCT_SALES`) and select the **Lineage** tab; expand the nodes to see column lineage. The
**dbt** tab shows the model SQL.

## Troubleshooting

- **`analytics` tables disappear / show as deleted**: the Oracle workflow must include
  `(?i)^analytics$` in `schemaFilterPattern`; with `markDeletedSchemas: true` any run without it
  soft-deletes the schema.
- **dbt step of the ingestion fails to fetch the manifest**: `dbt-run` has not succeeded yet; check
  `kubectl -n dbt logs job/<latest dbt-run job>`.
- **`ORA-01031: insufficient privileges` creating a materialized view**: `ANALYTICS` is missing
  `CREATE MATERIALIZED VIEW`; run the grant above.
- **`Unable to ingest owner from DBT ... APP / ANALYTICS`** warnings: dbt reports the Oracle schema
  owner as model owner and OpenMetadata has no user with that name. Harmless.
- **Force a reinstall of dbt**: change `REQ` in the `dbt-run` CronJob.
