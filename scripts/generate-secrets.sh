#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS_DIR="${ROOT_DIR}/secrets"

create_secret() {
  local file_name="$1"
  local file_path="${SECRETS_DIR}/${file_name}"

  if [[ -s "${file_path}" ]]; then
    echo "Keeping existing ${file_name}"
    return
  fi

  openssl rand -hex 32 > "${file_path}"
  chmod 600 "${file_path}" || true
  echo "Generated ${file_name}"
}

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate local secrets." >&2
  exit 1
fi

mkdir -p "${SECRETS_DIR}"

create_secret "postgres_password.txt"
create_secret "grafana_admin_password.txt"
create_secret "airflow_admin_password.txt"
create_secret "airflow_postgres_password.txt"

echo "Local secret files are ready in ${SECRETS_DIR}"
