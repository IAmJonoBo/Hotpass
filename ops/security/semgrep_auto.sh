#!/usr/bin/env bash
#
# Run `semgrep --config=auto` with optional corporate CA bundle support.
#
# Usage:
#   bash ops/security/semgrep_auto.sh [extra semgrep args...]
#   HOTPASS_CA_BUNDLE_B64="$(base64 <ca.pem)" bash ops/security/semgrep_auto.sh

set -euo pipefail

tmp_ca=""

cleanup() {
	if [[ -n $tmp_ca && -f $tmp_ca ]]; then
		rm -f "$tmp_ca"
	fi
}
trap cleanup EXIT

if [[ -n ${HOTPASS_CA_BUNDLE_B64-} ]]; then
	tmp_ca="$(mktemp)"
	printf '%s' "$HOTPASS_CA_BUNDLE_B64" | base64 --decode >"$tmp_ca"
	export REQUESTS_CA_BUNDLE="$tmp_ca"
	export SSL_CERT_FILE="$tmp_ca"
	echo "Loaded custom CA bundle into $tmp_ca for semgrep auto run."
fi

exec uv run semgrep --config=auto --metrics=off "$@"
