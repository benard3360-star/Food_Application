import firebase_admin
from firebase_admin import credentials, firestore

# Use a raw string (prefix with r) to avoid escaping issues
cred = credentials.Certificate(r'C:\Users\user\OneDrive - Strathmore University\Projects4\food_price_project\credentials\food-price-prediction-firebase-adminsdk-fbsvc-eb4cf9aab1.json')

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
