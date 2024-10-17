import json
import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('lexv2-runtime')

BOT_ID = 'LIUB5YGQMA'
BOT_ALIAS_ID = 'TSTALIASID'
LOCALE_ID = 'en_US'
SESSION_ID = 'test-session'

dynamodb = boto3.resource('dynamodb')

sqs = boto3.client('sqs')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/588738575076/Q1'

# Function to get user history from DynamoDB
def get_userSearchHistory(user_input):
    table = dynamodb.Table('userSearchHistory')
    response = table.get_item(Key={'Email': user_input})
    return response.get('Item', None)
    
def send_to_sqs(message):
    """Function to send the user's request to SQS"""
    try:
        logger.info(f"Sending message to SQS: {message}")
        
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        logger.info(f"Message sent to SQS: {response['MessageId']}")
    except Exception as e:
        logger.error(f"Error sending message to SQS: {str(e)}")

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    try:
        
        if 'body' in event and event['body']:
        
            body = json.loads(event['body'])
            if 'messages' in body and len(body['messages']) > 0:
                user_input = body['messages'][0]['unstructured']['text']
            else:
                raise KeyError("Expected 'messages' field with 'unstructured' text in the body")
        elif 'userMessage' in event:
            # If 'userMessage' exists directly
            user_input = event['userMessage']
        else:
            raise KeyError('Expected message in the body or userMessage in the event')

        userSearchHistory = get_userSearchHistory(user_input)

        # Check if userSearchHistory exists and send the message to SQS
        if userSearchHistory:
            
            message = {
                'Location': userSearchHistory['Location'],
                'Cuisine': userSearchHistory['Cuisine'],
                'DiningTime': userSearchHistory['DiningTime'],
                'numPeople': userSearchHistory['numPeople'],
                'Email': userSearchHistory['Email']
            }
            
            # Send the message to SQS
            send_to_sqs(message)
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "https://d9nelxbkq1009.cloudfront.net",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                },
                "body": json.dumps({
                    "message": "Thank You! The restaurant suggestions will be sent to your email shortly."
                }),
            }

        # If userSearchHistory doesn't exist, proceed to call Lex
        lex_response = client.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=SESSION_ID,
            text=user_input
        )

        lex_message = lex_response['messages'][0]['content']

        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "https://d9nelxbkq1009.cloudfront.net",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            },
            "body": json.dumps({
                "message": lex_message
            }),
        }

    except KeyError as e:
        logger.error(f"Missing field in request: {str(e)}")
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "https://d9nelxbkq1009.cloudfront.net",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            },
            "body": json.dumps({
                "message": f"Missing required field: {str(e)}"
            }),
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        response = {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "https://d9nelxbkq1009.cloudfront.net",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            },
            "body": json.dumps({
                "message": f"An error occurred: {str(e)}"
            }),
        }
    
    return response
