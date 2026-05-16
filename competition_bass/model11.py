# 考虑q(t),price(t)

# p(t),q(t)均标准化

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
PRICE_COL = "eth_price"
QEVENT_COL = "eth_eip_q_event"

START_DATE = "2016-03-10"
END_DATE = "2024-12-31"

OUTPUT_PNG_NEW = "btc_bass_pqfit_new_dev.png"
OUTPUT_PNG_CUM = "btc_bass_pqfit_cum_dev.png"
OUTPUT_CSV = "btc_bass_pqfit_results_all.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)

# --------- p(t) 函数 ----------
def price_identity(price):
    return normalize(price)

def price_log(price):
    return normalize(np.log(np.maximum(price, 1e-8)))

def price_pct(price):
    lag = np.roll(price, 1)
    lag[0] = price[0]
    pct = (price - lag) / np.where(lag == 0, 1, lag)
    return normalize(pct)

PRICE_FUNCS = {
    "linear_price": price_identity,
    "log_price": price_log,
    "pct_price": price_pct
}

# --------- q(t) 函数 ----------
def compute_q_t(df, q_params, q_form):
    q0, beta = q_params
    event = normalize(df[QEVENT_COL].values)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * event, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * event)
    else:
        raise ValueError("未知 q_form")
    return q_t

# --------- Bass 模型 ----------
def dN_pred(N, p_t, q_t, m):
    remaining = np.maximum(m - N, 0)
    return (p_t + q_t * (N / m)) * remaining

def compute_prediction(df, params, price_func, q_form):
    p0, alpha, q0, beta, m = params
    p_t = np.maximum(p0 + alpha * price_func(df[PRICE_COL].values), 0)
    q_t = compute_q_t(df, (q0, beta), q_form)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q_t, m), p_t, q_t

def residuals(params, df, price_func, q_form):
    p0, alpha, q0, beta, m = params
    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _, _ = compute_prediction(df, params, price_func, q_form)
    dN_true = df[NEW_COL].values
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return dN_true - dN_predicted

# --------- 拟合函数 + 显著性 t/p 值 ----------
def fit_bass(df, price_func, q_form):
    m_guess = 1.2 * df[CUM_COL].max()
    init = [0.0001, 0.01, 0.01, 0.01, m_guess]  # p0, alpha, q0, beta, m
    bounds = ([0, -10, 0, -10, 0.9*m_guess], [1, 10, 1, 10, 20*m_guess])

    res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, q_form), method="trf")
    if not res.success:
        return res

    params = res.x
    eps = 1e-6
    n = len(df)
    k = len(params)
    y_pred, _, _ = compute_prediction(df, params, price_func, q_form)

    # 数值雅可比
    J = []
    for i in range(k):
        p_eps = params.copy()
        p_eps[i] += eps
        y_pred_eps, _, _ = compute_prediction(df, p_eps, price_func, q_form)
        J.append((y_pred_eps - y_pred) / eps)
    J = np.array(J).T

    # 条件数
    try:
        cond = np.linalg.cond(J.T @ J)
    except np.linalg.LinAlgError:
        cond = np.nan

    # 显著性 t/p 值
    residuals_vec = df[NEW_COL].values - y_pred
    sigma2 = np.sum(residuals_vec**2)/(n - k)
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12*np.eye(k))
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)
    tvals = params / se
    pvals = 2*(1 - t.cdf(np.abs(tvals), df=n-k))

    res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
    return res

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    results = []
    valid_models = []

    plt.figure(figsize=(12,6))
    plt.plot(df[DATE_COL], df[NEW_COL], color='black', label="真实新增", linewidth=2)

    for pf_name, pf_func in PRICE_FUNCS.items():
        for q_form in ["linear", "log", "exp"]:
            model_name = f"{pf_name} + {q_form}_q"
            print(f"\n=== 拟合模型: {model_name} ===")
            res = fit_bass(df, pf_func, q_form)
            if (not res.success) or np.any(np.isnan(res.x)):
                print(f"⚠️ {model_name} 拟合失败")
                continue

            p0, alpha, q0, beta, m = res.x
            dN_pred, p_t, q_t = compute_prediction(df, res.x, pf_func, q_form)
            rmse = np.sqrt(np.mean((df[NEW_COL]-dN_pred)**2))
            sse = np.sum((df[NEW_COL]-dN_pred)**2)

            print(f"✅ {model_name} 拟合成功: p0={p0:.6f}, alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")
            print("--- 参数显著性 t/p 值 ---")
            for name, val, tval, pval in zip(["p0","alpha","q0","beta","m"], res.x, res.tvals, res.pvals):
                print(f"{name:5s}: val={val:.6f}, t={tval:.3f}, p={pval:.6e}")

            results.append({
                "model": model_name,
                "p0": p0, "alpha": alpha,
                "q0": q0, "beta": beta, "m": m,
                "SSE": sse, "RMSE": rmse,
                "t_p0": res.tvals[0], "p_p0": res.pvals[0],
                "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
                "t_q0": res.tvals[2], "p_q0": res.pvals[2],
                "t_beta": res.tvals[3], "p_beta": res.pvals[3],
                "t_m": res.tvals[4], "p_m": res.pvals[4],
            })

            df[f"pred_new_{model_name}"] = dN_pred
            df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
            valid_models.append(model_name)

            plt.plot(df[DATE_COL], dN_pred, '--', label=model_name)

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

    # 新增图
    plt.xlabel("日期")
    plt.ylabel("新增开发者数 dN/dt")
    plt.title("Bass 模型 p(t) 与 q(t) 组合拟合对比")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()

    # 累积曲线图
    plt.figure(figsize=(12,6))
    plt.plot(df[DATE_COL], df[CUM_COL], color='black', label="真实累积", linewidth=2)
    for model_name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{model_name}"], '--', label=model_name)
    plt.xlabel("日期")
    plt.ylabel("累积开发者数 N(t)")
    plt.title("Bass 模型 p(t) 与 q(t) 组合累积曲线对比")
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()
    
