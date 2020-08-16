import mock
import os

import responses
import requests


# Override smart_open library as it doesn't have any mock implementation
with mock.patch.dict(os.environ, {"EXAMPLE_S3_BUCKET": "test-bucket"} ),\
     mock.patch.dict('sys.modules', smart_open=mock.MagicMock()):
    from main import *


# Apply responses decorator
@responses.activate
def test_update_file():
    url = 'http://data.nba.net/10s/prod/v1/allstar/2016/AS_roster.json'
    responses.add(responses.GET, url,
            json={'sportsContent': {'roster': [{'coaches': {'coach': [{'fullName': 'Brad Stevens'}]}}]}}, status=200)

    result = update_file()

    assert result.json()['sportsContent']['roster'][0]['coaches']['coach'][0]['fullName'] == "Brad Stevens"
    assert result.status_code == 200
    assert result.url == url
