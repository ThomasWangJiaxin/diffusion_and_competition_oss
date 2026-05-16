# bass model拟合应该用N(t-1)

# event也使用了滞后的
# btc_event_lag1	btc_event_sum_7	btc_event_mean_7	btc_event_vol_7	btc_event_sum_14	btc_event_mean_14	btc_event_vol_14	btc_event_sum_21	btc_event_mean_21	btc_event_vol_21	btc_event_sum_30	btc_event_mean_30	btc_event_vol_30	
# btc_p_event_lag1	btc_p_event_sum_7	btc_p_event_mean_7	btc_p_event_vol_7	btc_p_event_sum_14	btc_p_event_mean_14	btc_p_event_vol_14	btc_p_event_sum_21	btc_p_event_mean_21	btc_p_event_vol_21	btc_p_event_sum_30	btc_p_event_mean_30	btc_p_event_vol_30	
# btc_q_event_lag1	btc_q_event_sum_7	btc_q_event_mean_7	btc_q_event_vol_7	btc_q_event_sum_14	btc_q_event_mean_14	btc_q_event_vol_14	btc_q_event_sum_21	btc_q_event_mean_21	btc_q_event_vol_21	btc_q_event_sum_30	btc_q_event_mean_30	btc_q_event_vol_30	
# bip_event_lag1	bip_event_sum_7	bip_event_mean_7	bip_event_vol_7	bip_event_sum_14	bip_event_mean_14	bip_event_vol_14	bip_event_sum_21	bip_event_mean_21	bip_event_vol_21	bip_event_sum_30	bip_event_mean_30	bip_event_vol_30	
# bip_p_event_lag1	bip_p_event_sum_7	bip_p_event_mean_7	bip_p_event_vol_7	bip_p_event_sum_14	bip_p_event_mean_14	bip_p_event_vol_14	bip_p_event_sum_21	bip_p_event_mean_21	bip_p_event_vol_21	bip_p_event_sum_30	bip_p_event_mean_30	bip_p_event_vol_30	
# bip_q_event_lag1	bip_q_event_sum_7	bip_q_event_mean_7	bip_q_event_vol_7	bip_q_event_sum_14	bip_q_event_mean_14	bip_q_event_vol_14	bip_q_event_sum_21	bip_q_event_mean_21	bip_q_event_vol_21	bip_q_event_sum_30	bip_q_event_mean_30	bip_q_event_vol_30	
# btc_bip_event_lag1	btc_bip_event_sum_7	btc_bip_event_mean_7	btc_bip_event_vol_7	btc_bip_event_sum_14	btc_bip_event_mean_14	btc_bip_event_vol_14	btc_bip_event_sum_21	btc_bip_event_mean_21	btc_bip_event_vol_21	btc_bip_event_sum_30	btc_bip_event_mean_30	btc_bip_event_vol_30	
# btc_p_bip_p_event_lag1	btc_p_bip_p_event_sum_7	btc_p_bip_p_event_mean_7	btc_p_bip_p_event_vol_7	btc_p_bip_p_event_sum_14	btc_p_bip_p_event_mean_14	btc_p_bip_p_event_vol_14	btc_p_bip_p_event_sum_21	btc_p_bip_p_event_mean_21	btc_p_bip_p_event_vol_21	btc_p_bip_p_event_sum_30	btc_p_bip_p_event_mean_30	btc_p_bip_p_event_vol_30	
# btc_q_bip_q_event_lag1	btc_q_bip_q_event_sum_7	btc_q_bip_q_event_mean_7	btc_q_bip_q_event_vol_7	btc_q_bip_q_event_sum_14	btc_q_bip_q_event_mean_14	btc_q_bip_q_event_vol_14	btc_q_bip_q_event_sum_21	btc_q_bip_q_event_mean_21	btc_q_bip_q_event_vol_21	btc_q_bip_q_event_sum_30	btc_q_bip_q_event_mean_30	btc_q_bip_q_event_vol_30	
# btc_p_bip_event_lag1	btc_p_bip_event_sum_7	btc_p_bip_event_mean_7	btc_p_bip_event_vol_7	btc_p_bip_event_sum_14	btc_p_bip_event_mean_14	btc_p_bip_event_vol_14	btc_p_bip_event_sum_21	btc_p_bip_event_mean_21	btc_p_bip_event_vol_21	btc_p_bip_event_sum_30	btc_p_bip_event_mean_30	btc_p_bip_event_vol_30	
# btc_bip_p_event_lag1	btc_bip_p_event_sum_7	btc_bip_p_event_mean_7	btc_bip_p_event_vol_7	btc_bip_p_event_sum_14	btc_bip_p_event_mean_14	btc_bip_p_event_vol_14	btc_bip_p_event_sum_21	btc_bip_p_event_mean_21	btc_bip_p_event_vol_21	btc_bip_p_event_sum_30	btc_bip_p_event_mean_30	btc_bip_p_event_vol_30	
# btc_q_bip_event_lag1	btc_q_bip_event_sum_7	btc_q_bip_event_mean_7	btc_q_bip_event_vol_7	btc_q_bip_event_sum_14	btc_q_bip_event_mean_14	btc_q_bip_event_vol_14	btc_q_bip_event_sum_21	btc_q_bip_event_mean_21	btc_q_bip_event_vol_21	btc_q_bip_event_sum_30	btc_q_bip_event_mean_30	btc_q_bip_event_vol_30	
# btc_bip_q_event_lag1	btc_bip_q_event_sum_7	btc_bip_q_event_mean_7	btc_bip_q_event_vol_7	btc_bip_q_event_sum_14	btc_bip_q_event_mean_14	btc_bip_q_event_vol_14	btc_bip_q_event_sum_21	btc_bip_q_event_mean_21	btc_bip_q_event_vol_21	btc_bip_q_event_sum_30	btc_bip_q_event_mean_30	btc_bip_q_event_vol_30，


