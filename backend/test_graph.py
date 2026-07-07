import requests
import json

url = "http://127.0.0.1:8080/v1/query_graph"
data = {
    "question": "What are the top 5 selling artists?",
    "previous_sql": None
}

response = requests.post(url, json=data)
print(json.dumps(response.json(), indent=2))
