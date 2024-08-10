import requests

url = "https://feadl.io/master_automatic_manager_task_creator/"
headers = {
    "Authorization": "Bearer 12876324876230984798374",
    "Content-Type": "application/json",
    "User-Agent": "Google-Cloud-Scheduler"
}
response = requests.post(url, headers=headers, json={})  # Assuming an empty JSON body; adjust as needed.

print(response.text)
