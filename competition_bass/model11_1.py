# 考虑q(t),price(t)
# bass model拟合应该用N(t-1)
# BTC
# PRICE_LAG_COLS = [
#     "btc_price_lag1","ln_btc_price_lag1","btc_return_1d",
#     "btc_return_7d","btc_vol_7d","btc_ma_7d","btc_trend_7d",
#     "btc_return_14d","btc_vol_14d","btc_ma_14d","btc_trend_14d",
#     "btc_return_21d","btc_vol_21d","btc_ma_21d","btc_trend_21d",
#     "btc_return_30d","btc_vol_30d","btc_ma_30d","btc_trend_30d"
# ]

# EVENT_LAG_COLS = [
#     "btc_event_lag1","btc_event_sum_7","btc_event_mean_7","btc_event_vol_7",
#     "btc_event_sum_14","btc_event_mean_14","btc_event_vol_14",
#     "btc_event_sum_21","btc_event_mean_21","btc_event_vol_21",
#     "btc_event_sum_30","btc_event_mean_30","btc_event_vol_30",
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_event_sum_14","btc_p_event_mean_14","btc_p_event_vol_14",
#     "btc_p_event_sum_21","btc_p_event_mean_21","btc_p_event_vol_21",
#     "btc_p_event_sum_30","btc_p_event_mean_30","btc_p_event_vol_30",
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7","btc_q_event_vol_7",
#     "btc_q_event_sum_14","btc_q_event_mean_14","btc_q_event_vol_14",
#     "btc_q_event_sum_21","btc_q_event_mean_21","btc_q_event_vol_21",
#     "btc_q_event_sum_30","btc_q_event_mean_30","btc_q_event_vol_30",
#     "bip_event_lag1","bip_event_sum_7","bip_event_mean_7","bip_event_vol_7",
#         "bip_event_sum_14","bip_event_mean_14","bip_event_vol_14",
#         "bip_event_sum_21","bip_event_mean_21","bip_event_vol_21",
#         "bip_event_sum_30","bip_event_mean_30","bip_event_vol_30",
#         "bip_p_event_lag1","bip_p_event_sum_7","bip_p_event_mean_7","bip_p_event_vol_7",
#         "bip_p_event_sum_14","bip_p_event_mean_14","bip_p_event_vol_14",
#         "bip_p_event_sum_21","bip_p_event_mean_21","bip_p_event_vol_21",
#         "bip_p_event_sum_30","bip_p_event_mean_30","bip_p_event_vol_30",
#         "bip_q_event_lag1","bip_q_event_sum_7","bip_q_event_mean_7","bip_q_event_vol_7",
#         "bip_q_event_sum_14","bip_q_event_mean_14","bip_q_event_vol_14",
#         "bip_q_event_sum_21","bip_q_event_mean_21","bip_q_event_vol_21",
#         "bip_q_event_sum_30","bip_q_event_mean_30","bip_q_event_vol_30",
#         "btc_bip_event_lag1","btc_bip_event_sum_7","btc_bip_event_mean_7","btc_bip_event_vol_7",
#         "btc_bip_event_sum_14","btc_bip_event_mean_14","btc_bip_event_vol_14",
#         "btc_bip_event_sum_21","btc_bip_event_mean_21","btc_bip_event_vol_21",
#         "btc_bip_event_sum_30","btc_bip_event_mean_30","btc_bip_event_vol_30",
#         "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#         "btc_p_bip_p_event_sum_14","btc_p_bip_p_event_mean_14","btc_p_bip_p_event_vol_14",
#         "btc_p_bip_p_event_sum_21","btc_p_bip_p_event_mean_21","btc_p_bip_p_event_vol_21",
#         "btc_p_bip_p_event_sum_30","btc_p_bip_p_event_mean_30","btc_p_bip_p_event_vol_30",
#         "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7","btc_q_bip_q_event_vol_7",
#         "btc_q_bip_q_event_sum_14","btc_q_bip_q_event_mean_14","btc_q_bip_q_event_vol_14",
#         "btc_q_bip_q_event_sum_21","btc_q_bip_q_event_mean_21","btc_q_bip_q_event_vol_21",
#         "btc_q_bip_q_event_sum_30","btc_q_bip_q_event_mean_30","btc_q_bip_q_event_vol_30",
#         "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7",
#         "btc_p_bip_event_sum_14","btc_p_bip_event_mean_14","btc_p_bip_event_vol_14",
#         "btc_p_bip_event_sum_21","btc_p_bip_event_mean_21","btc_p_bip_event_vol_21",
#         "btc_p_bip_event_sum_30","btc_p_bip_event_mean_30","btc_p_bip_event_vol_30",
#         "btc_bip_p_event_lag1","btc_bip_p_event_sum_7","btc_bip_p_event_mean_7","btc_bip_p_event_vol_7",
#         "btc_bip_p_event_sum_14","btc_bip_p_event_mean_14","btc_bip_p_event_vol_14",
#         "btc_bip_p_event_sum_21","btc_bip_p_event_mean_21","btc_bip_p_event_vol_21",
#         "btc_bip_p_event_sum_30","btc_bip_p_event_mean_30","btc_bip_p_event_vol_30",
#         "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7","btc_q_bip_event_vol_7",
#         "btc_q_bip_event_sum_14","btc_q_bip_event_mean_14","btc_q_bip_event_vol_14",
#         "btc_q_bip_event_sum_21","btc_q_bip_event_mean_21","btc_q_bip_event_vol_21",
#         "btc_q_bip_event_sum_30","btc_q_bip_event_mean_30","btc_q_bip_event_vol_30",
#         "btc_bip_q_event_lag1","btc_bip_q_event_sum_7","btc_bip_q_event_mean_7","btc_bip_q_event_vol_7",
#         "btc_bip_q_event_sum_14","btc_bip_q_event_mean_14","btc_bip_q_event_vol_14",
#         "btc_bip_q_event_sum_21","btc_bip_q_event_mean_21","btc_bip_q_event_vol_21",
#         "btc_bip_q_event_sum_30","btc_bip_q_event_mean_30","btc_bip_q_event_vol_30"
# ]

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt
import itertools
import math

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"


