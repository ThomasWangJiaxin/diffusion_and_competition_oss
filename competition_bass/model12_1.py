# 【price+p_event】+q_event

# ======
# 人工输入变量
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"

# # 事件滞后变量
# P_EVENT_COL = "btc_bip_p_event_lag1"
# QEVENT_COL = "btc_q_event_lag1"

# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pqfit_new_dev_allprice.png"
# OUTPUT_PNG_CUM = "eth_bass_pqfit_cum_dev_allprice.png"
# OUTPUT_CSV = "eth_bass_pqfit_results_allprice.csv"
# # ===================================

# # --------- 你要求的所有 price lag 变量 -----------
# PRICE_LAG_COLS = [
#     "btc_price_lag1","ln_btc_price_lag1",
#     "btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])

#     keep_cols = [DATE_COL, NEW_COL, CUM_COL, P_EVENT_COL, QEVENT_COL] + PRICE_LAG_COLS
#     df = df[keep_cols].sort_values(DATE_COL).reset_index(drop=True)

#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     out = df.loc[mask].copy()

#     # === 修复 (1): Bass 应使用 N(t−1) ===
#     out["N_lag"] = out[CUM_COL].shift(1).fillna(out[CUM_COL].iloc[0])
#     return out


# def normalize(x):
#     x = np.array(x, dtype=float)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)


# # --------- q(t) ----------
# def compute_q_t(df, q_params, q_form):
#     q0, beta = q_params
#     event_q = normalize(df[QEVENT_COL].values)

#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * event_q, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event_q, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * event_q)
#     else:
#         raise ValueError("未知 q_form")

#     return q_t


# # --------- p(t)，新增 price_log 模型 ----------
# def compute_p_t(df, params, price_array, p_model):
#     """
#     price_array：已 normalize 过的价格变量
#     event_x：事件变量（normalize）
#     """
#     price_x = price_array
#     event_x = normalize(df[P_EVENT_COL].values)

#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_x + beta * event_x

#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_x + beta * np.log1p(np.maximum(event_x, 0))

#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_x + beta * event_x + gamma * (price_x * event_x)

#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_x + beta * np.log1p(np.maximum(event_x, 0)) + gamma * (price_x * event_x)

#     else:
#         raise ValueError("未知 p(t) 模型类型")

#     return np.maximum(p_t, 0)


# # --------- Bass 模型 ----------
# def dN_pred(N_lag, p_t, q_t, m):
#     """使用 N(t–1) 预测 dN(t)  —— 已修复"""
#     remaining = np.maximum(m - N_lag, 0)
#     return (p_t + q_t * (N_lag / m)) * remaining


# def compute_prediction(df, params, price_array, p_model, q_form):
#     # 拆分 p/q/m 参数
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:3]
#         q0, beta_q, m = params[3:6]
#     else:
#         p_param_count = 4
#         p_params = params[:4]
#         q0, beta_q, m = params[4:7]

#     p_t = compute_p_t(df, p_params, price_array, p_model)
#     q_t = compute_q_t(df, (q0, beta_q), q_form)

#     # 使用 N(t−1)
#     N_lag = df["N_lag"].values

#     return dN_pred(N_lag, p_t, q_t, m), p_t, q_t


# def residuals(params, df, price_array, p_model, q_form):
#     # 参数结构判断
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[5]
#     else:
#         q0 = params[4]
#         m = params[6]

#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6

#     dNp, _, _ = compute_prediction(df, params, price_array, p_model, q_form)
#     if np.any(np.isnan(dNp)):
#         return np.ones(len(df)) * 1e6

#     return df[NEW_COL].values - dNp


# # --------- 拟合 ----------
# def fit_bass(df, price_array, p_model, q_form):
#     m_guess = 1.2 * df[CUM_COL].max()

#     if p_model in ["additive", "nonlinear_event"]:
#         init = [0.001, 0.01, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, 0, -10, 0.9*m_guess],
#                   [1, 10, 10, 1, 10, 20*m_guess])
#         param_names = ["p0", "alpha", "beta", "q0", "beta_q", "m"]
#     else:
#         init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, -10, 0, -10, 0.9*m_guess],
#                   [1, 10, 10, 10, 1, 10, 20*m_guess])
#         param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "m"]

#     res = least_squares(residuals, init, bounds=bounds,
#                         args=(df, price_array, p_model, q_form), method="trf")
#     if not res.success:
#         return None, None, None, param_names

#     params = res.x

#     # -------- t/p calculation (same as before) ----------
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     y_pred, _, _ = compute_prediction(df, params, price_array, p_model, q_form)

