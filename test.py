import json
import mock
import os
import pytest

import responses
import requests

from moto import mock_dynamodb2


# Override smart_open library as it doesn't have any mock implementation
with mock.patch.dict(os.environ, {"EXAMPLE_S3_BUCKET": "test-bucket"} ),\
     mock.patch.dict(os.environ, {"EXAMPLE_DYNAMODB_TABLE": "test1"} ),\
     mock.patch.dict('sys.modules', smart_open=mock.MagicMock()):
    from main import *


# Apply responses decorator
@responses.activate
def test_download_file():
    test_cases = [
        {
            "name": "works properly",
            "url": "https://github.com/alexnoob/BasketBall-GM-Rosters/releases/download/2020.2.0/2019-20.NBA.Roster.json",
            "status_code": 200,
            "output": {'tid': 5, 'name': 'Kevin Love', 'pos': 'FC', 'jerseyNumber': 0},
        },
        {
            "name": "error!",
            "url": "http://bad.url.com",
            "status_code": 404,
            "output": {'error': 'not found'}
        }
    ]

    for test in test_cases:
        responses.add(responses.GET, test['url'],
            json=test['output'], status=test['status_code'])        

        if test['name'] == 'error!':
            with pytest.raises(Exception):
                result = download_file(test['url'])
        else:
            result = download_file(test['url'])
            assert result == test['output']


@mock_dynamodb2
def test_dynamodb_put_item():
    table_name = "TestTable"
    conn = boto3.client(
        "dynamodb",
        region_name="us-east-1",
        aws_access_key_id="ak",
        aws_secret_access_key="sk",
    )

    conn.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": "PlayerName", "KeyType": "HASH"}, {"AttributeName": "JerseyNumber", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "PlayerName", "AttributeType": "S"}, {"AttributeName": "JerseyNumber", "AttributeType": "N"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )

    dynamodb_put_item(table_name, {'PlayerName': "Dubi Gal", 'JerseyNumber': 0, 'Position': "Center"})
    with pytest.raises(ClientError):
        dynamodb_put_item("SanAntonioSpurs-non-existing-table", {"PlayerName": "Bruce Bowen", "Position": "Shooting Guard", "JerseyNumber": 12})

    with pytest.raises(ParamValidationError):
        dynamodb_put_item(table_name, "intended type mismatch")


def test_upload_file():
    obj = json.dumps('{"something": "something"}')
    upload_file(obj)