# 没有p0，但都标准化
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "btc_price"
# QEVENT_COL = "bip_q_event"

# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pqfit_new_dev_nop0.png"
# OUTPUT_PNG_CUM = "eth_bass_pqfit_cum_dev_nop0.png"
# OUTPUT_CSV = "eth_bass_pqfit_results_nop0.csv"
# # ===================================

# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# # --------- p(t) 函数 ----------
# def price_identity(price):
#     return normalize(price)

# def price_log(price):
#     return normalize(np.log(np.maximum(price, 1e-8)))

# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return normalize(pct)

# PRICE_FUNCS = {
#     "linear_price": price_identity,
#     "log_price": price_log,
#     "pct_price": price_pct
# }

# # --------- q(t) 函数 ----------
# def compute_q_t(df, q_params, q_form):
#     q0, beta = q_params
#     event = normalize(df[QEVENT_COL].values)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * event, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * event)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# # --------- Bass 模型 ----------
# def dN_pred(N, p_t, q_t, m):
#     remaining = np.maximum(m - N, 0)
#     return (p_t + q_t * (N / m)) * remaining

# def compute_prediction(df, params, price_func, q_form):
#     alpha, q0, beta, m = params
#     p_t = np.maximum(alpha * price_func(df[PRICE_COL].values), 0)
#     q_t = compute_q_t(df, (q0, beta), q_form)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q_t, m), p_t, q_t

# def residuals(params, df, price_func, q_form):
#     alpha, q0, beta, m = params
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, q_form)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted

# # --------- 拟合函数 + 显著性 t/p 值 ----------
# def fit_bass(df, price_func, q_form):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [0.01, 0.01, 0.01, m_guess]  # alpha, q0, beta, m
#     bounds = ([-10, 0, -10, 0.9*m_guess], [10, 1, 10, 20*m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, q_form), method="trf")
#     if not res.success:
#         return res

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)
#     y_pred, _, _ = compute_prediction(df, params, price_func, q_form)

#     # 数值雅可比
#     J = []
#     for i in range(k):
#         p_eps = params.copy()
#         p_eps[i] += eps
#         y_pred_eps, _, _ = compute_prediction(df, p_eps, price_func, q_form)
#         J.append((y_pred_eps - y_pred) / eps)
#     J = np.array(J).T

#     # 条件数
#     try:
#         cond = np.linalg.cond(J.T @ J)
#     except np.linalg.LinAlgError:
#         cond = np.nan

#     # 显著性 t/p 值
#     residuals_vec = df[NEW_COL].values - y_pred
#     sigma2 = np.sum(residuals_vec**2)/(n - k)
#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12*np.eye(k))
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)
#     tvals = params / se
#     pvals = 2*(1 - t.cdf(np.abs(tvals), df=n-k))

#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#     return res

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     results = []
#     valid_models = []

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], color='black', label="真实新增", linewidth=2)

