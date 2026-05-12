#!/usr/bin/env bash

set -euo pipefail

#LOG_FILE="${1:-/var/log/nginx/access.log}"
### Comment the above line and uncomment the below for testing if no access.log pre-exist ###
LOG_FILE="${1:-./access.log}" 
TOP_COUNT=10

if [[ ! -f "${LOG_FILE}" ]]; then
  echo "Error: log file not found: ${LOG_FILE}" >&2
  exit 1
fi

if [[ ! -r "${LOG_FILE}" ]]; then
  echo "Error: log file is not readable: ${LOG_FILE}" >&2
  exit 1
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

# Keep only lines that look like nginx access log entries:
# - first token IPv4/IPv6-ish address
# - request and status fields present
awk '
  NF >= 9 && $1 ~ /^[0-9a-fA-F:.]+$/ && $9 ~ /^[0-9]{3}$/ { print }
' "${LOG_FILE}" > "${TMP_FILE}"

TOTAL_REQUESTS="$(wc -l < "${TMP_FILE}" | tr -d " ")"

if [[ "${TOTAL_REQUESTS}" -eq 0 ]]; then
  echo "No valid log entries found in ${LOG_FILE}"
  exit 0
fi

UNIQUE_IPS="$(awk '{print $1}' "${TMP_FILE}" | sort | uniq | wc -l | tr -d " ")"

ERROR_4XX="$(awk '$9 ~ /^4[0-9][0-9]$/ {count++} END {print count+0}' "${TMP_FILE}")"
ERROR_5XX="$(awk '$9 ~ /^5[0-9][0-9]$/ {count++} END {print count+0}' "${TMP_FILE}")"

PCT_4XX="$(awk -v e="${ERROR_4XX}" -v t="${TOTAL_REQUESTS}" 'BEGIN {printf "%.2f", (e/t)*100}')"
PCT_5XX="$(awk -v e="${ERROR_5XX}" -v t="${TOTAL_REQUESTS}" 'BEGIN {printf "%.2f", (e/t)*100}')"

echo "=== Nginx Log Analysis Report ==="
echo "Log File: ${LOG_FILE}"
echo "Total Requests: ${TOTAL_REQUESTS}"
echo "Unique IPs: ${UNIQUE_IPS}"
echo "4xx Errors: ${ERROR_4XX} (${PCT_4XX}%)"
echo "5xx Errors: ${ERROR_5XX} (${PCT_5XX}%)"
echo

echo "Top ${TOP_COUNT} IPs:"
awk '{print $1}' "${TMP_FILE}" | sort | uniq -c | sort -nr | head -n "${TOP_COUNT}" | \
awk '{printf "%2d. %-40s %8d requests\n", NR, $2, $1}'
echo

# This needs testing
# has been tested okay to push
echo "Top ${TOP_COUNT} Endpoints:"
# Extract endpoint path from the request field:
# Example request: "GET /api/v1/users HTTP/1.1"
awk -F\" '
  NF >= 2 {
    split($2, req, " ")
    if (length(req[2]) > 0) print req[2]
  }
' "${TMP_FILE}" | sort | uniq -c | sort -nr | head -n "${TOP_COUNT}" | \
awk '{printf "%2d. %-50s %8d requests\n", NR, $2, $1}'

