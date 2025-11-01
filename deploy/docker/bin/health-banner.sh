#!/bin/sh
cat <<MSG
==============================================================
Hotpass Compose stack starting…
If Prefect or Marquez health checks stay red, reconnect to the
VPN/bastion before retrying. The web UI expects PREFECT_API_URL=
${PREFECT_API_URL:-http://prefect:4200/api} and OPENLINEAGE_URL=
${OPENLINEAGE_URL:-http://marquez:5000/api/v1}.
==============================================================
MSG
