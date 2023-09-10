import json
from google.cloud import tasks_v2
from django.conf import settings
from google.protobuf import timestamp_pb2


def make_authorized_get_request():
    import google.auth.transport.requests
    import google.oauth2.id_token

    # Create a Request object
    auth_req = google.auth.transport.requests.Request()

    # Define the audience (the service or resource that will validate the ID token)
    audience = 'https://task-handler-h7k7efgceq-uc.a.run.app'  # Replace with your actual audience URL

    # Fetch the ID token by passing the Request object and audience
    id_token = google.oauth2.id_token.fetch_id_token(request=auth_req, audience=audience)


    return id_token


def enqueue_task(payload):


    client = tasks_v2.CloudTasksClient()

    # Create the parent queue name
    parent = client.queue_path(settings.GS_PROJECT_ID, settings.GS_QUEUE_REGION, settings.GS_QUEUE_NAME)

    # Create a task
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.GS_TASK_HANDLER_URL,  # Replace with your task handler URL
            "headers": {
                "Content-Type": "application/json"

            },
            "body": json.dumps(payload).encode(),
        }
    }

    # Create the task in Cloud Tasks
    response = client.create_task(parent=parent, task=task)

    # Print the task ID
    print(f"Task created: {response.name}")

