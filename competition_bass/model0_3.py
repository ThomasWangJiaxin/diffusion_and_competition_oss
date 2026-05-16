# # 离散模型model0_2.py改成周/月/季度通用版

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# import scipy.stats as stats
# import matplotlib.pyplot as plt
# import datetime as dt

# # ======================================================
# # 选择频率： "weekly" / "monthly" / "quarterly"
# # ======================================================
# FREQ = "quarterly"      # <<< 改这里即可！ weekly / monthly / quarterly

# # ======================================================
# # 自动选择文件路径
# # ======================================================
# FILE_MAP = {
#     "weekly": "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_weekly_timeline_event_all.csv",
#     "monthly": "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_monthly_timeline_event_all.csv",
#     "quarterly": "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_quarterly_timeline_event_all.csv",
# }

# CSV_PATH = FILE_MAP[FREQ]

# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"

# START = "2017-01"
# END = "2019-01"

# OUTPUT_PNG_NEW = f"btc_bass_new_{FREQ}.png"
# OUTPUT_PNG_CUM = f"btc_bass_cum_{FREQ}.png"
# OUTPUT_CSV = f"btc_bass_results_discrete_{FREQ}.csv"


# # ======================================================
# # 工具函数：解析不同频率日期
# # ======================================================

# def parse_period(x):
#     """将周/月/季度 字符串转换为 datetime"""
#     x = str(x)

#     # weekly: 2021-03-05-2021-03-11
#     if "-" in x and len(x) > 10:
#         start = x.split("-")[0:3]   # ['2021','03','05']
#         date_str = "-".join(start)
#         return pd.to_datetime(date_str)

#     # monthly: 2021-03
#     if len(x) == 7:
#         return pd.to_datetime(x + "-01")

#     # quarterly: 2021-Q1
#     if "Q" in x:
#         return pd.Period(x, freq="Q").start_time

#     # fallback
#     return pd.to_datetime(x)


# # ======================================================
# # 读取数据
# # ======================================================
# def load_data():
#     df = pd.read_csv(CSV_PATH)

#     df[DATE_COL] = df[DATE_COL].apply(parse_period)

#     df = df[[DATE_COL, NEW_COL, CUM_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# # ======================================================
# # 离散 Bass 模型
# # ======================================================
# def bass_discrete_new(t, p, q, m, N0):
#     T = len(t)
#     N = np.zeros(T)
#     dN = np.zeros(T)
#     N[0] = N0

#     for i in range(1, T):
#         dN[i] = (p + q * (N[i - 1] / m)) * (m - N[i - 1])
#         N[i] = N[i - 1] + dN[i]

#     return dN


# def simulate_bass_discrete(p, q, m, N0, T):
#     N = np.zeros(T)
#     dN = np.zeros(T)
#     N[0] = N0
#     for i in range(1, T):
#         dN[i] = (p + q * (N[i - 1] / m)) * (m - N[i - 1])
#         N[i] = N[i - 1] + dN[i]
#     return N, dN


# # ======================================================
# # 拟合
# # ======================================================
# def fit_bass_discrete(df):
#     y_true_dN = df[NEW_COL].values
#     y_true_cum = df[CUM_COL].values
#     N0 = y_true_cum[0]

#     t = np.arange(len(df))

#     m_guess = y_true_cum[-1] * 1.2
#     p0 = [0.01, 0.3, m_guess]

#     bounds_lower = [1e-6, 0, y_true_cum[-1] * 0.5]
#     bounds_upper = [0.99, 1.0, y_true_cum[-1] * 20.0]

#     def model(t, p, q, m):
#         return bass_discrete_new(t, p, q, m, N0)

#     popt, pcov = curve_fit(
#         model, t, y_true_dN,
#         p0=p0, bounds=(bounds_lower, bounds_upper),
#         maxfev=10000
#     )

#     p, q, m = popt
#     N_pred, dN_pred = simulate_bass_discrete(p, q, m, N0, len(df))

#     rmse_dN = np.sqrt(np.mean((y_true_dN - dN_pred) ** 2))

#     se = np.sqrt(np.diag(pcov))
#     residuals = y_true_dN - dN_pred

