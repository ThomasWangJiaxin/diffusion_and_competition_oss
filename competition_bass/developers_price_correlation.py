# import pandas as pd
# from scipy.stats import pearsonr

# # 读取数据
# df = pd.read_csv("/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv", parse_dates=["date"])

# # 选取日期区间
# mask = (df["date"] >= "2015-01-01") & (df["date"] <= "2014-12-31")
# df = df.loc[mask].copy()

# # 提取需要的列
# x = df["btc_price"]
# y = df["btc_new_developers"]

# # 去除缺失值
# valid = ~(x.isna() | y.isna())
# x, y = x[valid], y[valid]

# # 计算 Pearson 相关系数
# r, pval = pearsonr(x, y)
# print(f"Pearson相关系数 r = {r:.4f},  p-value = {pval:.4e}")


"""
BTC 开发者数量与价格相关性分析脚本（含显著性线）
-------------------------------------------------------
功能：
1. 读取 BTC 数据（价格与新增开发者数）
2. 计算基础 Pearson 相关系数
3. 计算平滑后的相关性
4. 计算滞后（Lag）相关性
5. 绘制显著性阈值线 (95% 置信区间)
-------------------------------------------------------
作者: ChatGPT
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, t

# ========================= 参数配置 =========================
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
PRICE_COL = "btc_price"
NEW_DEV_COL = "btc_new_developers"
START_DATE = "2015-01-01"
END_DATE = "2024-12-31"
SMOOTH_WINDOW = 7        # 平滑窗口（天）
MAX_LAG = 60             # 最大滞后期（天）
OUTPUT_PNG = "btc_price_dev_correlation_sig.png"
# ============================================================


# ---------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, PRICE_COL, NEW_DEV_COL]].sort_values(DATE_COL)
    mask = (df[DATE_COL] >= START_DATE) & (df[DATE_COL] <= END_DATE)
    df = df.loc[mask].copy()
    df = df.fillna(method="ffill").fillna(0)
    return df


# ---------- 基础相关性 ----------
def basic_correlation(df):
    x, y = df[PRICE_COL], df[NEW_DEV_COL]
    valid = ~(x.isna() | y.isna())
    r, p = pearsonr(x[valid], y[valid])
    print(f"① 原始数据相关性: r = {r:.4f}, p = {p:.4e}")
    return r, p


# ---------- 平滑后相关性 ----------
def smooth_correlation(df, window=7):
    df["price_smooth"] = df[PRICE_COL].rolling(window, center=True).mean()
    df["dev_smooth"] = df[NEW_DEV_COL].rolling(window, center=True).mean()
    x, y = df["price_smooth"], df["dev_smooth"]
    valid = ~(x.isna() | y.isna())
    r, p = pearsonr(x[valid], y[valid])
    print(f"② 平滑({window})后相关性: r = {r:.4f}, p = {p:.4e}")
    return r, p


# ---------- 滞后相关性 ----------
def lag_correlation(x, y, max_lag=30):
    """计算从 -max_lag 到 +max_lag 的相关性"""
    lags, corr = [], []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            corr.append(np.corrcoef(x[:lag], y[-lag:])[0, 1])
        elif lag > 0:
            corr.append(np.corrcoef(x[lag:], y[:-lag])[0, 1])
        else:
            corr.append(np.corrcoef(x, y)[0, 1])
        lags.append(lag)
    return pd.DataFrame({"lag": lags, "corr": corr})


def significance_threshold(n, alpha=0.05):
    """计算给定样本量下的Pearson相关系数显著性阈值（双侧）"""
    df = n - 2
    t_crit = t.ppf(1 - alpha / 2, df)
    r_crit = t_crit / np.sqrt(t_crit**2 + df)
    return r_crit


def analyze_lag_correlation(df, max_lag=60):
    x = df["price_smooth"].dropna().values
    y = df["dev_smooth"].dropna().values
    corr_df = lag_correlation(x, y, max_lag=max_lag)

    # 寻找最大相关性
    best = corr_df.loc[corr_df["corr"].idxmax()]
    print(f"③ 最大滞后相关性: r = {best['corr']:.4f} 在 lag = {int(best['lag'])}")

    # 显著性阈值
    r_sig = significance_threshold(len(x))
    print(f"④ 95% 显著性阈值: |r| > {r_sig:.3f}")

    # 绘图
    plt.figure(figsize=(10, 5))
    plt.plot(corr_df["lag"], corr_df["corr"], label="相关系数曲线", linewidth=2)
    plt.axhline(y=r_sig, color="gray", linestyle="--", label="95% 显著性阈值")
    plt.axhline(y=-r_sig, color="gray", linestyle="--")
    plt.axvline(0, color="black", linestyle="--")
    plt.axvline(best["lag"], color="red", linestyle="--", label=f"最大相关滞后={int(best['lag'])}")
    plt.title("ETH 价格 与 新增开发者 滞后相关性（含显著性线）")
    plt.xlabel("滞后天数 (正值 = 价格领先)")
    plt.ylabel("Pearson相关系数")
    plt.legend()
    plt.grid(True, linestyle="--")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=300)
    print(f"📊 滞后相关性图已保存至 {OUTPUT_PNG}")

    return corr_df


# ---------- 主程序 ----------
def main():
    df = load_data()
    print(f"数据范围: {df[DATE_COL].min().date()} 至 {df[DATE_COL].max().date()} 共 {len(df)} 条记录\n")

    # 基础 & 平滑相关性
    r1, p1 = basic_correlation(df)
    r2, p2 = smooth_correlation(df, SMOOTH_WINDOW)

    # 滞后分析
    corr_df = analyze_lag_correlation(df, MAX_LAG)

    # 汇总输出
    print("\n=== 相关性结果汇总 ===")
    print(f"原始:  r = {r1:.4f}, p = {p1:.4e}")
    print(f"平滑:  r = {r2:.4f}, p = {p2:.4e}")
    print(f"滞后:  最大 r = {corr_df['corr'].max():.4f}, 对应滞后 lag = {corr_df.loc[corr_df['corr'].idxmax(), 'lag']}\n")


if __name__ == "__main__":
    main()
