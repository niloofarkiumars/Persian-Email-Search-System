from dotenv import load_dotenv
import os

load_dotenv()

print(f"ES_HOST: {os.getenv('ES_HOST')}")
print(f"ES_USERNAME: {os.getenv('ES_USERNAME')}")
print(f"MONGO_HOST: {os.getenv('MONGO_HOST')}")
print(f"INDEX_NAME: {os.getenv('INDEX_NAME')}")

if os.getenv('ES_PASSWORD') == 'YOUR_PASSWORD_HERE':
    print("⚠️ WARNING: You haven't changed the password in .env!")
else:
    print("✅ Password configured")