EVENT_LAG_COLS = [
    "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
    "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
    # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
]

# ============= 价格滞后变量 =============
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]
# # 你给的滞后价格列（示例 - 请根据实际 CSV 中列名调整）
# PRICE_LAG_COLS = [
#     "btc_price_lag1","ln_btc_price_lag1","btc_return_1d",
#     "btc_return_7d","btc_vol_7d","btc_ma_7d","btc_trend_7d",
#     "btc_return_14d","btc_vol_14d","btc_ma_14d","btc_trend_14d",
#     "btc_return_21d","btc_vol_21d","btc_ma_21d","btc_trend_21d",
#     "btc_return_30d","btc_vol_30d","btc_ma_30d","btc_trend_30d"
# ]

# # 你给的滞后事件列（示例 - 请根据实际 CSV 中列名调整）
# EVENT_LAG_COLS = [
#     "btc_event_lag1","btc_event_sum_7","btc_event_mean_7","btc_event_vol_7",
#     "btc_event_sum_14","btc_event_mean_14","btc_event_vol_14",
#     "btc_event_sum_21","btc_event_mean_21","btc_event_vol_21",
#     "btc_event_sum_30","btc_event_mean_30","btc_event_vol_30",
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_event_sum_14","btc_p_event_mean_14","btc_p_event_vol_14",
#     "btc_p_event_sum_21","btc_p_event_mean_21","btc_p_event_vol_21",
#     "btc_p_event_sum_30","btc_p_event_mean_30","btc_p_event_vol_30",
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7","btc_q_event_vol_7",
#     "btc_q_event_sum_14","btc_q_event_mean_14","btc_q_event_vol_14",
#     "btc_q_event_sum_21","btc_q_event_mean_21","btc_q_event_vol_21",
#     "btc_q_event_sum_30","btc_q_event_mean_30","btc_q_event_vol_30",
#     "bip_event_lag1","bip_event_sum_7","bip_event_mean_7","bip_event_vol_7",
#         "bip_event_sum_14","bip_event_mean_14","bip_event_vol_14",
#         "bip_event_sum_21","bip_event_mean_21","bip_event_vol_21",
#         "bip_event_sum_30","bip_event_mean_30","bip_event_vol_30",
#         "bip_p_event_lag1","bip_p_event_sum_7","bip_p_event_mean_7","bip_p_event_vol_7",
#         "bip_p_event_sum_14","bip_p_event_mean_14","bip_p_event_vol_14",
#         "bip_p_event_sum_21","bip_p_event_mean_21","bip_p_event_vol_21",
#         "bip_p_event_sum_30","bip_p_event_mean_30","bip_p_event_vol_30",
#         "bip_q_event_lag1","bip_q_event_sum_7","bip_q_event_mean_7","bip_q_event_vol_7",
#         "bip_q_event_sum_14","bip_q_event_mean_14","bip_q_event_vol_14",
#         "bip_q_event_sum_21","bip_q_event_mean_21","bip_q_event_vol_21",
#         "bip_q_event_sum_30","bip_q_event_mean_30","bip_q_event_vol_30",
#         "btc_bip_event_lag1","btc_bip_event_sum_7","btc_bip_event_mean_7","btc_bip_event_vol_7",
#         "btc_bip_event_sum_14","btc_bip_event_mean_14","btc_bip_event_vol_14",
#         "btc_bip_event_sum_21","btc_bip_event_mean_21","btc_bip_event_vol_21",
#         "btc_bip_event_sum_30","btc_bip_event_mean_30","btc_bip_event_vol_30",
#         "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#         "btc_p_bip_p_event_sum_14","btc_p_bip_p_event_mean_14","btc_p_bip_p_event_vol_14",
#         "btc_p_bip_p_event_sum_21","btc_p_bip_p_event_mean_21","btc_p_bip_p_event_vol_21",
#         "btc_p_bip_p_event_sum_30","btc_p_bip_p_event_mean_30","btc_p_bip_p_event_vol_30",
#         "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7","btc_q_bip_q_event_vol_7",
#         "btc_q_bip_q_event_sum_14","btc_q_bip_q_event_mean_14","btc_q_bip_q_event_vol_14",
#         "btc_q_bip_q_event_sum_21","btc_q_bip_q_event_mean_21","btc_q_bip_q_event_vol_21",
#         "btc_q_bip_q_event_sum_30","btc_q_bip_q_event_mean_30","btc_q_bip_q_event_vol_30",
#         "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7",
#         "btc_p_bip_event_sum_14","btc_p_bip_event_mean_14","btc_p_bip_event_vol_14",
#         "btc_p_bip_event_sum_21","btc_p_bip_event_mean_21","btc_p_bip_event_vol_21",
#         "btc_p_bip_event_sum_30","btc_p_bip_event_mean_30","btc_p_bip_event_vol_30",
#         "btc_bip_p_event_lag1","btc_bip_p_event_sum_7","btc_bip_p_event_mean_7","btc_bip_p_event_vol_7",
#         "btc_bip_p_event_sum_14","btc_bip_p_event_mean_14","btc_bip_p_event_vol_14",
#         "btc_bip_p_event_sum_21","btc_bip_p_event_mean_21","btc_bip_p_event_vol_21",
#         "btc_bip_p_event_sum_30","btc_bip_p_event_mean_30","btc_bip_p_event_vol_30",
#         "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7","btc_q_bip_event_vol_7",
#         "btc_q_bip_event_sum_14","btc_q_bip_event_mean_14","btc_q_bip_event_vol_14",
#         "btc_q_bip_event_sum_21","btc_q_bip_event_mean_21","btc_q_bip_event_vol_21",
#         "btc_q_bip_event_sum_30","btc_q_bip_event_mean_30","btc_q_bip_event_vol_30",
#         "btc_bip_q_event_lag1","btc_bip_q_event_sum_7","btc_bip_q_event_mean_7","btc_bip_q_event_vol_7",
#         "btc_bip_q_event_sum_14","btc_bip_q_event_mean_14","btc_bip_q_event_vol_14",
#         "btc_bip_q_event_sum_21","btc_bip_q_event_mean_21","btc_bip_q_event_vol_21",
#         "btc_bip_q_event_sum_30","btc_bip_q_event_mean_30","btc_bip_q_event_vol_30"
# ]

