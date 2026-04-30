# direct DB write → db_proxy

**Path:** `theigors/rules/preferred_paths/direct-db-write`
**Updated:** 2026-04-29 by cc-sprint

applies_when: plan or diff writes raw psycopg2 INSERT/UPDATE against any igor table (not memory_palace, not test fixtures)
deprecated: raw psycopg2.connect + execute for business logic writes
preferred: PGDatabaseProxy (make_home_proxy / make_local_proxy) or the relevant domain helper (cortex.store, etc.)
why: db_proxy enforces search_path isolation, logs queries, and respects IGOR_HOME_DB_URL routing; raw writes silently target the wrong schema under test
