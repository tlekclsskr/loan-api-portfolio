import os
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'testing')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'testing')
os.environ['TABLE_NAME'] = 'loans-iac-test'
os.environ['BUCKET_NAME'] = 'test-bucket'

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

@mock_aws
def test_patch_status():
    conn = boto3.resource('dynamodb', region_name= 'us-east-1')
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
        'body': json.dumps({'customer': 'Test User', 'amount': 120000, 'months': 12})
    }
    post_response = lambda_function.lambda_handler(post_event, None)
    loan_id = json.loads(post_response['body'])['id']

    patch_event = {
        'requestContext': {'http': {'method': 'PATCH'}},
        'pathParameters': {'id': loan_id},
        'body': json.dumps({'status': 'approved'})
    }
    patch_response = lambda_function.lambda_handler(patch_event, None)
    patch_body = json.loads(patch_response['body'])
    assert patch_response['statusCode'] == 200
    assert patch_body['status'] == 'approved'


@mock_aws
def test_delete_loan():
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
        'body': json.dumps({'customer': 'Test User', 'amount': 120000, 'months': 12})
    }
    post_response = lambda_function.lambda_handler(post_event, None)
    loan_id = json.loads(post_response['body'])['id']

    delete_event = {
        'requestContext': {'http': {'method': 'DELETE'}},
        'pathParameters': {'id': loan_id}
    }
    delete_response = lambda_function.lambda_handler(delete_event, None)
    assert delete_response['statusCode'] == 200

    get_event = {
        'requestContext': {'http': {'method': 'GET'}},
        'pathParameters': {'id': loan_id}
    }
    get_response = lambda_function.lambda_handler(get_event, None)
    assert get_response['statusCode'] == 404


@mock_aws
def test_get_document_upload_url():
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
        'body': json.dumps({'customer': 'Test User', 'amount': 120000, 'months': 12})
    }
    post_response = lambda_function.lambda_handler(post_event, None)
    loan_id = json.loads(post_response['body'])['id']

    doc_event = {
        'requestContext': {'http': {'method': 'POST'}},
        'pathParameters': {'id': loan_id},
        'rawPath': f'/loans/{loan_id}/document',
        'body': json.dumps({'filename': 'test.pdf'})
    }
    doc_response = lambda_function.lambda_handler(doc_event, None)
    doc_body = json.loads(doc_response['body'])
    assert doc_response['statusCode'] == 200
    assert 'upload_url' in doc_body