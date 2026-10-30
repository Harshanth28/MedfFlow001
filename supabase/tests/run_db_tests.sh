#!/usr/bin/env bash
# MedFlow Step 2 — apply migrations + seeds to a PostgreSQL database and run assertions.
#
# Usage:
#   DATABASE_URL=postgres://... supabase/tests/run_db_tests.sh   # existing (NON-production) database
#   supabase/tests/run_db_tests.sh                               # throw-away local cluster (needs initdb/pg_ctl)
#
# The seeds are run TWICE to prove they are idempotent.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP=""

cleanup() {
  if [[ -n "$TMP" ]]; then
    "$PGBIN/pg_ctl" -D "$TMP/data" -m fast stop >/dev/null 2>&1 || true
    rm -rf "$TMP"
  fi
}
trap cleanup EXIT

if [[ -z "${DATABASE_URL:-}" ]]; then
  PGBIN="${PGBIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"
  TMP="$(mktemp -d)"
  "$PGBIN/initdb" -D "$TMP/data" -U postgres -A trust >/dev/null
  "$PGBIN/pg_ctl" -D "$TMP/data" -o "-p 55432 -k $TMP -c listen_addresses=''" -l "$TMP/log" -w start >/dev/null
  DATABASE_URL="postgresql://postgres@/postgres?host=$TMP&port=55432"
  echo "Started throw-away PostgreSQL $("$PGBIN/postgres" --version | awk '{print $3}')"
fi

run() { psql "$DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -f "$1"; echo "  ok  $(basename "$1")"; }

echo "== migrations"
for f in "$ROOT"/supabase/migrations/*.sql; do run "$f"; done
echo "== migrations again (must be safe to re-run)"
for f in "$ROOT"/supabase/migrations/*.sql; do run "$f"; done
echo "== seeds (pass 1)"
run "$ROOT/data/hospital_seed.sql"; run "$ROOT/data/baby_seed.sql"
echo "== seeds (pass 2, idempotency)"
run "$ROOT/data/hospital_seed.sql"; run "$ROOT/data/baby_seed.sql"
echo "== assertions"
psql "$DATABASE_URL" -X -q -v ON_ERROR_STOP=1 -f "$ROOT/supabase/tests/db_assertions.sql"
