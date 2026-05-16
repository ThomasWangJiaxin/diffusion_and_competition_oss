import pandas as pd
import numpy as np

# ====== 配置 ======
INPUT = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_features.csv"
OUTPUT = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"

# 若处理 ETH，只需替换上面 INPUT/OUTPUT 即可


# ====== 加载并按日期排序 ======
df = pd.read_csv(INPUT, parse_dates=["date"]).sort_values("date").reset_index(drop=True)


# ====== 找到所有事件列 ======
# p 类：btc_p_event, bip_p_event, btc_p_bip_p_event 等
# q 类：btc_q_event, bip_q_event, ...
# n 类（因变量）：btc_event, bip_event, btc_bip_event
event_cols = [
    col for col in df.columns
    if col.endswith("_event") and not col.startswith("price")
]

print("事件列如下：")
print(event_cols)

# ====== 此函数用于把生成的新列插到原列后 ======
def insert_after(df, ref_col, new_cols):
    ref_idx = df.columns.get_loc(ref_col)
    new_cols = [c for c in new_cols if c not in df.columns]  # 避免重复
    df = df[df.columns[:ref_idx+1].tolist() + new_cols + df.columns[ref_idx+1:].tolist()]
    return df


# ====== 事件滞后 / 汇总 / 波动 指标 ======
WINDOWS = [7, 14, 21, 30]

for col in event_cols:

    new_cols = []

    # ---------- lag1 ----------
    lag1 = f"{col}_lag1"
    df[lag1] = df[col].shift(1)
    new_cols.append(lag1)

    # ---------- 窗口指标 ----------
    for n in WINDOWS:

        # sum
        sum_col = f"{col}_sum_{n}"
        df[sum_col] = df[col].shift(1).rolling(n).sum()
        new_cols.append(sum_col)

        # mean
        mean_col = f"{col}_mean_{n}"
        df[mean_col] = df[col].shift(1).rolling(n).mean()
        new_cols.append(mean_col)

        # vol (波动 = std)
        vol_col = f"{col}_vol_{n}"
        df[vol_col] = df[col].shift(1).rolling(n).std()
        new_cols.append(vol_col)

    # 插在事件列后面
    df = insert_after(df, col, new_cols)


# ====== 保存 ======
df.to_csv(OUTPUT, index=False)
print(f"\n已保存至：{OUTPUT}")
