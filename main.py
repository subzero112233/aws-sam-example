import json
import logging
import os

import smart_open 
import requests

example_bucket = os.environ['EXAMPLE_S3_BUCKET']


def lambda_handler(event, context): # pragma: no cover
    update_file()

    return {
            'statusCode': 200,
            'body': json.dumps('Success')
    }
    


def update_file():
    response = requests.get('http://data.nba.net/10s/prod/v1/allstar/2016/AS_roster.json')
    if response.status_code != 200:
        raise Exception("Failed to download file, make sure it exists")

    with smart_open.open('s3://{}/{}'.format(example_bucket, 'roster.json'), 'wb') as fout:
        fout.write(response.content)

    logging.info('Finished updating file')

    return response

    

