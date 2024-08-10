import sys
import os
import json
from google.cloud import tasks_v2
from google.oauth2 import service_account
from google.protobuf import duration_pb2
from firebase_admin import firestore, auth
from decouple import config

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.tasks import create_queue, auth_task

credentials = service_account.Credentials.from_service_account_file('credentials.json')
db = firestore.Client(project='feed-ai-c379d')

def feadlio_automatic_manager_task_creator():
    users_ref = db.collection(u'users').document(u'CwJacPGQ5Bg9SD0NHeRl9bWP3yw1')
    doc = users_ref.get()

    user = doc.to_dict()
    if user.get('isAutomated'):
        payload = {"uid": doc.id}
        create_queue(doc.id)
        auth_task(payload, doc.id, config("ELAINE_GENERATE_IMAGE"))
    
    print("Tasks created successfully")

feadlio_automatic_manager_task_creator()

# pecknatasha14@gmail.com