import os
import boto3
import json
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path_params = event.get('pathParameters') or {}
    loan_id = path_params.get('id')

    if method == 'POST':
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
                'body': json.dumps({'statusCode': 404, 'body': json.dumps({'error': 'Loan not found'})}, ensure_ascii=False)
            }
        return {
            'statusCode': 200,
            'body': json.dumps(item, ensure_ascii=False, default=str)
        }

    elif method == 'PATCH' and loan_id:
        body = json.loads(event.get('body') or {})
        table.update_item(
            Key={'id': loan_id},
            UpdateExpression='SET #s = #val',
            ExpressionAtrributeNames={'#s': 'status'},
            ExpressionAttributeValues={'#val': body.get('status')}
        )
        return {'statusCode': 200, 'body': json.dumps({'id': loan_id, 'status': body.get('status')}, ensure_ascii=False)}

    else:
        response = table.scan()
        return {'statusCode': 200, 'body': json.dumps(response.get('Item', []), ensure_ascii=False, default=str)}
