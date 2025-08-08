#!/bin/bash

set -euxo pipefail

cwd="$(pwd)"

cd .venv/lib/python3.12/site-packages/
zip -u -r9 "${cwd}/function.zip" * -x '__pycache__/*' || true

cd "${cwd}/src"
zip -u "${cwd}/function.zip" -r . -x '__pycache__/*' || true

cd "${cwd}"
aws s3 cp function.zip s3://wcl-analyzer-lambda-code/function.zip
# create lambda function if it doesn't exist
if [[ $(aws lambda list-functions --query "Functions[?FunctionName=='$WCL_FUNCTION_NAME'].FunctionName" --output text) == "" ]]; then
  echo "Lambda function does not exist. Creating function..."
  aws lambda create-function \
    --function-name "$WCL_FUNCTION_NAME" \
    --runtime python3.12 \
    --handler handler.handler \
    --code "S3Bucket=wcl-analyzer-lambda-code,S3Key=function.zip" \
    --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/service-role/wcl-analyzer-lambda-role-rh6pdnzt \
    --timeout 30 \
    --environment Variables="{WCL_CLIENT_ID=$WCL_CLIENT_ID,WCL_CLIENT_SECRET=$WCL_CLIENT_SECRET}" \
    --memory-size 2048 \
    --ephemeral-storage Size=2048
else
  echo "Lambda function already exists. Updating code..."
  aws lambda update-function-code \
    --function-name "$WCL_FUNCTION_NAME" \
    --s3-bucket "wcl-analyzer-lambda-code" \
    --s3-key "function.zip"

  echo "Waiting for function to update..."
  aws lambda wait function-updated \
    --function-name "$WCL_FUNCTION_NAME"
fi

# aws lambda update-function-code --function-name wcl-analyzer-lambda --s3-bucket wcl-analyzer-lambda-code --s3-key function.zip --publish