#     # 数值雅可比
#     J = []
#     for i in range(k):
#         p_eps = params.copy()
#         p_eps[i] += eps
#         y_eps, _, _ = compute_prediction(df, p_eps, price_array, p_model, q_form)
#         J.append((y_eps - y_pred) / eps)
#     J = np.array(J).T

#     residuals_vec = df[NEW_COL] - y_pred
#     sigma2 = np.sum(residuals_vec**2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#         se = np.sqrt(np.diag(cov))
#     except:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

#     res.se, res.tvals, res.pvals = se, tvals, pvals
#     return res, params, (tvals, pvals), param_names



# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     # p(t) 四模型
#     p_models = ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]

#     # q(t) 三模型
#     q_forms = ["linear", "log", "exp"]

#     results = []
#     valid_models = []

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], color="black", linewidth=2, label="真实新增")

#     # ---------- (3) 遍历所有 price lag 变量 ----------
#     for price_col in PRICE_LAG_COLS:
#         print(f"\n==========================")
#         print(f"⚡ 使用价格变量：{price_col}")
#         print(f"==========================")

#         raw_price = df[price_col].values

#         # 三种价格变换 linear / log / pct
#         price_transforms = {
#             "linear": normalize(raw_price),
#             "log": normalize(np.log(np.maximum(raw_price, 1e-8))),  # 新增 log 变换
#             "pct": normalize(np.concatenate([[0], np.diff(raw_price) / (np.maximum(raw_price[:-1], 1e-8))]))
#         }

#         for pt_name, price_arr in price_transforms.items():
#             for p_model in p_models:
#                 for q_form in q_forms:

#                     model_name = f"{price_col}_{pt_name}_{p_model}_{q_form}"
#                     print(f"\n=== 拟合：{model_name} ===")

#                     res, params, (tvals, pvals), param_names = fit_bass(
#                         df, price_arr, p_model, q_form
#                     )

#                     if res is None:
#                         print("❌ 拟合失败")
#                         continue

#                     dN_pred, _, _ = compute_prediction(
#                         df, params, price_arr, p_model, q_form
#                     )

#                     rmse = np.sqrt(np.mean((df[NEW_COL]-dN_pred)**2))
#                     sse = np.sum((df[NEW_COL]-dN_pred)**2)

#                     print(f"✅ 成功 (RMSE={rmse:.3f})")

#                     # 保存结果
#                     row = {
#                         "model": model_name,
#                         "price_col": price_col,
#                         "price_tf": pt_name,
#                         "p_model": p_model,
#                         "q_form": q_form,
#                         "RMSE": rmse,
#                         "SSE": sse
#                     }
#                     for n, v, tval, pval in zip(param_names, params, tvals, pvals):
#                         row[n] = v
#                         row["t_"+n] = tval
#                         row["p_"+n] = pval
#                     results.append(row)

#                     # 画图
#                     df[f"pred_new_{model_name}"] = dN_pred
#                     df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
#                     valid_models.append(model_name)

#                     plt.plot(df[DATE_COL], dN_pred, "--", alpha=0.5, label=model_name)

#     # 保存 CSV
#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n📁 所有模型结果已写入 {OUTPUT_CSV}")


# if __name__ == "__main__":
#     main()


# =======
# p q自动两两组合

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BTC
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"

# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

START_DATE = "2020-10-01"
END_DATE = "2021-10-01"

OUTPUT_CSV = "btc_bass_pqfit_results_ALL_PQ20202021.csv"
# ===================================

# ============= 显式写入你要求的 P_EVENT_LIST 与 Q_EVENT_LIST =============
P_EVENT_LIST = [
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
    "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
    # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
]
Q_EVENT_LIST = [
    "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
    "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
    # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
]

# ============= 价格滞后变量 =============
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]
# P_EVENT_LIST = [
#     "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_mean_7","eth_p_event_vol_7",
#     "eth_p_eip_p_event_lag1","eth_p_eip_p_event_sum_7","eth_p_eip_p_event_mean_7","eth_p_eip_p_event_vol_7",
#     "eth_p_eip_event_lag1","eth_p_eip_event_sum_7","eth_p_eip_event_mean_7","eth_p_eip_event_vol_7"
# ]

# Q_EVENT_LIST = [
#     "eth_q_event_lag1","eth_q_event_sum_7","eth_q_event_mean_7",
#     "eth_q_eip_q_event_lag1","eth_q_eip_q_event_sum_7","eth_q_eip_q_event_mean_7",
#     "eth_q_eip_event_lag1","eth_q_eip_event_sum_7","eth_q_eip_event_mean_7"
# ]

# # ============= 价格滞后变量集合（你要求的） =============
# PRICE_LAG_COLS = [
#     "eth_price_lag1","eth_ma_7d","eth_ma_14d","eth_ma_21d","eth_ma_30d"
# ]

