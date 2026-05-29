import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.formula.api as smf

# データ読み込み
df = pd.read_csv("data/cleaned_jobs.csv")

# スキル一覧
skills = [
    "python",
    "sql",
    "aws",
    "java",
    "javascript",
    "typescript",
    "excel",
    "tableau",
    "power_bi",
    "docker",
    "react",
    "git"
]

#スキル件数
skill_counts = df[skills].sum()
skill_counts = skill_counts[skill_counts > 0]

print("\nスキル件数")
print(skill_counts.sort_values(ascending=False))

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


#仮説1 (スキル別平均年収) 可視化

long_df = df.melt(
    id_vars=["salary"],
    value_vars=skills,
    var_name="skill",
    value_name="has_skill"
)

skill_salary_df = (
    long_df[long_df["has_skill"] == True]
    .groupby("skill")["salary"]
    .agg(["mean", "count"])
    .reset_index()
)

#高い順に並び変え
skill_salary_df = skill_salary_df.sort_values(by="mean", ascending=False)

print("\nスキル別平均給与")
print(skill_salary_df)

#グラフサイズ
plt.figure(figsize=(10, 6))

#棒グラフ
sns.barplot(
    data=skill_salary_df,
    x="mean",
    y="skill"
)

#タイトルなど
plt.title("Average Salary by Skill")
plt.xlabel("Average Salary(USD)")
plt.ylabel("Skill")

plt.tight_layout()

plt.savefig(
    "graphs/skill_salary.png",
    bbox_inches="tight"
)

plt.show()

#仮説2: 未経験OK求人の給与 可視化

experience_salary_df = (
    df.groupby("no_experience")["salary"]
    .agg(["mean", "count"])
    .reset_index()
)

print("\n未経験OK求人")
print(experience_salary_df)

#グラフサイズ
plt.figure(figsize=(6, 4))

#棒グラフ
sns.barplot(
    data=experience_salary_df,
    x="no_experience",
    y="mean"
)

#タイトルなど
plt.title("Salary by Experience Requirement")
plt.xlabel("No Experience")
plt.ylabel("Average Salary (USD)")

plt.tight_layout()

plt.savefig(
    "graphs/no_experience_salary.png",
    bbox_inches="tight"
)

plt.show()


#仮説3: リモート求人の給与 可視化

remote_salary_df = (
    df.groupby("remote")["salary"]
    .agg(["mean", "count"])
    .reset_index()
)

print("\nリモート求人")
print(remote_salary_df)

#グラフサイズ
plt.figure(figsize=(6, 4))

#棒グラフ
sns.barplot(
    data=remote_salary_df,
    x="remote",
    y="mean"
)

#タイトルなど
plt.title("Salary by Remote Availability")
plt.xlabel("Remote")
plt.ylabel("Average Salary(USD)")

plt.tight_layout()

plt.savefig(
    "graphs/remote_salary.png",
    bbox_inches="tight"
)

plt.show()