START_DATE = "2020-10-01"
END_DATE = "2021-10-01"

OUTPUT_PNG_NEW = "btc_bass_pqfit_new_dev.png"
OUTPUT_PNG_CUM = "btc_bass_pqfit_cum_dev.png"
OUTPUT_CSV = "btc_bass_pqfit_results_all20202021.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    # 全表先做一次前向填充与 0 填充，保证每个滞后列在选择时存在值
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

def normalize(x):
    x = np.array(x, dtype=float)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


# --------- price 变换函数（注意已移除 pct，新增 exp） ----------
def price_identity(price_arr):
    return normalize(price_arr)

def price_log(price_arr):
    return normalize(np.log(np.maximum(price_arr, 1e-8)))

def price_exp(price_arr):
    # 为避免 np.exp 溢出，先 clip 到合理范围
    clipped = np.clip(price_arr, -50, 50)
    return normalize(np.exp(clipped))

PRICE_FUNCS = {
    "linear_price": price_identity,
    "log_price": price_log,
    "exp_price": price_exp
}


# --------- q(t) 计算（基于给定的滞后事件列） ----------
def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * ev)
    else:
        raise ValueError("未知 q_form")
    return q_t


# --------- Bass 增量（使用 N_lag） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m):
    remaining = np.maximum(m - N_lag, 0)
    return (p_t_arr + q_t_arr * (N_lag / m)) * remaining