#     n = len(df)
#     k = 3

#     tvals = popt / se
#     pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), df=n - k))

#     return popt, {
#         "se": se,
#         "tvals": tvals,
#         "pvals": pvals,
#         "rmse_dN": rmse_dN,
#         "N_pred": N_pred,
#         "dN_pred": dN_pred,
#         "N0": N0
#     }


# # ======================================================
# # 主程序
# # ======================================================
# def main():
#     df = load_data()
#     df = select_date(df, START, END)

#     print(f"\n=== Fitting Discrete Bass Model ({FREQ}) ===")
#     popt, fit_info = fit_bass_discrete(df)

#     p, q, m = popt
#     se_p, se_q, se_m = fit_info["se"]
#     t_p, t_q, t_m = fit_info["tvals"]
#     pv_p, pv_q, pv_m = fit_info["pvals"]
#     rmse = fit_info["rmse_dN"]

#     print("\n=== Parameter Estimates ===")
#     print(f"p = {p:.6f}  (SE={se_p:.6f}, t={t_p:.3f}, p={pv_p:.3f})")
#     print(f"q = {q:.6f}  (SE={se_q:.6f}, t={t_q:.3f}, p={pv_q:.3f})")
#     print(f"m = {m:.1f}  (SE={se_m:.1f}, t={t_m:.3f}, p={pv_m:.3f})")
#     print(f"RMSE(dN) = {rmse:.4f}")
#     print(f"N0 = {fit_info['N0']}")

#     df["pred_new"] = fit_info["dN_pred"]
#     df["pred_cum"] = fit_info["N_pred"]

#     # save csv
#     pd.DataFrame([{
#         "param": "p", "estimate": p, "se": se_p, "t": t_p, "p_value": pv_p
#     }, {
#         "param": "q", "estimate": q, "se": se_q, "t": t_q, "p_value": pv_q
#     }, {
#         "param": "m", "estimate": m, "se": se_m, "t": t_m, "p_value": pv_m
#     }, {
#         "param": "RMSE_dN", "estimate": rmse
#     }]).to_csv(OUTPUT_CSV, index=False)

#     # plots
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="Actual cumulative")
#     plt.plot(df[DATE_COL], df["pred_cum"], "--", label="Predicted")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="Actual ΔN")
#     plt.plot(df[DATE_COL], df["pred_new"], "--", label="Pred ΔN")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()


# ===========
# index版离散Bass模型
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import scipy.stats as stats
import matplotlib.pyplot as plt
import os
from datetime import datetime

# ============= Parameters (EDIT HERE) =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_weekly_timeline_event_all.csv"

INDEX_COL = "index"         # <--- CSV 的 index 列名（你可以改）
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"

# 你设置 index 选择区间（例如 weekly）
# BTC weekly: 253-357; ETH weekly: 159-263
# BTC monthly: 59-83; ETH monthly:38-62
# BTC quarterly: 21-29; ETH quarterly:14-22
START_IDX = 59               # <--- 人工输入开始 index
END_IDX   = 83               # <--- 人工输入结束 index

OUTPUT_PNG_NEW = "btc_bass_new_dev_discrete_weekly.png"
OUTPUT_PNG_CUM = "btc_bass_cum_dev_discrete_weekly.png"
OUTPUT_CSV     = "btc_bass_results_discrete_weekly.csv"
# ===================================================


