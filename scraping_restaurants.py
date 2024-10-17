import json
import requests
import boto3
from datetime import datetime
import os
from requests_aws4auth import AWS4Auth

# AWS credentials and region for signing
region = 'us-east-1'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('yelp-restaurants')

# Yelp API key from environment variables
YELP_API_KEY = os.getenv('YELP_API_KEY')

# Function to fetch restaurants from Yelp API
def fetch_restaurants(cuisine, location="Manhattan", limit=50):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    params = {
        "categories": cuisine.lower(),  # Use the cuisine directly
        "location": location,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Function to store data in DynamoDB
def store_in_dynamodb(restaurant, cuisine):
    table.put_item(
        Item={
            'BusinessID': restaurant['id'],
            'Name': restaurant['name'],
            'Address': restaurant['location']['address1'],
            'Coordinates': {
                'Latitude': str(restaurant['coordinates']['latitude']),
                'Longitude': str(restaurant['coordinates']['longitude'])
            },
            'NumberOfReviews': restaurant['review_count'],
            'Rating': str(restaurant['rating']),
            'ZipCode': restaurant['location']['zip_code'],
            'Cuisine': cuisine,
            'InsertedAtTimestamp': datetime.now().isoformat()
        }
    )

def store_in_elasticsearch(restaurant, cuisine):
    es_url = "https://search-restaurant-search-4dnkbzyw36vyq3ooake4tavkoy.us-east-1.es.amazonaws.com/restaurants/_doc/" + restaurant['id']
    payload = {
        "RestaurantID": restaurant['id'],
        "Cuisine": cuisine
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Add your master username and password here
    master_username = "siddharth"  # Replace with your actual username
    master_password = "Sansid@22"  # Replace with your actual password

    # Use requests with HTTP Basic Authentication
    response = requests.put(es_url, json=payload, headers=headers, auth=(master_username, master_password))
    
    if response.status_code == 201:
        print(f"Stored {restaurant['name']} in Elasticsearch")
    else:
        print(f"Error storing {restaurant['name']} in Elasticsearch: {response.text}")


# Main Lambda handler function
def lambda_handler(event, context):
    # List of cuisines to fetch
    cuisines = ["Chinese", "Italian", "Mexican"]
    
    # Fetch and store restaurants for each cuisine
    for cuisine in cuisines:
        print(f"Fetching {cuisine} restaurants...")
        data = fetch_restaurants(cuisine)
        
        # Check if response contains businesses
        if "businesses" in data:
            for restaurant in data['businesses']:
                try:
                    store_in_dynamodb(restaurant, cuisine)
                    store_in_elasticsearch(restaurant, cuisine)
                except Exception as e:
                    print(f"Error storing {restaurant['name']}: {str(e)}")
        else:
            print(f"No data found for {cuisine} restaurants")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Data scraped and stored in DynamoDB')
    }
