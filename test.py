import mock
import os
import pytest

import responses
import requests


# Override smart_open library as it doesn't have any mock implementation
with mock.patch.dict(os.environ, {"EXAMPLE_S3_BUCKET": "test-bucket"} ),\
     mock.patch.dict('sys.modules', smart_open=mock.MagicMock()):
    from main import *


# Apply responses decorator
@responses.activate
def test_update_file():
    test_cases = [
        {
            "name": "works properly",
            "url": "http://data.nba.net/10s/prod/v1/allstar/2016/AS_roster.json",
            "status_code": 200,
            "output": {'sportsContent': {'roster': [{'coaches': {'coach': [{'fullName': 'Brad Stevens'}]}}]}}
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
                result = update_file(test['url'])
        else:
            result = update_file(test['url'])
            assert result.json() == test['output']
            assert result.status_code == test['status_code']
            assert result.url == test['url']
