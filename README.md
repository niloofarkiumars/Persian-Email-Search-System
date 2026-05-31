# Persian Email Search System

## 🎯 Overview

A complete, production-ready Persian/Farsi full-text search system for email data using Elasticsearch and MongoDB.

## 📋 What You Need to Customize

### 1. Database Schema Mapping

**Most Important**: Your team MUST customize the field mappings in `src/models/email_model.py`:

```python
# In EmailMapper class, change these to match your database columns:

FIELD_MAPPINGS = {
    'message_id': 'YOUR_MESSAGE_ID_COLUMN',     # e.g., '_id' or 'msg_id'
    'subject': 'YOUR_SUBJECT_COLUMN',           # e.g., 'email_subject'
    'body': 'YOUR_BODY_COLUMN',                 # e.g., 'email_body' or 'content'
    'from_address': 'YOUR_FROM_COLUMN',         # e.g., 'sender' or 'from_email'
    'to_addresses': 'YOUR_TO_COLUMN',           # e.g., 'recipients' or 'to'
    'date': 'YOUR_DATE_COLUMN',                 # e.g., 'sent_date' or 'created_at'
    'has_attachment': 'YOUR_ATTACHMENT_COLUMN', # e.g., 'attachments' or 'has_attachments'
}

### 2. Edit .env file with your MongoDB credentials
MONGO_HOST=mongodb://your-mongodb-host:27017/
MONGO_DATABASE=your_database_name
MONGO_COLLECTION=your_collection_name

# Download from:
https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.13.4-windows-x86_64.zip


# Install Persian plugin:
C:\elasticsearch\bin\elasticsearch-plugin.bat install https://artifacts.elastic.co/downloads/elasticsearch-plugins/analysis-icu/analysis-icu-8.13.4.zip

# Start Elasticsearch:
C:\elasticsearch\bin\elasticsearch.bat

# Install Docker Desktop
# Then run:
docker run -d --name mongodb-container -p 27017:27017 mongo:latest

