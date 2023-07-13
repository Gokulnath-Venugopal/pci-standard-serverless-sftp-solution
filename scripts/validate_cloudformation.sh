#!/bin/bash
set -euo pipefail
shopt -s globstar nullglob

rc=0
for filename in ./**/template.yml ; do
  echo "==> Validating ${filename}"
  aws cloudformation validate-template --template-body "file://$(pwd)/${filename}" >/dev/null || exit $?
done

exit $rc