# --------- 拟合与显著性工具（针对单个 price_col & q_col） ----------
def compute_prediction_for_pair(df, params, price_func, q_form):
    """
    params: [p0, alpha, q0, beta, m]
    df must have columns: 'price_input' and 'q_input' and 'N_lag'
    """
    p0, alpha, q0, beta, m = params
    price_vals = df["price_input"].values
    q_vals = df["q_input"].values

    p_t = np.maximum(p0 + alpha * price_func(price_vals), 0)
    q_t = compute_q_t_from_array(q_vals, (q0, beta), q_form)
    N_lag = df["N_lag"].values
    dN_pred = dN_pred_from_Nlag(N_lag, p_t, q_t, m)
    return dN_pred, p_t, q_t

def residuals_for_pair(params, df, price_func, q_form):
    p0, alpha, q0, beta, m = params
    # 基本参数约束
    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _, _ = compute_prediction_for_pair(df, params, price_func, q_form)
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_predicted

def fit_bass_pair(df, price_func, q_form):
    """
    Fit params [p0, alpha, q0, beta, m] for the df (which already contains
    columns price_input, q_input, N_lag). Returns res or None if fail.
    """
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        init = [0.0001, 0.01, 0.01, 0.01, m_guess]
        bounds = ([0, -10, 0, -10, 0.9*m_guess], [1, 10, 1, 10, 20*m_guess])

        res = least_squares(residuals_for_pair, init, bounds=bounds, args=(df, price_func, q_form), method="trf")
        if not res.success:
            return None

        params = res.x
        eps = 1e-6
        n = len(df)
        k = len(params)
        y_pred, _, _ = compute_prediction_for_pair(df, params, price_func, q_form)

        # 数值雅可比
        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_for_pair(df, p_eps, price_func, q_form)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        # 条件数
        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        residuals_vec = df[NEW_COL].values - y_pred
        sigma2 = np.sum(residuals_vec**2) / (n - k)
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se = np.sqrt(np.diag(cov))
        except np.linalg.LinAlgError:
            se = np.full(k, np.nan)

        tvals = params / se
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
    except Exception as e:
        print(f"⚠️ 拟合异常: {e}")
        return None


