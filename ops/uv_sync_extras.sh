#!/usr/bin/env bash
#
# Synchronise Hotpass dependencies using uv extras selected via HOTPASS_UV_EXTRAS.
#
# Usage:
#   HOTPASS_UV_EXTRAS="dev orchestration" bash ops/uv_sync_extras.sh
#   # defaults to "dev orchestration" when HOTPASS_UV_EXTRAS is unset

set -euo pipefail

extras=${HOTPASS_UV_EXTRAS:-"dev orchestration"}

if [[ -z ${extras// /} ]]; then
	echo "HOTPASS_UV_EXTRAS is empty; refusing to run without at least one extra." >&2
	exit 1
fi

args=()
for extra in ${extras}; do
	args+=("--extra" "${extra}")
done

echo "Synchronising uv environment with extras: ${extras}"
uv sync --frozen "${args[@]}"

printf "Tip: use 'make sync EXTRAS=\"%s\"' for subsequent runs.\n" "$extras"
