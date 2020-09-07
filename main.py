import boto3
import logging
import json
import os

import smart_open
import requests

from botocore.exceptions import ClientError, ParamValidationError

example_bucket = os.environ['EXAMPLE_S3_BUCKET']
example_table = os.environ['EXAMPLE_DYNAMODB_TABLE']

dynamodb2 = boto3.resource('dynamodb')


def lambda_handler(event, context):  # pragma: no cover
    data = download_file(
        'https://github.com/alexnoob/BasketBall-GM-Rosters/releases/download/2020.2.0/2019-20.NBA.Roster.json')

    # Assume we know that the Spurs are team id 26 and (it's permanent)
    # Let's prepare a list containing the Spurs roster
    roster = [player for player in data['players'] if player['tid'] == 26]

    for player in roster:
        if player.get('stats'):
            if player['stats'][-1].get('jerseyNumber'):
                jersey = int(player['stats'][-1]['jerseyNumber'])
        else:
            jersey = 0000000

        dynamodb_put_item(example_table,
                          {'PlayerName': player['name'], 'JerseyNumber': jersey, 'Position': player['pos']})

    upload_file(json.dumps(data).encode('utf-8'))

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }


def download_file(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to download file, make sure it exists")
    return json.loads(response.content)


# We do "test" this function, we're just mocking it and pretending it does the upload
def upload_file(obj):
    with smart_open.open('s3://{}/{}'.format(example_bucket, 'roster.json'), 'wb') as fout:
        fout.write(obj)


def dynamodb_put_item(table, item):
    try:
        table = dynamodb2.Table(table)
        table.put_item(Item=item)
    except (ClientError, ParamValidationError) as e:
        logging.error(e)
        raise