#     for pf_name, pf_func in PRICE_FUNCS.items():
#         for q_form in ["linear", "log", "exp"]:
#             model_name = f"{pf_name} + {q_form}_q (no p0)"
#             print(f"\n=== 拟合模型: {model_name} ===")
#             res = fit_bass(df, pf_func, q_form)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 print(f"⚠️ {model_name} 拟合失败")
#                 continue

#             alpha, q0, beta, m = res.x
#             dN_pred, p_t, q_t = compute_prediction(df, res.x, pf_func, q_form)
#             rmse = np.sqrt(np.mean((df[NEW_COL]-dN_pred)**2))
#             sse = np.sum((df[NEW_COL]-dN_pred)**2)

#             print(f"✅ {model_name} 拟合成功: alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")
#             print("--- 参数显著性 t/p 值 ---")
#             for name, val, tval, pval in zip(["alpha","q0","beta","m"], res.x, res.tvals, res.pvals):
#                 print(f"{name:5s}: val={val:.6f}, t={tval:.3f}, p={pval:.6e}")

#             results.append({
#                 "model": model_name,
#                 "alpha": alpha, "q0": q0, "beta": beta, "m": m,
#                 "SSE": sse, "RMSE": rmse,
#                 "t_alpha": res.tvals[0], "p_alpha": res.pvals[0],
#                 "t_q0": res.tvals[1], "p_q0": res.pvals[1],
#                 "t_beta": res.tvals[2], "p_beta": res.pvals[2],
#                 "t_m": res.tvals[3], "p_m": res.pvals[3],
#             })

#             df[f"pred_new_{model_name}"] = dN_pred
#             df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
#             valid_models.append(model_name)

#             plt.plot(df[DATE_COL], dN_pred, '--', label=model_name)

#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 所有拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

#     # 新增图
#     plt.xlabel("日期")
#     plt.ylabel("新增开发者数 dN/dt")
#     plt.title("Bass 模型 p(t)=α·f(price), q(t) 不同形式拟合对比 (无 p0)")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()

#     # 累积曲线图
#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[CUM_COL], color='black', label="真实累积", linewidth=2)
#     for model_name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{model_name}"], '--', label=model_name)
#     plt.xlabel("日期")
#     plt.ylabel("累积开发者数 N(t)")
#     plt.title("Bass 模型累积曲线拟合对比 (无 p0)")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()

# 加入滞后和平滑
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# QEVENT_COL = "btc_bip_event"

# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# # 滞后与平滑参数
# PRICE_LAG = 0
# PRICE_SMOOTH = 0
# QEVENT_LAG = 0
# QEVENT_SMOOTH = 0

# OUTPUT_PNG_NEW = "btc_bass_pqfit_new_dev_lag_smooth.png"
# OUTPUT_PNG_CUM = "btc_bass_pqfit_cum_dev_lag_smooth.png"
# OUTPUT_CSV = "btc_bass_pqfit_results_lag_smooth.csv"
# # ===================================

# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# # --------- 滞后和平滑函数 ----------
# def apply_lag_smooth(x, lag=0, smooth=1):
#     """对序列进行滞后和平滑"""
#     x = pd.Series(x).shift(lag).rolling(smooth, min_periods=1).mean()
#     return x.fillna(method="bfill").values

# # --------- p(t) 函数 ----------
# def price_identity(price):
#     price = apply_lag_smooth(price, PRICE_LAG, PRICE_SMOOTH)
#     return normalize(price)

# def price_log(price):
#     price = apply_lag_smooth(price, PRICE_LAG, PRICE_SMOOTH)
#     return normalize(np.log(np.maximum(price, 1e-8)))

# def price_pct(price):
#     price = apply_lag_smooth(price, PRICE_LAG, PRICE_SMOOTH)
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return normalize(pct)

# PRICE_FUNCS = {
#     "linear_price": price_identity,
#     "log_price": price_log,
#     "pct_price": price_pct
# }

# # --------- q(t) 函数 ----------
# def compute_q_t(df, q_params, q_form):
#     q0, beta = q_params
#     event = apply_lag_smooth(df[QEVENT_COL].values, QEVENT_LAG, QEVENT_SMOOTH)
#     event = normalize(event)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * event, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * event)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# # --------- Bass 模型 ----------
# def dN_pred(N, p_t, q_t, m):
#     remaining = np.maximum(m - N, 0)
#     return (p_t + q_t * (N / m)) * remaining

