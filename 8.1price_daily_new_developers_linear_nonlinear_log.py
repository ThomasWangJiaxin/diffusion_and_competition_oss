import pandas as pd
import numpy as np
from scipy import stats

# ================= 参数 =================
CSV_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv"

# Bitcoin 2017-01-01~2019-01-01;2020-10-01~2022-10-01;2012-03-11~2025-12-31
# Ethereum 2017-01-01~2019-01-01;2020-10-01~2022-12-31;2013-12-26~2025-12-31
# 时间筛选（可以改成你需要的区间）
START_TIME = "2017-01-01"
END_TIME   = "2019-01-01"

# 列名（如有不同请改这里）
DATE_COL = "date"
DEV_COL  = "Ethereum_new_developers"
PRICE_COL = "Ethereum_closing_price"

# ================= 读取数据 =================
df = pd.read_csv(CSV_PATH)

# 解析日期
df[DATE_COL] = pd.to_datetime(df[DATE_COL])

# 按时间区间筛选
mask = (df[DATE_COL] >= START_TIME) & (df[DATE_COL] <= END_TIME)
df_sub = df.loc[mask].copy()

# 去掉缺失值
df_sub = df_sub[[DEV_COL, PRICE_COL]].dropna()

# ================= 相关分析 =================

x = df_sub[DEV_COL]
y = df_sub[PRICE_COL]

# 1. Pearson
pearson_r, pearson_p = stats.pearsonr(x, y)

# 2. Spearman
spearman_r, spearman_p = stats.spearmanr(x, y)

# 3. Log–Log（对数后再做 Pearson）
x_log = np.log(x[x > 0])
y_log = np.log(y[x > 0])   # 对齐同样索引
loglog_r, loglog_p = stats.pearsonr(x_log, y_log)

# ================= 输出结果 =================
print("===== Correlation Results =====")
print(f"Time Window: {START_TIME} to {END_TIME}")
print()
print(f"Pearson     r = {pearson_r:.4f}, p-value = {pearson_p:.4e}")
print(f"Spearman    r = {spearman_r:.4f}, p-value = {spearman_p:.4e}")
print(f"Log-Log     r = {loglog_r:.4f}, p-value = {loglog_p:.4e}")
print("================================")
