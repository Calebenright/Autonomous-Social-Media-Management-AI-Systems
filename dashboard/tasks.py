import json
from google.cloud import tasks_v2
from django.conf import settings
from google.protobuf import timestamp_pb2
from google.protobuf import duration_pb2
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

def post_task(payload, queue_name, queue_url):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, queue_name)

    task_payload = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": queue_url,
            "oidc_token": {
                "service_account_email": "main-service@starter-web-app-389316.iam.gserviceaccount.com",
                "audience": "https://us-central1-feed-ai-c379d.cloudfunctions.net/post_to_social",
            },
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(payload).encode(),
        }
    }

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

def make_authorized_get_request():
    import google.auth.transport.requests
    import google.oauth2.id_token
    auth_req = google.auth.transport.requests.Request()
    audience = 'https://task-handler-h7k7efgceq-uc.a.run.app'
    id_token = google.oauth2.id_token.fetch_id_token(request=auth_req, audience=audience)
    return id_token