# --------- 主程序：遍历 price_lag × event_lag × price_func × q_form ----------
def main():
    df_all = load_data()
    df_all = select_date(df_all, START_DATE, END_DATE)

    results = []
    valid_models = []

    # 画真实新增为底图
    plt.figure(figsize=(12, 6))
    plt.plot(df_all[DATE_COL], df_all[NEW_COL], color="black", label="真实新增", linewidth=2)

    # 遍历所有 price lag × event lag 组合（每次只用 1 个 price lag + 1 个 event lag）
    for price_col, event_col in itertools.product(PRICE_LAG_COLS, EVENT_LAG_COLS):
        # 要求这些列在 df_all 中存在
        if price_col not in df_all.columns or event_col not in df_all.columns:
            print(f"⚠️ 列缺失，跳过组合：price={price_col}, event={event_col}")
            continue

        print(f"\n=== 拟合组合: price={price_col}, event={event_col} ===")

        # 选取并准备子 DataFrame（保留原来的时间窗口）
        df = df_all[[DATE_COL, NEW_COL, CUM_COL, price_col, event_col]].copy()
        # price_input / q_input
        df["price_input"] = df[price_col].values
        df["q_input"] = df[event_col].values

        # 使用 N(t-1)（第一行用初始累积做填充）
        df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values

        # 标准化或其他前处理在 price_func 中已考虑（price_func 接收原始 price_input 数组）
        for pf_name, pf_func in PRICE_FUNCS.items():
            for q_form in ["linear", "log", "exp"]:
                model_name = f"{price_col} | {event_col} | {pf_name} + q_{q_form}"
                print(f"-- 模型: {model_name}")

                res = fit_bass_pair(df, pf_func, q_form)
                if res is None:
                    print(f"⚠️ 拟合失败，跳过：{model_name}")
                    continue

                p0, alpha, q0, beta, m = res.x
                dN_pred, p_t, q_t = compute_prediction_for_pair(df, res.x, pf_func, q_form)
                cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
                rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                sse = np.sum((df[NEW_COL].values - dN_pred)**2)

                print(f"✅ 成功: p0={p0:.6f}, alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.2f}, RMSE={rmse:.3f}")

                # 保存结果行
                row = {
                    "price_col": price_col,
                    "event_col": event_col,
                    "price_func": pf_name,
                    "q_form": q_form,
                    "p0": p0, "alpha": alpha, "q0": q0, "beta": beta, "m": m,
                    "SSE": sse, "RMSE": rmse,
                    "cond": getattr(res, "cond", np.nan)
                }
                # 添加入每个参数的 se/t/p
                for i, name in enumerate(["p0", "alpha", "q0", "beta", "m"]):
                    row[f"param_{i}"] = res.x[i]
                    row[f"se_{i}"] = float(res.se[i]) if hasattr(res, "se") else np.nan
                    row[f"t_{i}"] = float(res.tvals[i]) if hasattr(res, "tvals") else np.nan
                    row[f"p_{i}"] = float(res.pvals[i]) if hasattr(res, "pvals") else np.nan

                results.append(row)

                # 保存预测到 df_all（列名带组合识别）
                safe_name = f"pred_new_{price_col}__{event_col}__{pf_name}__{q_form}"
                safe_cum = f"pred_cum_{price_col}__{event_col}__{pf_name}__{q_form}"
                df_all[safe_name] = np.nan
                df_all[safe_cum] = np.nan
                # 对齐索引并写入
                df_all.loc[df.index, safe_name] = dN_pred
                df_all.loc[df.index, safe_cum] = cum_pred
                valid_models.append(safe_name)

                # 在新增图上画一条（可能很多条，可以在必要时注释掉）
                plt.plot(df[DATE_COL], dN_pred, "--", alpha=0.6, linewidth=0.8, label=model_name)

    # 保存结果表
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有拟合结果保存至 {OUTPUT_CSV}")

    # 最终绘图设置并保存（新增）
    plt.xlabel("date")
    plt.ylabel("daily new developers")
    plt.title("Bass model fits (dN) — many combos")
    # 为避免图例太长，仅显示真实新增与若干模型（如需要展示全部可移除此条件）
    plt.legend(ncol=2, fontsize="small")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()

    # 绘制累积曲线（选择性绘制所有已保存的累积预测）
    plt.figure(figsize=(12, 6))
    plt.plot(df_all[DATE_COL], df_all[CUM_COL], color="black", label="真实累积", linewidth=2)
    for col in df_all.columns:
        if col.startswith("pred_cum_"):
            plt.plot(df_all[DATE_COL], df_all[col], "--", alpha=0.7, linewidth=0.8)
    plt.xlabel("date"); plt.ylabel("cumulative users")
    plt.title("Bass model fits (N cumulative)")
    plt.legend().set_visible(False)
    plt.grid(True, linestyle="--")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()

# ============
# 下面代码是手动选择 price lag + event lag 的版本
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt
# import math

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"

# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pqfit_new_dev.png"
# OUTPUT_PNG_CUM = "btc_bass_pqfit_cum_dev.png"

# # ---------- 你手动选择的两个变量 ----------
# price_col = "btc_ma_14d"     # <<< 手动输入价格变量
# event_col = "btc_p_event_cum_lag1"     # <<< 手动输入事件变量


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# def normalize(x):
#     x = np.array(x, dtype=float)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# # --------- price 变换函数 ----------
# def price_identity(price_arr):
#     return normalize(price_arr)

# def price_log(price_arr):
#     return normalize(np.log(np.maximum(price_arr, 1e-8)))

# def price_exp(price_arr):
#     clipped = np.clip(price_arr, -50, 50)
#     return normalize(np.exp(clipped))

# PRICE_FUNCS = {
#     "linear_price": price_identity,
#     "log_price": price_log,
#     "exp_price": price_exp
# }

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
#     q0, beta = q_params
#     ev = normalize(event_arr)

#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")

#     return q_t

# # --------- Bass 增量 ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m):
#     remaining = np.maximum(m - N_lag, 0)
#     return (p_t_arr + q_t_arr * (N_lag / m)) * remaining

