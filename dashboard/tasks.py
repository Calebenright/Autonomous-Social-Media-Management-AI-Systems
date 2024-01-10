import json
from google.cloud import tasks_v2
from django.conf import settings
from google.protobuf import timestamp_pb2
from google.protobuf import duration_pb2
import json

def enqueue_task(payload, queue_name, queue_url):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, queue_name)

    # Construct the task payload
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

    # Set the task schedule time (optional)
    # task_schedule_time = timestamp_pb2.Timestamp(seconds=int(time.time()) + 60)  # Task will be scheduled to run after 1 minute
    # task_payload["schedule_time"] = task_schedule_time

    task = client.create_task(parent=parent, task=task_payload)
    print(f"Task created: {task.name}")

def make_authorized_get_request():
    import google.auth.transport.requests
    import google.oauth2.id_token
    auth_req = google.auth.transport.requests.Request()
    audience = 'https://task-handler-h7k7efgceq-uc.a.run.app'
    id_token = google.oauth2.id_token.fetch_id_token(request=auth_req, audience=audience)
    return id_token

