# import pandas as pd
# from scipy import stats

# # === 参数设置 ===
# # 可以自行修改路径和字段名
# event_file = "/home/lab0/survival_diffusion_github/Ethereum/eth_event_daily_stats.csv"
# price_file = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# price_column = "eth_price"  # ← 请手动改成价格列名，如 'btc_price'
# date_col_event = "date"
# date_col_price = "date"

# # 定义事件分类（可以根据需要修改）
# p_events = ["CreateEvent", "IssuesEvent", "PushEvent", "ReleaseEvent", "DeleteEvent", "MemberEvent", "GollumEvent"]
# q_events = ["CommitCommentEvent", "ForkEvent", "IssueCommentEvent",
#             "PullRequestEvent", "PullRequestReviewCommentEvent",
#             "PullRequestReviewEvent", "WatchEvent"]

# # === 读取数据 ===
# event_df = pd.read_csv(event_file)
# price_df = pd.read_csv(price_file)

# # 统一日期格式
# event_df[date_col_event] = pd.to_datetime(event_df[date_col_event])
# price_df[date_col_price] = pd.to_datetime(price_df[date_col_price])

# # 合并
# merged = pd.merge(event_df, price_df[[date_col_price, price_column]],
#                   left_on=date_col_event, right_on=date_col_price, how="inner")

# # === 自动检测事件列 ===
# event_cols = [c for c in event_df.columns if c not in [date_col_event, "总数"]]

# # === 计算主动类与模仿类事件总和 ===
# merged["p_total"] = merged[[c for c in p_events if c in merged.columns]].sum(axis=1)
# merged["q_total"] = merged[[c for c in q_events if c in merged.columns]].sum(axis=1)

# # === 定义计算相关性与显著性函数 ===
# def corr_sig(x, y):
#     if x.nunique() < 2 or y.nunique() < 2:
#         return (None, None)
#     r, pval = stats.pearsonr(x, y)
#     return (r, pval)

# # === 计算所有事件的相关性 ===
# results = []

# for col in event_cols + ["总数", "p_total", "q_total"]:
#     if col not in merged.columns:
#         continue
#     r, pval = corr_sig(merged[col], merged[price_column])
#     results.append({"event": col, "correlation": r, "p_value": pval})

# # === 输出结果 ===
# result_df = pd.DataFrame(results).sort_values("correlation", ascending=False)
# print(result_df.to_string(index=False))

# # === 可选：保存到CSV ===
# result_df.to_csv("event_price_correlation_results.csv", index=False)
# print("\n✅ 结果已保存至 event_price_correlation_results.csv")


# ===========
# 考虑滞后
# 事件领先价格 7 天（看看开发活动是否提前反映市场）：
# lag_days = 7
# 价格领先事件 7 天（看看价格波动是否带动开发活动）：
# lag_days = -7

import pandas as pd
import numpy as np
from scipy import stats

# === 参数设置 ===
event_file = "/home/lab0/survival_diffusion_github/Bitcoin/bips_event_daily_stats.csv"
price_file = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
price_column = "eth_price"  # ← 改成价格列名
date_col_event = "date"
date_col_price = "date"

# 时间与滞后参数
start_date = "2015-01-01"  # 可设为 None
end_date = "2024-12-31"
lag_days = 0  # 正数: 事件领先价格; 负数: 价格领先事件

# === 定义事件分类 ===
p_events = ["CreateEvent", "PushEvent", "DeleteEvent", "GollumEvent"]
q_events = [
    "CommitCommentEvent", "ForkEvent", "IssueCommentEvent",
    "PullRequestEvent", "PullRequestReviewCommentEvent",
    "PullRequestReviewEvent", "WatchEvent",
]

# === 读取数据 ===
event_df = pd.read_csv(event_file)
price_df = pd.read_csv(price_file)

# === 日期解析（自动推断格式） ===
event_df[date_col_event] = pd.to_datetime(event_df[date_col_event], errors="coerce", infer_datetime_format=True)
price_df[date_col_price] = pd.to_datetime(price_df[date_col_price], errors="coerce", infer_datetime_format=True)

# === 筛选日期范围 ===
if start_date:
    event_df = event_df[event_df[date_col_event] >= pd.to_datetime(start_date)]
if end_date:
    event_df = event_df[event_df[date_col_event] <= pd.to_datetime(end_date)]

# === 滞后调整 ===
if lag_days != 0:
    print(f"⏱ 应用滞后：价格序列平移 {lag_days} 天")
    price_df[price_column] = price_df[price_column].shift(lag_days)

# === 合并数据 ===
merged = pd.merge(
    event_df,
    price_df[[date_col_price, price_column]],
    left_on=date_col_event,
    right_on=date_col_price,
    how="inner"
)

# === 自动检测事件列 ===
event_cols = [c for c in event_df.columns if c not in [date_col_event, "总数"]]

# === 计算主动类与模仿类事件总和 ===
merged["p_total"] = merged[[c for c in p_events if c in merged.columns]].sum(axis=1)
merged["q_total"] = merged[[c for c in q_events if c in merged.columns]].sum(axis=1)

# === 清洗数据（去掉NaN和inf） ===
merged.replace([np.inf, -np.inf], np.nan, inplace=True)
merged.dropna(subset=[price_column], inplace=True)

# === 相关性计算函数 ===
def corr_sig(x, y):
    valid = (~x.isna()) & (~y.isna())
    if valid.sum() < 3 or x[valid].nunique() < 2 or y[valid].nunique() < 2:
        return (np.nan, np.nan)
    r, pval = stats.pearsonr(x[valid], y[valid])
    return (r, pval)

# === 执行计算 ===
results = []
for col in event_cols + ["总数", "p_total", "q_total"]:
    if col not in merged.columns:
        continue
    r, pval = corr_sig(merged[col], merged[price_column])
    results.append({"event": col, "correlation": r, "p_value": pval})

# === 输出结果 ===
result_df = pd.DataFrame(results).sort_values("correlation", ascending=False)
print("\n📊 事件与价格相关性结果（滞后={} 天）:".format(lag_days))
print(result_df.to_string(index=False))

# === 保存 ===
out_file = f"event_price_correlation_results_lag{lag_days}.csv"
result_df.to_csv(out_file, index=False)
print(f"\n✅ 结果已保存至 {out_file}")