# # --------- 基于单 price + single event 的预测 ----------
# def compute_prediction_for_pair(df, params, price_func, q_form):
#     p0, alpha, q0, beta, m = params
#     price_vals = df["price_input"].values
#     q_vals = df["q_input"].values

#     p_t = np.maximum(p0 + alpha * price_func(price_vals), 0)
#     q_t = compute_q_t_from_array(q_vals, (q0, beta), q_form)
#     N_lag = df["N_lag"].values

#     dN_pred = dN_pred_from_Nlag(N_lag, p_t, q_t, m)
#     return dN_pred, p_t, q_t

# def residuals_for_pair(params, df, price_func, q_form):
#     p0, alpha, q0, beta, m = params

#     if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6

#     dN_predicted, _, _ = compute_prediction_for_pair(df, params, price_func, q_form)

#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6

#     return df[NEW_COL].values - dN_predicted

# def fit_bass_pair(df, price_func, q_form):
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
#         init = [0.0001, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, 0, -10, 0.9*m_guess],
#                   [1, 10, 1, 10, 20*m_guess])

#         res = least_squares(
#             residuals_for_pair,
#             init,
#             bounds=bounds,
#             args=(df, price_func, q_form),
#             method="trf"
#         )

#         if not res.success:
#             return None

#         params = res.x
#         eps = 1e-8
#         n = len(df)
#         k = len(params)

#         y_pred, _, _ = compute_prediction_for_pair(df, params, price_func, q_form)

#         # ---- 数值雅可比 ----
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_for_pair(df, p_eps, price_func, q_form)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T

#         # 条件数
#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except:
#             cond = np.nan

#         res.cond = cond

#         # ---- 标准误差 / t / p ----
#         residuals_vec = df[NEW_COL].values - y_pred
#         sigma2 = np.sum(residuals_vec ** 2) / (n - k)

#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except:
#             se = np.full(k, np.nan)

#         tvals = params / se
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

#         res.se, res.tvals, res.pvals = se, tvals, pvals
#         return res

#     except Exception as e:
#         print("⚠️ 拟合异常:", e)
#         return None


# # --------- 主程序（只跑你手动选的 price + event） ----------
# def main():
#     print(f"\n=== 手动选择的组合 ===")
#     print(f"price col = {price_col}")
#     print(f"event col = {event_col}\n")

#     df_all = load_data()
#     df_all = select_date(df_all, START_DATE, END_DATE)

#     # ---- 只构造一个 df ----
#     df = df_all[[DATE_COL, NEW_COL, CUM_COL, price_col, event_col]].copy()
#     df["price_input"] = df[price_col].values
#     df["q_input"] = df[event_col].values
#     df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values

#     # ---- 画真实新增 ----
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], color="black", label="真实新增", linewidth=2)

#     # ---- 遍历三种 price_func × 三种 q(t) 形式 ----
#     for pf_name, pf_func in PRICE_FUNCS.items():
#         for q_form in ["linear", "log", "exp"]:
#             model_name = f"{pf_name} + q_{q_form}"

#             print(f"-- 开始拟合模型：{model_name}")

#             res = fit_bass_pair(df, pf_func, q_form)

#             if res is None:
#                 print("⚠️ 拟合失败\n")
#                 continue

#             p0, alpha, q0, beta, m = res.x
#             dN_pred, _, _ = compute_prediction_for_pair(df, res.x, pf_func, q_form)
#             cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)

#             rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred) ** 2))

#             print(f"  p0={p0:.6f}, alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.2f}, RMSE={rmse:.4f}, cond={res.cond:.1f}")

#             # 画预测曲线
#             plt.plot(df[DATE_COL], dN_pred, "--", linewidth=1, alpha=0.7, label=model_name)

#             # 写入 df_all（可选）
#             df_all[f"pred_new_{pf_name}_{q_form}"] = dN_pred
#             df_all[f"pred_cum_{pf_name}_{q_form}"] = cum_pred

#     plt.legend(fontsize="small")
#     plt.title("Bass model fit")
#     plt.xlabel("date")
#     plt.ylabel("new users")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()

#     # 累积图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df_all[DATE_COL], df_all[CUM_COL], color="black", linewidth=2, label="真实累积")

#     for col in df_all.columns:
#         if col.startswith("pred_cum_"):
#             plt.plot(df_all[DATE_COL], df_all[col], "--", alpha=0.6, linewidth=1)

#     plt.legend().set_visible(False)
#     plt.title("Bass cumulative")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()

