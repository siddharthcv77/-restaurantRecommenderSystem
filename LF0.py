import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Lex client
client = boto3.client('lexv2-runtime')

# Lex bot configuration (adjust the botID, aliasID, and localeID as per your Lex bot)
BOT_ID = 'LIUB5YGQMA'
BOT_ALIAS_ID = 'TSTALIASID'
LOCALE_ID = 'en_US'
SESSION_ID = 'test-session'

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('userSearchHistory')

# Initialize SQS clients
sqs = boto3.client('sqs')
# Your SQS Queue URL
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/588738575076/Q1'

# Function to get user history from DynamoDB
def get_userSearchHistory(user_input):
    table = dynamodb.Table('userSearchHistory')
    response = table.get_item(Key={'Email': user_input})
    return response.get('Item', None)  # Returns None if 'Item' doesn't exist
    
def send_to_sqs(message):
    """Function to send the user's request to SQS"""
    try:
        logger.info(f"Sending message to SQS: {message}")  # Log the message being sent
        # Send message to SQS queue
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
        # Extract user input from the event body or userMessage
        if 'body' in event and event['body']:
            # If 'body' exists, extract the message from 'messages'
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

        # Extract email from the user input, assuming it's part of the input
        # You can modify this depending on the structure of the input
        # email = extract_email(user_input)  # Function to extract the email from the input text
        
        # if not email:
        #     raise ValueError("Email not found in user input")

        # Fetch user history using the extracted email
        userSearchHistory = get_userSearchHistory(user_input)

        # Check if userSearchHistory exists and send the message to SQS
        if userSearchHistory:
            # Create the message to send to SQS
            message = {
                'Location': userSearchHistory['Location'],
                'Cuisine': userSearchHistory['Cuisine'],
                'DiningTime': userSearchHistory['DiningTime'],
                'numPeople': userSearchHistory['numPeople'],
                'Email': userSearchHistory['Email']
            }
            
            # Send the message to SQS
            send_to_sqs(message)
            
            # Return response indicating no interaction with Lex
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

        # Extract Lex's response
        lex_message = lex_response['messages'][0]['content']

        # Prepare the response with the dynamic message from Lex
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
