import os
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'testing')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'testing')
os.environ['TABLE_NAME'] = 'loans-iac-test'

import json
import importlib
import boto3
from moto import mock_aws

@mock_aws
def test_create_and_get_loan():
    conn = boto3.resource('dynamodb', region_name='us-east-1')
    conn.create_table(
        TableName='loans-iac-test',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    import lambda_function
    importlib.reload(lambda_function)

    post_event = {
        'requestContext': {'http': {'method': 'POST'}},
        'body': json.dumps({'customer': 'Test User', 'amount': '120000', 'months': 12})
    }
    response = lambda_function.lambda_handler(post_event, None)
    assert response['statusCode'] == 200

    body = json.loads(response['body'])
    assert body['customer'] == 'Test User'