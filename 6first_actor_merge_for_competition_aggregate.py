# 针对5文件进行周/月/季度的聚合

import pandas as pd
from pathlib import Path

# ==================== 配置区 ====================
INPUT_CSV = "/home/lab0/survival_diffusion_github/merged_first_actor_for_competition_day.csv"
OUTPUT_DIR = Path("/home/lab0/survival_diffusion_github")
OUTPUT_DIR.mkdir(exist_ok=True)

DATE_COL = "date"
# ===============================================

def reorder_columns_tightly(df, time_col):
    """
    把每一对 new_developers 和 cum_users 紧挨在一起
    """
    # 1. 先提取时间列
    other_cols = [c for c in df.columns if c != time_col]

    # 2. 按 repo 前缀分组（去掉后缀得到 repo 名）
    repo_dict = {}
    for col in other_cols:
        if col.endswith("_new_developers"):
            repo = col.replace("_new_developers", "")
            repo_dict.setdefault(repo, [])
            repo_dict[repo].append(col)
        elif col.endswith("_cum_users"):
            repo = col.replace("_cum_users", "")
            repo_dict.setdefault(repo, [])
            repo_dict[repo].append(col)

    # 3. 保证 new 在前、cum 在后（如果只有一列也无所谓）
    ordered_cols = [time_col]
    for repo in sorted(repo_dict.keys()):               # 按字母序保证每次结果一致
        cols = repo_dict[repo]
        new_col = [c for c in cols if c.endswith("_new_developers")]
        cum_col = [c for c in cols if c.endswith("_cum_users")]
        ordered_cols.extend(new_col + cum_col)

    return df[ordered_cols]


def main():
    print("正在读取原始数据...")
    df = pd.read_csv(INPUT_CSV, parse_dates=[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    print(f"原始数据形状: {df.shape}")

    # ==================== 周聚合 ====================
    print("\n正在生成 周 聚合数据...")
    df_w = df.copy()
    df_w["week"] = df_w[DATE_COL].dt.to_period("W").apply(lambda r: r.start_time)
    weekly = df_w.groupby("week").agg(
        {c: "sum" for c in df.columns if c.endswith("_new_developers")} |
        {c: "last" for c in df.columns if c.endswith("_cum_users")}
    ).reset_index()

    weekly = reorder_columns_tightly(weekly, "week")
    weekly.to_csv(OUTPUT_DIR / "merged_first_actor_for_competition_weekly_aggregated.csv", index=False)
    print(f"周聚合完成 → {len(weekly)} 周")

    # ==================== 月聚合 ====================
    print("\n正在生成 月 聚合数据...")
    df_m = df.copy()
    df_m["month"] = df_m[DATE_COL].dt.to_period("M").apply(lambda r: r.start_time)
    monthly = df_m.groupby("month").agg(
        {c: "sum" for c in df.columns if c.endswith("_new_developers")} |
        {c: "last" for c in df.columns if c.endswith("_cum_users")}
    ).reset_index()

    monthly = reorder_columns_tightly(monthly, "month")
    monthly.to_csv(OUTPUT_DIR / "merged_first_actor_for_competition_monthly_aggregated.csv", index=False)
    print(f"月聚合完成 → {len(monthly)} 个月")

    # ==================== 季度聚合 ====================
    print("\n正在生成 季度 聚合数据...")
    df_q = df.copy()
    df_q["quarter"] = df_q[DATE_COL].dt.to_period("Q").apply(lambda r: r.start_time)
    quarterly = df_q.groupby("quarter").agg(
        {c: "sum" for c in df.columns if c.endswith("_new_developers")} |
        {c: "last" for c in df.columns if c.endswith("_cum_users")}
    ).reset_index()

    quarterly = reorder_columns_tightly(quarterly, "quarter")
    quarterly.to_csv(OUTPUT_DIR / "merged_first_actor_for_competition_quarterly_aggregated.csv", index=False)
    print(f"季度聚合完成 → {len(quarterly)} 个季度")

    print("\n全部完成！三个文件已保存（每对 new/cum 列严格紧邻）：")
    for f in OUTPUT_DIR.glob("*aggregated.csv"):
        print("  →", f.name)

if __name__ == "__main__":
    main()