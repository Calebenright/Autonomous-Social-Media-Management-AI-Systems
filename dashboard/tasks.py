import json
from google.cloud import tasks_v2
from google.oauth2 import service_account
from google.protobuf import duration_pb2
from google.api_core.exceptions import NotFound
import json
from decouple import config

credentials = service_account.Credentials.from_service_account_file('credentials.json')

def get_cloud_tasks_client():
    """ Helper function to create a Cloud Tasks client with the necessary credentials. """
    return tasks_v2.CloudTasksClient(credentials=credentials)

def enqueue_task(payload, queue_name, queue_url):
    client = get_cloud_tasks_client()
    parent = client.queue_path(config("GS_PROJECT_ID"), config("GS_QUEUE_REGION"), queue_name)

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
    client = get_cloud_tasks_client()
    parent = client.queue_path(config("GS_PROJECT_ID"), config("GS_QUEUE_REGION"), queue_name)

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
    client = get_cloud_tasks_client()
    parent = client.queue_path(config("GS_PROJECT_ID"), config("GS_QUEUE_REGION"), queue_name)
    API_TOKEN = config("API_TOKEN")
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

def create_queue(queue):
    location = config("GS_QUEUE_REGION")
    project = config("GS_PROJECT_ID")
    client = get_cloud_tasks_client()

    parent = f"projects/{project}/locations/{location}"
    queue_path = client.queue_path(project, location, queue)

    retry_config = {
        'max_attempts': 1
    }

    try:
        client.get_queue(name=queue_path)
        print(f"Queue '{queue}' already exists.")
        return False
    except NotFound:
        queue_obj = client.create_queue(
            parent=parent,
            queue={
                "name": queue_path,
                "retry_config": retry_config
            }
        )
        print('Created queue with no retries:', queue_obj.name)
        return True


