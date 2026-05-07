import requests
import pandas as pd
import re
import time
import statsmodels.formula.api as smf

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

        time.sleep(1)

        data = response.json()

        jobs = data.get("results", [])

        print(f"{keyword} page{page}: {len(jobs)}件")

        #どの検索語で取れた求人か保存
        for job in jobs:
            job["searched_keyword"] = keyword

        all_jobs.extend(jobs)

print("\n取得総件数:", len(all_jobs))

#前処理
skill_patterns = {
    "python": r"\bpython\b",
    "sql": r"\bsql\b",
    "aws": r"\baws\b",
    "java": r"\bjava\b",
    "javascript": r"\bjavascript\b",
    "typescript": r"\btypescript\b",
    "excel": r"\bexcel\b",
    "tableau": r"\btableau\b",
    "power_bi": r"power bi|powerbi",
    "docker": r"\bdocker\b",
    "react": r"\breact\b",
    "git": r"\bgit\b"
}

skills = list(skill_patterns.keys())

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

    text = (item["title"] + " " + item["description"]).lower()

    #スキル判定
    for skill, pattern in skill_patterns.items():
        item[skill] = re.search(pattern, text) is not None

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

#推定給与除外
#df = df[df["salary_is_predicted"] == "0"]

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
    
#仮説1(改善版): 職種ごと * スキル
print("\n--- 仮説1 (改善版): 職種ごと * スキル ---")

for skill in skills:
    print(f"\n{skill}")

    result = df.groupby(["keyword", skill])["salary"].mean().unstack()

    if True in result.columns and False in result.columns:
        result["diff"] = result[True] - result[False]
        print(result)

#スキル数と年収
df["skill_count"] = df[skills].sum(axis=1)


print("\nスキル数 * 年収")
print(df.groupby("skill_count")["salary"].mean())

#仮説2: 未経験OK求人は低年収か
print("\n--- 仮説2: 未経験OK求人の給与 ---")
print(df.groupby("no_experience")["salary"].agg(["mean", "count"]))

print("\n職種別 * 未経験OK")
print(df.groupby(["keyword", "no_experience",])["salary"].agg(["mean", "count"]).sort_values(by="mean", ascending=False))

print(("\n--- 仮説2 (件数、割合確認)"))
print(df["no_experience"].value_counts())
print(df["no_experience"].value_counts(normalize=True) * 100)


#仮説3: リモート可求人は高収入か
print("\n--- 仮説3: リモート求人の給与 ---")
print(df.groupby("remote")["salary"].mean())

print("\n職種別 * リモート")
print(df.groupby(["keyword", "remote"])["salary"].mean().unstack())


#回帰分析用
reg_df = df.copy()

binary_cols = ["python", "sql", "aws", "remote", "no_experience"]

for col in binary_cols:
    reg_df[col] = reg_df[col].astype(int)

#重回帰分析
model = smf.ols("salary ~ python + sql + aws + remote + no_experience + C(keyword)", data=reg_df).fit()

print(model.summary())