# def compute_prediction(df, params, price_func, q_form):
#     alpha, q0, beta, m = params
#     p_t = np.maximum(alpha * price_func(df[PRICE_COL].values), 0)
#     q_t = compute_q_t(df, (q0, beta), q_form)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q_t, m), p_t, q_t

# def residuals(params, df, price_func, q_form):
#     alpha, q0, beta, m = params
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, q_form)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted

# # --------- 拟合函数 + 显著性 t/p 值 ----------
# def fit_bass(df, price_func, q_form):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [0.01, 0.01, 0.01, m_guess]  # alpha, q0, beta, m
#     bounds = ([-10, 0, -10, 0.9*m_guess], [10, 1, 10, 20*m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, q_form), method="trf")
#     if not res.success:
#         return res

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)
#     y_pred, _, _ = compute_prediction(df, params, price_func, q_form)

#     # 数值雅可比
#     J = []
#     for i in range(k):
#         p_eps = params.copy()
#         p_eps[i] += eps
#         y_pred_eps, _, _ = compute_prediction(df, p_eps, price_func, q_form)
#         J.append((y_pred_eps - y_pred) / eps)
#     J = np.array(J).T

#     # 条件数
#     try:
#         cond = np.linalg.cond(J.T @ J)
#     except np.linalg.LinAlgError:
#         cond = np.nan

#     # 显著性 t/p 值
#     residuals_vec = df[NEW_COL].values - y_pred
#     sigma2 = np.sum(residuals_vec**2)/(n - k)
#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12*np.eye(k))
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)
#     tvals = params / se
#     pvals = 2*(1 - t.cdf(np.abs(tvals), df=n-k))

#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#     return res

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     results = []
#     valid_models = []

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], color='black', label="真实新增", linewidth=2)

#     for pf_name, pf_func in PRICE_FUNCS.items():
#         for q_form in ["linear", "log", "exp"]:
#             model_name = f"{pf_name} + {q_form}_q (lag+smooth)"
#             print(f"\n=== 拟合模型: {model_name} ===")
#             res = fit_bass(df, pf_func, q_form)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 print(f"⚠️ {model_name} 拟合失败")
#                 continue

#             alpha, q0, beta, m = res.x
#             dN_pred, p_t, q_t = compute_prediction(df, res.x, pf_func, q_form)
#             rmse = np.sqrt(np.mean((df[NEW_COL]-dN_pred)**2))
#             sse = np.sum((df[NEW_COL]-dN_pred)**2)

#             print(f"✅ {model_name} 拟合成功: alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")
#             print("--- 参数显著性 t/p 值 ---")
#             for name, val, tval, pval in zip(["alpha","q0","beta","m"], res.x, res.tvals, res.pvals):
#                 print(f"{name:5s}: val={val:.6f}, t={tval:.3f}, p={pval:.6e}")

#             results.append({
#                 "model": model_name,
#                 "alpha": alpha, "q0": q0, "beta": beta, "m": m,
#                 "SSE": sse, "RMSE": rmse,
#                 "t_alpha": res.tvals[0], "p_alpha": res.pvals[0],
#                 "t_q0": res.tvals[1], "p_q0": res.pvals[1],
#                 "t_beta": res.tvals[2], "p_beta": res.pvals[2],
#                 "t_m": res.tvals[3], "p_m": res.pvals[3],
#             })

#             df[f"pred_new_{model_name}"] = dN_pred
#             df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
#             valid_models.append(model_name)

#             plt.plot(df[DATE_COL], dN_pred, '--', label=model_name)

#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 所有拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

#     # 新增图
#     plt.xlabel("日期")
#     plt.ylabel("新增开发者数 dN/dt")
#     plt.title("Bass 模型 p(t)=α·f(price), q(t)=g(q_event) 滞后+平滑拟合对比")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()

#     # 累积曲线图
#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[CUM_COL], color='black', label="真实累积", linewidth=2)
#     for model_name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{model_name}"], '--', label=model_name)
#     plt.xlabel("日期")
#     plt.ylabel("累积开发者数 N(t)")
#     plt.title("Bass 模型累积曲线拟合对比 (滞后+平滑)")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()



# p(t)不标准化，q(t)标准化
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# Q_EVENT_COL = "btc_q_event"  # q(t)对应事件列
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_price_qfit_new.png"
# OUTPUT_PNG_CUM = "btc_bass_price_qfit_cum.png"
# OUTPUT_CSV = "btc_bass_price_qfit_results.csv"
# # ===================================

# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, Q_EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     df = df.loc[mask].copy()
#     return df

# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q_t, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q_t * (N / m)) * remaining_market

# # q(t) 三种形式
# def q_linear(q0, beta, q_event):
#     return np.maximum(q0 + beta * q_event, 0)

# def q_log(q0, beta, q_event):
#     return np.maximum(q0 + beta * np.log1p(np.maximum(q_event, 0)), 0)

# def q_exp(q0, beta, q_event):
#     return np.maximum(q0 * np.exp(beta * q_event), 0)

# def compute_prediction(df, params, price_func, q_func):
#     p0, alpha, q0, beta, m = params
#     price = df[PRICE_COL].values
#     q_event = df[Q_EVENT_COL].values
#     p_t = np.maximum(p0 + alpha * price_func(price), 0)
#     q_t = q_func(q0, beta, q_event)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q_t, m), p_t, q_t

# # --------- least_squares 残差函数 ----------
# def residuals(params, df, price_func, q_func):
#     p0, alpha, q0, beta, m = params
#     if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, q_func)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted

# # --------- 拟合 + 显著性检验 ----------
# def fit_bass(df, price_func, q_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, 0.01, m_guess]
#     bounds = ([0, -10, 0, -10, 0.9 * m_guess], [1, 10, 10, 10, 20 * m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, q_func), method="trf")
#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # 数值近似雅可比
#     y_pred, _, _ = compute_prediction(df, params, price_func, q_func)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _, _ = compute_prediction(df, params_eps, price_func, q_func)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T

#     # 条件数
#     try:
#         cond = np.linalg.cond(J.T @ J)
#         print(f"⚙️ Hessian 条件数 cond={cond:.2e}")
#     except np.linalg.LinAlgError:
#         cond = np.nan

#     # 显著性检验
#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred
#     sigma2 = np.sum(residuals_vec**2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

#     param_names = ["p0", "alpha", "q0", "beta", "m"]
#     print("\n--- 参数显著性 t/p 值 ---")
#     for name, val, tval, pval in zip(param_names, params, tvals, pvals):
#         print(f"{name:5s} : val={val:.6f}, t={tval:.3f}, p={pval:.6e}")

#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#     return res

# # --------- price 不标准化形式 ----------
# def price_identity(price):
#     return price

# def price_log(price):
#     return np.log(np.maximum(price, 1e-8))

# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return pct

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     price_models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_price": price_pct
#     }

#     q_models = {
#         "linear_q": q_linear,
#         "log_q": q_log,
#         "exp_q": q_exp
#     }

#     results = []

#     for pname, pfunc in price_models.items():
#         for qname, qfunc in q_models.items():
#             model_name = f"{pname} + {qname}"
#             print(f"\n=== 拟合模型: {model_name} ===")
#             res = fit_bass(df, pfunc, qfunc)
#             if not res.success or np.any(np.isnan(res.x)):
#                 print(f"⚠️ 模型 {model_name} 优化失败或参数异常，跳过。")
#                 continue

#             p0, alpha, q0, beta, m = res.x
#             dN_predicted, p_t, q_t = compute_prediction(df, res.x, pfunc, qfunc)
#             rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#             sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

#             print(f"✅ {model_name} 拟合成功: p0={p0:.6f}, alpha={alpha:.6f}, q0={q0:.6f}, beta={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#             results.append({
#                 "model": model_name,
#                 "p0": p0, "alpha": alpha, "q0": q0, "beta": beta, "m": m,
#                 "SSE": sse, "RMSE": rmse,
#                 "t_p0": res.tvals[0], "p_p0": res.pvals[0],
#                 "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
#                 "t_q0": res.tvals[2], "p_q0": res.pvals[2],
#                 "t_beta": res.tvals[3], "p_beta": res.pvals[3],
#                 "t_m": res.tvals[4], "p_m": res.pvals[4],
#             })

#             # 绘图
#             df[f"pred_new_{model_name}"] = dN_predicted
#             df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)

#     # 保存结果表格
#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 所有模型结果保存至 {OUTPUT_CSV}")

#     # 新增图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
#     for r in results:
#         name = r["model"]
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend(); plt.xlabel("日期"); plt.ylabel("新增用户"); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)

#     # 累积图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积", color="black", linewidth=2)
#     for r in results:
#         name = r["model"]
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.legend(); plt.xlabel("日期"); plt.ylabel("累积用户"); plt.grid(True, linestyle="--"); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()



