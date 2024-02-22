import json
from google.cloud import tasks_v2
from google.oauth2 import service_account
from django.conf import settings
from google.protobuf import duration_pb2, timestamp_pb2
from google.api_core.exceptions import NotFound, AlreadyExists
import json

def enqueue_task(payload, queue_name, queue_url):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, queue_name)

    task_payload = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": queue_url,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(payload).encode(),
        }
    }

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

def gc_task(payload, queue_name, queue_url):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, queue_name)

    task_payload = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": queue_url,
            "headers": {
                "Content-Type": "application/json"
            },
            "oidc_token": {
                "service_account_email": "main-service@starter-web-app-389316.iam.gserviceaccount.com"
            },
            "body": json.dumps(payload).encode(),
        }
    }

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

def auth_task(payload, queue_name, queue_url):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, queue_name)
    API_TOKEN = settings.API_TOKEN
    dispatch_deadline = duration_pb2.Duration(seconds=600)
    task_payload = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": queue_url,
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_TOKEN}"
            },
            "body": json.dumps(payload).encode(),
        },
        "dispatch_deadline": dispatch_deadline,
    }

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

from google.api_core.exceptions import AlreadyExists

def create_queue(queue):
    location = 'us-central1'
    project = 'starter-web-app-389316'
    client = tasks_v2.CloudTasksClient()

    parent = f"projects/{project}/locations/{location}"
    queue_path = client.queue_path(project, location, queue)

    try:
        client.get_queue(name=queue_path)
        print(f"Queue '{queue}' already exists.")
        return False  
    except NotFound:
        queue_obj = client.create_queue(parent=parent, queue={"name": queue_path})
        print('Created queue:', queue_obj.name)
        return True 
    except AlreadyExists:
        print(f"Queue '{queue}' already exists.")
        return False 


def make_authorized_get_request():
    import google.auth.transport.requests
    import google.oauth2.id_token
    auth_req = google.auth.transport.requests.Request()
    audience = 'https://task-handler-h7k7efgceq-uc.a.run.app'
    id_token = google.oauth2.id_token.fetch_id_token(request=auth_req, audience=audience)
    return id_token

