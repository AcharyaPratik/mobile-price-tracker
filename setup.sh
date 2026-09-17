#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "▶ Project root: $PROJECT_ROOT"

# 1. folders
mkdir -p data/raw data/processed scripts/sources sql dags logs plugins reports
touch scripts/sources/__init__.py
echo "  ✅ folders created"

# 2. .env
if [ -f .env ]; then
    echo "  ℹ️  .env already exists — skipping"
else
    read -rsp "  Enter your Postgres password: " DB_PASSWORD
    echo
    cat > .env <<ENVEOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mobile_tracker
DB_USER=postgres
DB_PASSWORD=${DB_PASSWORD}
AIRFLOW_UID=$(id -u)
ENVEOF
    echo "  ✅ .env written"
fi

# 3. .gitignore
for line in ".env" "venv/" "__pycache__/" "*.pyc" \
            "logs/" "plugins/" \
            "data/raw/*.csv" "data/processed/*.csv" "reports/*.csv"; do
    grep -qxF "$line" .gitignore 2>/dev/null || echo "$line" >> .gitignore
done
echo "  ✅ .gitignore updated"

# 4. Postgres databases
if ! command -v psql >/dev/null 2>&1; then
    echo "  ❌ psql not found. Install Postgres and re-run."
    exit 1
fi

DB_USER=$(grep -E '^DB_USER=' .env | cut -d= -f2-)
DB_PASSWORD=$(grep -E '^DB_PASSWORD=' .env | cut -d= -f2-)
export PGPASSWORD="$DB_PASSWORD"

create_db() {
    local name="$1"
    if psql -U "$DB_USER" -h localhost -lqt 2>/dev/null | cut -d'|' -f1 | grep -qw "$name"; then
        echo "  ✅ database '$name' exists"
    else
        psql -U "$DB_USER" -h localhost -c "CREATE DATABASE $name;" >/dev/null
        echo "  ✅ database '$name' created"
    fi
}

create_db mobile_tracker
create_db airflow

echo
echo "✅ Setup complete."
