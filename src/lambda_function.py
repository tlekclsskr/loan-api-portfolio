import os
import boto3
import json
import uuid
import urllib.request
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

s3 = boto3.client(
    's3',
    region_name='ap-southeast-7',
    endpoint_url='https://s3.ap-southeast-7.amazonaws.com'
)
BUCKET_NAME = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path_params = event.get('pathParameters') or {}
    loan_id = path_params.get('id')
    path = event.get('rawPath', '')

    if method == 'GET' and path.endswith('/exchange-rate'):
        try:
            with urllib.request.urlopen('https://open.er-api.com/v6/latest/USD', timeout=5) as response:
                data = json.loads(response.read().decode())
            thb_rate = data.get('rates', {}).get('THB')
            return {
                'statusCode': 200,
                'body': json.dumps({'usd_to_thb': thb_rate, 'source': 'open.er-api.com'}, ensure_ascii=False)
            }
        except Exception as e:
            return {
                'statusCode': 502,
                'body': json.dumps({'error': f'Failure to fetch third_party API: {str(e)}'}, ensure_ascii=False)
            }

    elif method == 'POST' and loan_id and path.endswith('/document'):
        body = json.loads(event.get('body') or '{}')
        filename = body.get('filename', 'document.pdf')
        s3_key = f"loans/{loan_id}/{filename}"

        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300
        )

        table.update_item(
            Key={'id': loan_id},
            UpdateExpression='SET document_key = :val',
            ExpressionAttributeValues={':val': s3_key}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'upload_url': upload_url, 'expires_in_seconds': 300}, ensure_ascii=False)
        }

    elif method == 'POST':
        body = json.loads(event.get('body') or '{}')
        amount = body.get('amount')
        months = body.get('months')
        monthly_payment = Decimal(str(amount)) / Decimal(str(months))

        item = {
            'id': str(uuid.uuid4()),
            'customer': body.get('customer'),
            'amount': amount,
            'months': months,
            'monthly_payment': monthly_payment,
            'status': 'pending'
        }
        table.put_item(Item=item)
        return {
            'statusCode': 200, 
            'body': json.dumps(item, ensure_ascii=False, default=str)
        }

    elif method == 'GET' and loan_id:
        response = table.get_item(Key={'id': loan_id})
        item = response.get('Item')
        if item is None:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Loan not found'}, ensure_ascii=False)
            }
        return {
            'statusCode': 200,
            'body': json.dumps(item, ensure_ascii=False, default=str)
        }

    elif method == 'PATCH' and loan_id:
        body = json.loads(event.get('body') or '{}')
        table.update_item(
            Key={'id': loan_id},
            UpdateExpression='SET #s = :val',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':val': body.get('status')}
        )
        return {'statusCode': 200, 'body': json.dumps({'id': loan_id, 'status': body.get('status')}, ensure_ascii=False)}

    elif method == 'DELETE' and loan_id:
        table.delete_item(Key={'id': loan_id})
        return {'statusCode': 200, 'body': json.dumps({'id': loan_id, 'deleted': True}, ensure_ascii=False)}

    else:
        response = table.scan()
        return {'statusCode': 200, 'body': json.dumps(response.get('Items', []), ensure_ascii=False, default=str)}
