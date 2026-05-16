import pandas as pd

# ====== 配置：替换为 weekly / monthly / quarterly 文件 ======
INPUT = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_weekly_timeline_event_all_with_price_features.csv"
OUTPUT = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_weekly_timeline_event_all_with_price_event_features.csv"

# 若处理 BTC：只改 INPUT 和 OUTPUT 即可
# 若处理 monthly/quarterly：同样改路径即可

# ====== 加载数据（已按周期聚合，无需 parse_dates）======
df = pd.read_csv(INPUT)

# 排序（避免用户文件周期顺序错乱）
if "date" in df.columns:
    df = df.sort_values("date").reset_index(drop=True)
elif "period" in df.columns:
    df = df.sort_values("period").reset_index(drop=True)

# ====== 自动识别事件列 ======
event_cols = [
    col for col in df.columns
    if col.endswith("_event") and not col.startswith("price")
]

print("事件列：", event_cols)

# ====== 生成滞后与窗口统计量 ======
WINDOWS = [2, 4, 6, 8, 10]


def insert_after(df, ref_col, new_cols):
    """将新列插入到 ref_col 后面"""
    ref_idx = df.columns.get_loc(ref_col)
    new_cols = [c for c in new_cols if c not in df.columns]
    df = df[df.columns[:ref_idx+1].tolist()
            + new_cols
            + df.columns[ref_idx+1:].tolist()]
    return df


for col in event_cols:

    new_cols = []

    # -------- lag1 --------
    lag1 = f"{col}_lag1"
    df[lag1] = df[col].shift(1)
    new_cols.append(lag1)

    # -------- windows: sum, mean, vol --------
    for n in WINDOWS:

        # sum
        sum_col = f"{col}_sum_{n}"
        df[sum_col] = df[col].shift(1).rolling(n).sum()
        new_cols.append(sum_col)

        # mean
        mean_col = f"{col}_mean_{n}"
        df[mean_col] = df[col].shift(1).rolling(n).mean()
        new_cols.append(mean_col)

        # vol
        vol_col = f"{col}_vol_{n}"
        df[vol_col] = df[col].shift(1).rolling(n).std()
        new_cols.append(vol_col)

    # 插入事件列后
    df = insert_after(df, col, new_cols)


# ====== 保存输出 ======
df.to_csv(OUTPUT, index=False)
print(f"已经生成特征文件：{OUTPUT}")