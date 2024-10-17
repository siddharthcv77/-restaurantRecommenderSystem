# Restaurant Recommender System
A serverless restaurant recommender system that provides personalized dining suggestions based on user preferences. Built using AWS Lambda, Amazon Lex, API Gateway, DynamoDB, and Elasticsearch. Integrates the Yelp API for restaurant data collection and uses AWS SES for automated email notifications.

Features
Chatbot: Handles user conversations through Amazon Lex, collecting location, cuisine, and dining preferences.
Restaurant Data: Fetches over 5,000 restaurant entries from Yelp API and stores them in DynamoDB and Elasticsearch.
Personalized Suggestions: Delivers restaurant recommendations via email based on user preferences.
Serverless Architecture: Uses AWS Lambda, API Gateway, and SQS for a scalable, microservice-based backend.
Automated Notifications: Sends personalized dining suggestions via email using AWS SES.

Technologies Used
Frontend: HTML/CSS (Hosted on AWS S3)
Backend: AWS Lambda, API Gateway, Amazon Lex, SQS
Database: DynamoDB, Elasticsearch
External APIs: Yelp API, AWS SES
Programming Language: Python (Lambda Functions), JavaScript (API integration)

Architecture
The application follows a microservices architecture using serverless technologies:
Amazon Lex Chatbot: Interacts with users to gather preferences such as cuisine type, location, dining time, and number of people.
Lambda Functions: Processes requests, integrates with Lex, and handles data from Yelp API.
Yelp API: Fetches restaurant data, which is stored in DynamoDB and Elasticsearch.
SQS & SES: Queue system for processing recommendations and sending emails.
