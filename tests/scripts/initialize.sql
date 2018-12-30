BEGIN;
CREATE SCHEMA IF NOT EXISTS "celsus_core" AUTHORIZATION postgres;
SET search_path TO celsus_core, public;
\i tests/scripts/library.sql
\i tests/scripts/book.sql
COMMIT;