import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
QEVENT_COL = "btc_p_event_lag1"  # 使用滞后事件列
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "btc_bass_qfit_new_dev.png"
OUTPUT_PNG_CUM = "btc_bass_qfit_cum_dev.png"
OUTPUT_CSV = "btc_bass_qfit_results_t_p_lag.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

# --------- 工具函数 ----------
def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)

# --------- 模型定义 ----------
def dN_pred(N_lag, p, q_t, m):
    """Bass 增量模型，使用 N(t-1)"""
    remaining_market = np.maximum(m - N_lag, 0)
    return (p + q_t * (N_lag / m)) * remaining_market

def compute_q_t(df, q_params, q_form="exp"):
    q0, beta = q_params
    event = normalize(df[QEVENT_COL].values)  # 使用滞后事件列
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * event, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * event)
    else:
        raise ValueError("未知 q_form，请选择 'linear' / 'log' / 'exp'")
    return q_t

def compute_prediction(df, params, q_form):
    p, q0, beta, m = params
    q_t = compute_q_t(df, (q0, beta), q_form)
    N = df[CUM_COL].values
    N_lag = np.roll(N, 1)
    N_lag[0] = 0  # N(-1)=0
    dN_predicted = dN_pred(N_lag, p, q_t, m)  # 改变量名，避免与函数名冲突
    return dN_predicted, q_t


def residuals(params, df, q_form):
    p, q0, beta, m = params
    if m <= df[CUM_COL].max() or q0 < 0 or p < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_prediction(df, params, q_form)
    dN_true = df[NEW_COL].values
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return dN_true - dN_predicted

# --------- 参数拟合 + 显著性检验 ----------
def fit_bass(df, q_form):
    m_guess = 1.2 * df[CUM_COL].max()
    init = [1e-4, 0.01, 0.01, m_guess]
    bounds = ([0, 0, -10, 0.9 * m_guess], [1, 1, 10, 20 * m_guess])
    res = least_squares(residuals, init, bounds=bounds, args=(df, q_form), method="trf")

    if not res.success:
        return res

    params = res.x
    eps = 1e-6
    n = len(df)
    k = len(params)

    # 数值雅可比矩阵
    y_pred, _ = compute_prediction(df, params, q_form)
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _ = compute_prediction(df, params_eps, q_form)
        grad_i = (y_pred_eps - y_pred) / eps
        J.append(grad_i)
    J = np.array(J).T

    try:
        cond = np.linalg.cond(J.T @ J)
        print(f"⚙️ Hessian 条件数 cond={cond:.2e}")
    except np.linalg.LinAlgError:
        cond = np.nan
        print("⚠️ Hessian 条件数计算失败")

    residuals_vec = df[NEW_COL].values - y_pred
    sigma2 = np.sum(residuals_vec ** 2) / (n - k)
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)
    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

    res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
    return res

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    results = []
    for q_form in ["linear", "log", "exp"]:
        print(f"\n==============================")
        print(f"=== 拟合模型：q_form = {q_form} ===")
        print(f"==============================")

        res = fit_bass(df, q_form)
        if (not res.success) or np.any(np.isnan(res.x)):
            print(f"❌ {q_form} 模型优化失败。")
            continue

        p, q0, beta, m = res.x
        dN_predicted, q_t = compute_prediction(df, res.x, q_form)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
        sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

        print(f"✅ {q_form} 拟合成功：p={p:.6f}, q0={q0:.6f}, β={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

        result = {
            "q_form": q_form,
            "p": p, "q0": q0, "beta": beta, "m": m,
            "SSE": sse, "RMSE": rmse,
            "t_p": res.tvals[0], "p_p": res.pvals[0],
            "t_q0": res.tvals[1], "p_q0": res.pvals[1],
            "t_beta": res.tvals[2], "p_beta": res.pvals[2],
            "t_m": res.tvals[3], "p_m": res.pvals[3],
        }
        results.append(result)

    # 保存所有结果
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有 q_form 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
