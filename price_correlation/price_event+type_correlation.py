import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# ===============================
# 用户指定日期范围（新增）
# ===============================
start_date = "2017-01-01"
end_date = "2019-01-01"

# 读取数据
try:
    event_data = pd.read_csv('/home/lab0/survival_diffusion_github/Ethereum/eth_event_daily_stats_timeline_event.csv')
    price_data = pd.read_csv('/home/lab0/survival_diffusion_github/price_eth_20152025.csv')
except FileNotFoundError as e:
    print(f"Error: CSV file not found. Please check file paths. {e}")
    exit(1)

# 日期格式处理
event_data['date'] = pd.to_datetime(event_data['date'])
price_data['Date'] = pd.to_datetime(price_data['Date'])

# ===============================
# 日期过滤（新增）
# ===============================
event_data = event_data[(event_data['date'] >= start_date) & (event_data['date'] <= end_date)]
price_data = price_data[(price_data['Date'] >= start_date) & (price_data['Date'] <= end_date)]

print(f"时间范围筛选后：事件数据 {len(event_data)} 条，价格数据 {len(price_data)} 条")

# 事件列
event_columns = [
    'CommitCommentEvent', 'CreateEvent', 'DeleteEvent', 'ForkEvent',
    'IssueCommentEvent', 'IssuesEvent', 'PullRequestEvent',
    'PullRequestReviewCommentEvent', 'PullRequestReviewEvent',
    'PushEvent', 'ReleaseEvent', 'WatchEvent', 'All_events'
]

# ================
# 累计事件量
# ================
for col in event_columns:
    event_data[f'Cum_{col}'] = event_data[col].cumsum()

# ================
# 滚动 7/14/21/30（window 在筛选后的数据范围上重新计算）
# ================
windows = [7, 14, 21, 30]
for col in event_columns:
    for w in windows:
        event_data[f'Roll{w}_{col}'] = event_data[col].rolling(window=w).sum()

# 合并
merged_data = pd.merge(event_data, price_data, left_on='date', right_on='Date', how='inner')

# 构造最终数据
data = merged_data[
    event_columns +
    [f'Cum_{col}' for col in event_columns] +
    [f'Roll{w}_{col}' for col in event_columns for w in windows] +
    ['Close', 'Change %']
]

# 转成数值
for col in data.columns:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# 可打开用于百分比处理
# data['Change %'] = data['Change %'].str.rstrip('%').astype(float) / 100

# 缺失处理
if data.isnull().any().any():
    print("Warning: Missing values detected. Filling with 0.")
    data.fillna(0, inplace=True)

# ===============================
# 定义非线性变换函数
# ===============================
def nonlinear_transforms(x):
    return {
        'log1p': np.log1p(x),
        'sqrt': np.sqrt(x),
        'squared': x**2
    }

# ===============================
# 相关性计算函数
# ===============================
def compute_corr(var_name, x, y):
    corr, p = pearsonr(x, y)
    print(f"{var_name:<30} — Price: {corr:.4f} (p={p:.4f})")
    return corr, p

# ===============================
# 1. 每日事件量 + 非线性
# ===============================
print("\n=== 每天事件量（含 log / sqrt / squared）与 Price 的相关性 ===")
for col in event_columns:
    x = data[col]

    compute_corr(col, x, data['Close'])

    # 非线性变换
    for tname, tval in nonlinear_transforms(x).items():
        compute_corr(f"{col}_{tname}", tval, data['Close'])

    print("-" * 60)

# ===============================
# 2. 累计事件量 + 非线性
# ===============================
print("\n=== 累计事件量（含 log / sqrt / squared）与 Price 的相关性 ===")
for col in event_columns:
    base = data[f'Cum_{col}']
    compute_corr(f"Cum_{col}", base, data['Close'])

    for tname, tval in nonlinear_transforms(base).items():
        compute_corr(f"Cum_{col}_{tname}", tval, data['Close'])

    print("-" * 60)

# ===============================
# 3. 滚动事件量 + 非线性
# ===============================
print("\n=== 过去 7/14/21/30 天事件量（含 log / sqrt / squared）与 Price 的相关性 ===")
for col in event_columns:
    for w in windows:
        base_name = f'Roll{w}_{col}'
        base = data[base_name]

        compute_corr(base_name, base, data['Close'])

        for tname, tval in nonlinear_transforms(base).items():
            compute_corr(f"{base_name}_{tname}", tval, data['Close'])

    print("-" * 60)
