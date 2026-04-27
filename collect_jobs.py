import requests
import pandas as pd
import re

APP_ID = "6567b9ca"
APP_KEY = "12776a9c4c36d3b8d12e82eb89df5a23"

url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

#APIでデータ取得
params = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "what": "engineer",
    "results_per_page": 1
}

response = requests.get(url, params=params)
data = response.json()

jobs = data["results"]

print(jobs)