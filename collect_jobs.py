import requests
import pandas as pd
import re

APP_ID = "6567b9ca"
APP_KEY = "12776a9c4c36d3b8d12e82eb89df5a23"

keywords = [
    "data analyst",
    "software engineer",
    "frontend engineer",
    "backend engineer",
    "full stack engineer",
    "junior developer",
    "entry level analyst",
    "junior data analyst",
    "graduate engineer"
]

#複数ページ取得
all_jobs = []

for keyword in keywords:
    print(f"\n検索中: {keyword}")

    for page in range(1, 4):

        url = "https://api.adzuna.com/v1/api/jobs/us/search/" + str(page)

        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": keyword,
            "results_per_page": 50
        }

        response = requests.get(url, params=params)
        data = response.json()

        jobs = data.get("results", [])

        print(f"{keyword} page{page}: {len(jobs)}件")

        #どの検索語で取れた求人か保存
        for job in jobs:
            job["searched_keyword"] = keyword

        all_jobs.extend(jobs)

print("\n取得総件数:", len(all_jobs))

#前処理
skills = ["python", "sql", "aws", "java", "javascript", "typescript", "excel", "tableau", "power_bi", "docker", "react", "git"]

processed = []

for job in all_jobs:
    item = {
        "keyword": job.get("searched_keyword", ""),
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

    item["typescript"] = "typescript" in text
    item["excel"] = "excel" in text
    item["tableau"] = "tableau" in text
    item["power_bi"] = "power bi" in text or "powerbi" in text
    item["docker"] = "docker" in text
    item["react"] = "react" in text
    item["git"] = "git" in text

    # 仮説2: 未経験OK判定
    search_kw = item["keyword"].lower()

    strong_keywords = [
        "no experience",
        "entry level",
        "trainee",
        "fresh graduate"
    ]

    medium_keywords = [
        "junior",
        "graduate",
        "training provided",
        "assistant",
        "intern"
    ]

    negative_keywords = [
        "3+ years",
        "5+ years",
        "7+ years",
        "senior",
        "lead",
        "manager",
        "principal"
    ]

    score = 0

    for word in ["junior", "entry level", "graduate"]:
        if word in search_kw:
            score += 3

    for word in strong_keywords:
        if word in text:
            score += 2

    for word in medium_keywords:
        if word in text:
            score += 1

    for word in negative_keywords:
        if word in text:
            score -= 2

    item["no_experience"] = score >= 2
    
    #仮説3: リモート可判定
    item["remote"] = (
        "remote" in text or
        "work from home" in text or
        "hybrid" in text
    )

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

#スキル件数TOP7
skill_counts = df[skills].sum()
skill_counts = skill_counts[skill_counts > 0]

print("スキル件数TOP7")
print(skill_counts.sort_values(ascending=False).head(7))

#給与あり&ノイズ除去
df = df[df["salary"].notna()]
df = df[df["salary"] >= 50000]

#給与概要
print("\n給与統計")
print(df["salary"].describe())

#職種別平均給与
print("\n職種別平均給与")
print(df.groupby("keyword")["salary"].mean().sort_values(ascending=False))

#仮説1: スキル有無で年収差
print("\n--- 仮説1: スキル有無で年収差 ---")

for skill in skills:
    result = df.groupby(skill)["salary"].mean()
    print(f"\n{skill}")
    print(result)

#仮説2: 未経験OK求人は低年収か
print("\n--- 仮説2: 未経験OK求人の給与 ---")
print(df.groupby("no_experience")["salary"].agg(["mean", "count"]))

print("\n職種別 * 未経験OK")
print(df.groupby(["keyword", "no_experience",])["salary"].agg(["mean", "count"]).sort_values(by="mean", ascending=False))

#仮説3: リモート可求人は高収入か
print("\n--- 仮説3: リモート求人の給与 ---")
print(df.groupby("remote")["salary"].mean())

print("\n職種別 * リモート")
