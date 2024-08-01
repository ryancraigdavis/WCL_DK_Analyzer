#!/bin/bash

set -euxo pipefail

cwd="$(pwd)"

yarn build
cd dist

aws s3 cp . s3://wcl-analyzer-frontend/ --recursive
aws cloudfront create-invalidation --distribution-id E2QQGL1YVUW0M3 --paths '/*'

cd -
rm -rf dist
