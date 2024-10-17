import json
import boto3
import requests
from datetime import datetime
import time
from requests.auth import HTTPBasicAuth

# Initialize AWS services
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

# Elasticsearch endpoint
es_url = "https://search-restaurant-search-4dnkbzyw36vyq3ooake4tavkoy.us-east-1.es.amazonaws.com"

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('userSearchHistory')

# Function to poll messages from SQS
def get_message_from_queue(queue_url):
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
    messages = response.get('Messages', [])
    return messages[0] if messages else None

# Function to query Elasticsearch
def query_elasticsearch(cuisine):
    # Generate a random seed based on the current time to ensure randomness
    random_seed = int(time.time())

    # Elasticsearch query with random_score to randomize results
    query = {
        "query": {
            "function_score": {
                "query": {
                    "match": {
                        "Cuisine": cuisine
                    }
                },
                "random_score": {
                    "seed": random_seed
                }
            }
        }
    }
    
    # Use HTTP Basic Authentication
    master_username = "siddharth"
    master_password = "test@password77"

    # Perform the request to Elasticsearch
    response = requests.post(
        es_url + "/restaurants/_search",
        json=query,
        headers={"Content-Type": "application/json"},
        auth=HTTPBasicAuth(master_username, master_password)
    )
    
    # Return the response as a JSON object
    return response.json()

# Function to get restaurant details from DynamoDB
def get_restaurant_details(restaurant_id):
    table = dynamodb.Table('yelp-restaurants')
    response = table.get_item(Key={'BusinessID': restaurant_id})
    return response.get('Item')

# Function to send restaurant suggestions via SES
def send_email(recipient, subject, body):
    print('sending email to ', recipient)
    print('subject: ',subject)
    print('body: ',body)
    ses.send_email(
        Source="nyuevents24@gmail.com",
        Destination={'ToAddresses': [recipient]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body}}
        }
    )
    
    # numPeople = body['numPeople']
    # location = body['Location']
    # time = body['DiningTime']
    
    
# Function to store data in DynamoDB
def store_in_dynamodb(email, cuisine, location, time, numPeople):
    table = dynamodb.Table('userSearchHistory')
    table.put_item(
        Item={
            'Email': email,
            'Cuisine': cuisine,
            'Location': location,
            'DiningTime': time,
            'numPeople': numPeople,
            'InsertedAtTimestamp': datetime.now().isoformat()
        }
    )    
# def store_in_dynamodb(email, email_body):
#     table.put_item(
#         Item={
#             'Email': email,
#             'email_body': email_body
#         }
#     )

# Lambda handler function
def lambda_handler(event, context):
    # Get message from SQS
    message = get_message_from_queue("https://sqs.us-east-1.amazonaws.com/588738575076/Q1")
    if not message:
        return {"statusCode": 200, "body": "No messages in queue"}

    # Extract user preferences from SQS message
    body = json.loads(message['Body'])
    cuisine = body['Cuisine']
    email = body['Email']
    numPeople = body['numPeople']
    location = body['Location']
    time = body['DiningTime']

    # Query Elasticsearch for matching restaurants
    es_response = query_elasticsearch(cuisine)
    
    # Check if hits contain any results
    if es_response['hits']['total']['value'] > 0:
        hits = es_response['hits']['hits'][:3]  # Get up to 3 restaurants
        restaurant_details_list = []
        
        # Fetch additional restaurant details from DynamoDB for each hit
        for hit in hits:
            restaurant_id = hit['_source']['RestaurantID']
            restaurant_details = get_restaurant_details(restaurant_id)
            restaurant_details_list.append(restaurant_details)
        
        # Prepare email body with 3 restaurant suggestions
        email_body = "Hello! Here are my " + cuisine + " restaurant suggestions for " + str(numPeople) + " people, for " + str(time) + ":\n"
        for details in restaurant_details_list:
            email_body += f"{details['Name']}, located at {details['Address']}\n"
        
        # store search history in dynamoDB ('userSearchHistory')
        store_in_dynamodb(email, cuisine, location, time, numPeople)
        
        print('cuisine: ',cuisine,' ', email_body)
        
        # Send the email
        send_email(email, f"{cuisine} Restaurant Suggestions", email_body)
    else:
        print(f"No restaurants found for cuisine: {cuisine}")
        return {"statusCode": 404, "body": json.dumps("No restaurants found")}

    # Confirm processing and delete message from SQS
    sqs.delete_message(QueueUrl="https://sqs.us-east-1.amazonaws.com/588738575076/Q1", ReceiptHandle=message['ReceiptHandle'])

    return {"statusCode": 200, "body": "Suggestions sent via email"}