# --------- Load Data ----------
def load_data():
    df = pd.read_csv(CSV_PATH)
    df = df[[INDEX_COL, NEW_COL, CUM_COL]]
    df = df.sort_values(INDEX_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df


def select_index(df, start_idx, end_idx):
    mask = (df[INDEX_COL] >= start_idx) & (df[INDEX_COL] <= end_idx)
    return df.loc[mask].copy().reset_index(drop=True)


# --------- Discrete Bass Model ----------
def bass_discrete_new(t, p, q, m, N0):
    T = len(t)
    N = np.zeros(T)
    dN = np.zeros(T)
    N[0] = N0

    for i in range(1, T):
        dN[i] = (p + q * (N[i-1] / m)) * (m - N[i-1])
        N[i] = N[i-1] + dN[i]

    return dN


def simulate_bass_discrete(p, q, m, N0, T):
    N = np.zeros(T)
    dN = np.zeros(T)
    N[0] = N0

    for i in range(1, T):
        dN[i] = (p + q * (N[i-1] / m)) * (m - N[i-1])
        N[i] = N[i-1] + dN[i]
    return N, dN


# --------- Model Fitting ----------
def fit_bass_discrete(df):
    y_true_dN = df[NEW_COL].values
    y_true_cum = df[CUM_COL].values
    N0 = y_true_cum[0]

    t = np.arange(len(df))

    # initial guess
    m_guess = y_true_cum[-1] * 1.2
    p0 = [0.01, 0.3, m_guess]

    bounds_lower = [1e-6, 0, y_true_cum[-1] * 0.5]
    bounds_upper = [0.99, 1.0, y_true_cum[-1] * 20.0]

    def model(t, p, q, m):
        return bass_discrete_new(t, p, q, m, N0)

    popt, pcov = curve_fit(
        model, t, y_true_dN,
        p0=p0, bounds=(bounds_lower, bounds_upper),
        maxfev=10000
    )

    p, q, m = popt
    N_pred, dN_pred = simulate_bass_discrete(p, q, m, N0, len(df))

    rmse_dN = np.sqrt(np.mean((y_true_dN - dN_pred) ** 2))

    # statistics
    se = np.sqrt(np.diag(pcov))
    residuals = y_true_dN - dN_pred
    n = len(df)
    k = 3

    sigma2 = np.sum(residuals ** 2) / (n - k)
    tvals = popt / se
    pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), df=n - k))

    return popt, {
        "se": se,
        "tvals": tvals,
        "pvals": pvals,
        "rmse_dN": rmse_dN,
        "N_pred": N_pred,
        "dN_pred": dN_pred,
        "N0": N0
    }


# --------- Main ----------
def main():
    df = load_data()
    df = select_index(df, START_IDX, END_IDX)

    print("\n=== Fitting Discrete Bass Model based on INDEX range ===")
    print(f"Selected index: {START_IDX} → {END_IDX}")
    print(f"Total observations: {len(df)}")

    popt, fit_info = fit_bass_discrete(df)

    p, q, m = popt
    rmse = fit_info["rmse_dN"]

    se_p, se_q, se_m = fit_info["se"]
    t_p, t_q, t_m = fit_info["tvals"]
    p_pval, p_qval, p_mval = fit_info["pvals"]

    print(f"\n=== Parameter Estimates ===")
    print(f"p = {p:.6f}  (SE={se_p:.6f}, t={t_p:.3f}, p={p_pval:.3f})")
    print(f"q = {q:.6f}  (SE={se_q:.6f}, t={t_q:.3f}, p={p_qval:.3f})")
    print(f"m = {m:.2f}  (SE={se_m:.2f}, t={t_m:.3f}, p={p_mval:.3f})")
    print(f"RMSE (ΔN) = {rmse:.4f}")
    print(f"N0 = {fit_info['N0']}")

    df["pred_new"] = fit_info["dN_pred"]
    df["pred_cum"] = fit_info["N_pred"]

    # Save results
    pd.DataFrame([
        {"param": "p", "estimate": p, "se": se_p, "t": t_p, "p_value": p_pval},
        {"param": "q", "estimate": q, "se": se_q, "t": t_q, "p_value": p_qval},
        {"param": "m", "estimate": m, "se": se_m, "t": t_m, "p_value": p_mval},
        {"param": "RMSE_dN", "estimate": rmse}
    ]).to_csv(OUTPUT_CSV, index=False)

    # --------- Plots ---------
    plt.figure(figsize=(12, 6))
    plt.plot(df[INDEX_COL], df[CUM_COL], label="Actual cumulative N(t)")
    plt.plot(df[INDEX_COL], df["pred_cum"], "--", label="Predicted Bass N(t)")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(df[INDEX_COL], df[NEW_COL], label="Actual ΔN")
    plt.plot(df[INDEX_COL], df["pred_new"], "--", label="Predicted Bass ΔN")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
