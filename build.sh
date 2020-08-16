#!/bin/bash

set -e

function cleanup {
  echo "Cleaning up..."
  rm -rf .pytest_cache __pycache__ *.pyc
}

ENV=$1
FUNCTION_NAME=medium-example 
STACK_NAME=$FUNCTION_NAME-$ENV


case $ENV in
    dev)
        S3_ARTIFACT_BUCKET=medium-lambda-dev
        ;;
    staging)
        S3_ARTIFACT_BUCKET=medium-lambda-staging
        ;;
    prod)
        S3_ARTIFACT_BUCKET=medium-lambda-prod
        ;;
    *)
        echo "Environment should be dev/staging/prod only"
        exit 1
esac


# Syntax check
python3.6 -m py_compile $SCRIPT_NAME

# Unit tests
pytest --cov-report term-missing --cov=. test.py -rxXs

# Prepare
mkdir -p dist/
rsync -av --exclude-from 'excludes.txt' "$PWD/" dist/

# Clean garbage
trap cleanup EXIT

# Build
sam build --build-dir build --use-container  

# Integration tests
sam local invoke --template build/template.yaml --env-vars ${ENV}.json --event ${FUNCTION_NAME}-event.json > output
if [[ -z "$integration_tests" ]]
then
    cat output
    status=$(cat output | jq .statusCode)
    if [[ -z "$status" ]]
    then
        echo "integration test failed: error occured"
        exit 1
    elif [[ "$status" != 200 ]]
    then
        echo "integration test failed with the following error: $status"
    exit 1
    fi
fi

# Package
sam package --metadata function=$FUNCTION_NAME --s3-prefix $FUNCTION_NAME  --template-file build/template.yaml --s3-bucket $S3_ARTIFACT_BUCKET --output-template-file build/packaged.yaml

# Deploy
sam deploy --template-file build/packaged.yaml --stack-name "$STACK_NAME" --capabilities CAPABILITY_IAM --parameter-overrides "ParameterKey=Environment,ParameterValue=${ENV}"

exit 0