# ----------------- 工具函数 -----------------
def normalize(x):
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

# --------- q(t) 计算（使用指定的 QEVENT 列） ----------
def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        # q0 * exp(beta * ev)
        q_t = q0 * np.exp(beta * ev)
    else:
        raise ValueError("未知 q_form")
    return q_t

# --------- p(t) 计算（price_array 已由外部转换/normalize） ----------
def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    """
    params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, m]
            for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, m]
    price_array: already-normalized numpy array for price transform
    p_event_col: column name in df for p-event (raw values)
    returns p_t (array)
    """
    # event for p:
    ev = normalize(df[p_event_col].values)

    if p_model == "additive":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * ev

    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))

    elif p_model == "interaction_linear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)

    elif p_model == "interaction_nonlinear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)

    else:
        raise ValueError("未知 p_model")
    return np.maximum(p_t, 0)

# --------- Bass 增量（使用 N_lag） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m):
    remaining = np.maximum(m - N_lag, 0)
    return (p_t_arr + q_t_arr * (N_lag / m)) * remaining

# --------- compute_prediction 针对单个组合（price_array, p_event_col, q_event_col, p_model, q_form） ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
    """
    params layout depends on p_model:
      if p_model in ['additive','nonlinear_event']:
         params = [p0, alpha, beta, q0, beta_q, m]
      else:
         params = [p0, alpha, beta, gamma, q0, beta_q, m]
    """
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q, m = params[p_param_count:p_param_count+3]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q, m = params[p_param_count:p_param_count+3]

    # p_t from price_array and p-event column
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    # q_t from q-event column
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    # N_lag
    N_lag = df["N_lag"].values
    dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m)
    return dN, p_t, q_t

# --------- residuals for least_squares ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
    # basic checks for param plausibility
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[5]
    else:
        q0 = params[4]
        m = params[6]

    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6

    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_predicted

# --------- fit for one pair ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form):
    """
    Fit params for given df (which must have N_lag and event cols).
    Returns res or None on failure.
    """
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        if p_model in ["additive", "nonlinear_event"]:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, 0, -10, 0.9*m_guess],
                      [1, 10, 10, 1, 10, 20*m_guess])
        else:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 20*m_guess])

        res = least_squares(residuals_pair, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form), method="trf")
        if not res.success:
            return None

        params = res.x
        # compute numeric jacobian for se/t/p
        eps = 1e-6
        n = len(df)
        k = len(params)
        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)

        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        resid_vec = df[NEW_COL].values - y_pred
        sigma2 = np.sum(resid_vec**2) / (n - k)
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
        # 捕获拟合异常并返回 None（上层会跳过）
        # 可以在这里打印或记录异常以便调试
        # print("Fit error:", e)
        return None

# ----------------- 主程序 -----------------
def main():
    # 读取全表一次，后续切片
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)

    # ensure date ordering
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    results = []
    combos_done = 0
    combos_skipped = 0

    total_price_cols = [c for c in PRICE_LAG_COLS]
    total_p_events = [c for c in P_EVENT_LIST]
    total_q_events = [c for c in Q_EVENT_LIST]

    # iterate all P x Q combos
    for p_event_col in total_p_events:
        for q_event_col in total_q_events:

            # check the required columns exist for combinations
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
                combos_skipped += 1
                continue

            # select date window
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue

            # add N_lag = N(t-1) (first row fill with initial cum)
            df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values

            # iterate price cols and transforms
            for price_col in total_price_cols:
                raw_price = df[price_col].values.astype(float)

                # three transforms: linear, log, exp (normalized)
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    # if transform fails, skip this price_col
                    print(f"⚠️ price transform error for {price_col}, skipping.")
                    continue

                for pt_name, price_arr in price_transforms.items():
                    # loop p_model and q_form
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
                            print(f"\n→ 拟合: {model_tag}")

                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form)
                            if res is None:
                                print("  ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue

                            combos_done += 1
                            params = res.x
                            # compute prediction to get RMSE/SSE
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)

                            # param names depending on p_model
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "m"]

                            row = {
                                "P_event": p_event_col,
                                "Q_event": q_event_col,
                                "price_col": price_col,
                                "price_tf": pt_name,
                                "p_model": p_model,
                                "q_form": q_form,
                                "RMSE": rmse,
                                "SSE": sse,
                                "cond": float(getattr(res, "cond", np.nan))
                            }

                            for i, name in enumerate(param_names):
                                row[name] = float(params[i]) if i < len(params) else np.nan
                                row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
                                row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
                                row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan

                            results.append(row)

    # write results to csv
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()
