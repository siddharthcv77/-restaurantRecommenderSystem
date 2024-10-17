import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/588738575076/Q1'

def lambda_handler(event, context):
    logger.info("Lambda function invoked.")
    logger.info("Received event: " + json.dumps(event, indent=2))
    
    try:
        intent_name = event['sessionState']['intent']['name']
        
        # Handle different intents
        if intent_name == "GreetingIntent" or intent_name == "continueIntent":
            response_message = "Hi there, how can I help?"
        elif intent_name == "ThankYouIntent":
            response_message = "You're welcome!"
        elif intent_name == "DiningSuggestionsIntent":
            # Extract the slot values (user's input)
            slots = event['sessionState']['intent']['slots']
            location = slots['Location']['value']['interpretedValue']
            cuisine = slots['Cuisine']['value']['interpretedValue']
            dining_time = slots['DiningTime']['value']['interpretedValue']
            num_people = slots['numPeople']['value']['interpretedValue']
            email = slots['Email']['value']['interpretedValue']
            
            message = {
                'Location': location,
                'Cuisine': cuisine,
                'DiningTime': dining_time,
                'numPeople': num_people,
                'Email': email
            }
            
            # Send the message to SQS
            send_to_sqs(message)
            
            response_message = f"Thank you! You’ve requested {cuisine} cuisine in {location} for {num_people} people at {dining_time}. We will send suggestions to {email} shortly."
        else:
            response_message = "I'm still under development. Please come back later."
        
        response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent_name,
                    "state": "Fulfilled"
                }
            },
            "messages": [{
                "contentType": "PlainText",
                "content": response_message
            }]
        }
        
    except KeyError as e:
        logger.error(f"Error processing event: {str(e)}")
        response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": "FallbackIntent",
                    "state": "Failed"
                }
            },
            "messages": [{
                "contentType": "PlainText",
                "content": f"Sorry, I encountered an error: {str(e)}"
            }]
        }
    
    return response

def send_to_sqs(message):
    """Function to send the user's request to SQS"""
    try:
        logger.info(f"Sending message to SQS: {message}")
        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        logger.info(f"Message sent to SQS: {response['MessageId']}")
    except Exception as e:
        logger.error(f"Error sending message to SQS: {str(e)}")
