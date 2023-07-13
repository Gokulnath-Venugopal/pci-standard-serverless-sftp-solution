#!/usr/bin/env sh
# shellcheck disable=SC2044
# shellcheck disable=SC2039
# shellcheck disable=SC3040
set -euo pipefail

rc=0
for filename in $(find . -name '*.sh') ; do
  echo "==> Validating ${filename}"
  shellcheck "${filename}" || exit $?
done

exit $rc