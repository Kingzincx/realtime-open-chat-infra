#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${ROOT_DIR}/certs"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

mkdir -p "${CERT_DIR}"

CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"

create_leaf_cert() {
  local name="$1"
  local key_file="${CERT_DIR}/${name}.key"
  local csr_file="${TMP_DIR}/${name}.csr"
  local crt_file="${CERT_DIR}/${name}.crt"
  local config_file="${TMP_DIR}/${name}.cnf"

  cat > "${config_file}" <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = ${name}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = nginx
DNS.3 = api
DNS.4 = event-consumer
DNS.5 = chat-history-consumer
DNS.6 = moderation-consumer
IP.1 = 127.0.0.1
EOF

  openssl genrsa -out "${key_file}" 2048
  openssl req -new -key "${key_file}" -out "${csr_file}" -config "${config_file}"
  openssl x509 -req \
    -in "${csr_file}" \
    -CA "${CA_CERT}" \
    -CAkey "${CA_KEY}" \
    -CAcreateserial \
    -out "${crt_file}" \
    -days 825 \
    -sha256 \
    -extfile "${config_file}" \
    -extensions v3_req
}

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required to generate local certificates." >&2
  exit 1
fi

if [[ ! -f "${CA_KEY}" || ! -f "${CA_CERT}" ]]; then
  openssl genrsa -out "${CA_KEY}" 4096
  openssl req -x509 -new -nodes \
    -key "${CA_KEY}" \
    -sha256 \
    -days 3650 \
    -out "${CA_CERT}" \
    -subj "/CN=Realtime Open Chat Local CA"
fi

create_leaf_cert "nginx"
create_leaf_cert "api"
create_leaf_cert "event-consumer"
create_leaf_cert "chat-history-consumer"
create_leaf_cert "moderation-consumer"

chmod 644 "${CERT_DIR}"/*.crt
chmod 600 "${CERT_DIR}"/*.key

echo "Generated local CA, NGINX, FastAPI, and consumer certificates in ${CERT_DIR}"
