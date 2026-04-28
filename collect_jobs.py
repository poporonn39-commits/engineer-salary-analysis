import requests
import pandas as pd
import re

APP_ID = "6567b9ca"
APP_KEY = "12776a9c4c36d3b8d12e82eb89df5a23"

keywords = [
    "data analyst",
    "junior analyst",
    "senior data analyst",
    "business analyst",
    "bi analyst"
]

#複数ページ取得
all_jobs = []

for keyword in keywords:
    print(f"\n検索中: {keyword}")

    for page in range(1, 3):

        url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": "data analyst",
            "results_per_page": 50
        }

        response = requests.get(url, params=params)
        data = response.json()

        jobs = data["results"]

        print(f"{page}ページ目取得件数:", len(jobs))

        all_jobs.extend(jobs)

print("\n取得総件数:", len(all_jobs))

#前処理
skills = ["python", "sql", "aws", "java", "javascript", "excel", "tableau", "power bi", "sas", "r", "spark"]

processed = []

for job in all_jobs:
    item = {
        "title": job.get("title", ""),
        "company": job.get("company", {}).get("display_name", ""),
        "description": job.get("description", ""),
        "location": job.get("location", {}).get("display_name", ""),
        "salary_max": job.get("salary_max"),
        "salary_min": job.get("salary_min"),
        "salary_is_predicted": job.get("salary_is_predicted")
    }

    #平均給与作成
    if item["salary_min"] is not None and item["salary_max"] is not None:
        item["salary"] = (item["salary_min"] + item["salary_max"]) / 2
    else:
        item["salary"] = None

    text = item["description"].lower()

    #スキル判定
    item["python"] = "python" in text
    item["sql"] = "sql" in text
    item["aws"] = "aws" in text

    item["java"] = re.search(r"\bjava\b",text) is not None
    item["javascript"] = re.search(r"\bjavascript\b", text) is not None

    item["excel"] = "excel" in text
    item["tableau"] = "tableau" in text
    item["power_bi"] = re.search(r"\bpower bi\b", text) is not None
    item["sas"] = re.search(r"\bsas\b", text) is not None
    item["r"] = re.search(r"\br\b", text) is not None
    item["spark"] = re.search(r"\bspark\b", text) is not None

    processed.append(item)

#DataFrame化
df = pd.DataFrame(processed)

print("重複削除前:", len(df))

#情報確認用
#print(df.head())

#print(df.info())

#重複削除
df = df.drop_duplicates(subset=["title", "company", "location"])
print("重複削除後:", len(df))

#スキル件数TOP5

skill_cols = ["python", "sql", "aws", "java", "javascript", "excel", "tableau", "power_bi", "sas", "r", "spark"]

skill_counts = df[skill_cols].sum()

print("スキル件数TOP5")
print(skill_counts.sort_values(ascending=False).head(5))

#給与概要
df = df[df["salary"] >= 50000]
print("\n給与統計")
print(df["salary"].describe())