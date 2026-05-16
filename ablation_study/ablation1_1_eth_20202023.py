"""
M1.1 Ablation: Pure Bass Model 连续拟合 离散拟合参数不显著
==============================
p(t) = p0          (no price, no profession-logic events)
q(t) = q0          (no herding-logic events)
No in-flow effects (no direct migration, no gamma_in)
No out-flow effects (no delta_out)

ΔN(t) = [p0 + q0 * N(t-1)/m] * (m - N(t-1))

Parameters: [p0, q0, m]  — 3 parameters only
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import scipy.stats as stats
import matplotlib.pyplot as plt
import os
from datetime import datetime

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
START_DATE = "2020-10-01"
END_DATE = "2023-01-01"

OUTPUT_PNG_NEW = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M1_1_eth_20202023.png"
OUTPUT_PNG_CUM = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M1_1_eth_20202023.png"
OUTPUT_CSV = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M1_1_eth_20202023.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    df = df.loc[mask].copy()
    return df

# --------- 模型定义 ----------
def bass_model_N(t, p, q, m):
    """Bass 模型累计量 N(t)"""
    if p == 0:
        return m * (1 - np.exp(-q * t))
    denom = 1 + (q / p) * np.exp(-(p + q) * t)
    return m * (1 - np.exp(-(p + q) * t)) / denom

def bass_model_dN(t, p, q, m):
    """Bass 模型新增量 dN/dt"""
    if p == 0:
        return m * q * np.exp(-q * t)

    exp_term = np.exp(-(p + q) * t)
    numerator = m * (p + q)**2 / p * exp_term
    denominator = (1 + (q / p) * exp_term)**2

    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)

# --------- 评价指标 ----------
def compute_metrics(y_true, y_pred, k_params):
    T = len(y_true)
    error = y_true - y_pred

    MAD = np.mean(np.abs(error))
    SSE = np.sum(error**2)
    MSE = SSE / T
    RMSE = np.sqrt(MSE)

    # R2
    ss_total = np.sum((y_true - np.mean(y_true))**2)
    R2 = 1 - SSE / ss_total if ss_total != 0 else np.nan

    # Adjusted R2
    adj_R2 = 1 - (1 - R2) * (T - 1) / (T - k_params - 1) if T > k_params + 1 else np.nan

    # MAPE（避免除0）
    mask = y_true != 0
    MAPE = np.mean(np.abs(error[mask] / y_true[mask])) * 100 if np.any(mask) else np.nan

    # WAPE
    WAPE = np.sum(np.abs(error)) / np.sum(y_true) * 100 if np.sum(y_true) != 0 else np.nan

    return {
        "MAD": MAD,
        "SSE": SSE,
        "MSE": MSE,
        "RMSE": RMSE,
        "R2": R2,
        "Adj_R2": adj_R2,
        "MAPE": MAPE,
        "WAPE": WAPE
    }

# --------- 参数拟合 ----------
def fit_bass(df):
    start_date = pd.to_datetime(START_DATE)
    df['t'] = (df[DATE_COL] - start_date).dt.days.values
    t = df['t'].values

    y_true_dN = df[NEW_COL].values
    y_true_cum = df[CUM_COL].values

    # N0 = y_true_cum[0]  # *** 新增：真实累计起点 ***

    # 初始猜测
    m_guess_cum = np.max(y_true_cum) * 1.2
    p0 = [0.01, 0.3, m_guess_cum]
    bounds_lower = [1e-6, 0, np.max(y_true_cum) * 1.05]
    bounds_upper = [0.99, 1.0, np.max(y_true_cum) * 10.0]

    try:
        popt, pcov = curve_fit(
            bass_model_dN, t, y_true_dN,
            p0=p0,
            bounds=(bounds_lower, bounds_upper),
            maxfev=10000,
            ftol=1e-8
        )
        p, q, m = popt
    except Exception as e:
        print(f"拟合失败: {e}")
        return None, None

    dN_pred = bass_model_dN(t, *popt)

    # *** 新增：累计预测加上 N0 平移，使曲线从真实值开始 ***
    # N_pred = N0 + bass_model_N(t, *popt)
    N_pred = bass_model_N(t, *popt)

    rmse_dN = np.sqrt(np.mean((y_true_dN - dN_pred) ** 2))

    se = np.sqrt(np.diag(pcov))

    n = len(df)
    k = 3
    residuals = y_true_dN - dN_pred

    if n - k > 0:
        sigma2 = np.sum(residuals**2) / (n - k)
        tvals = popt / se
        pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), df=n - k))
    else:
        tvals = np.full(k, np.nan)
        pvals = np.full(k, np.nan)

    return popt, {
        'se': se,
        'tvals': tvals,
        'pvals': pvals,
        'rmse_dN': rmse_dN,
        'N_pred': N_pred,
        'dN_pred': dN_pred
    }

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)
    
    # 窗口内累计归零
    cum_offset = df[CUM_COL].iloc[0] - df[NEW_COL].iloc[0]
    df[CUM_COL] = df[CUM_COL] - cum_offset

    print("\n=== 拟合模型：Bass dN/dt（窗口内累计版本） ===")
    popt, fit_info = fit_bass(df)
    if popt is None:
        print(f"⚠️ 模型优化失败，跳过")
        return

    p, q, m = popt
    metrics = compute_metrics(df[NEW_COL].values, fit_info['dN_pred'], k_params=3)

    print(f"✅ 拟合成功：p={p:.6f}, q={q:.6f}, m={m:.1f}")
    print("\n--- 评价指标（基于新增量 dN）---")
    for k, v in metrics.items():
        print(f"{k:8s}: {v:.4f}")

    df["pred_new"] = fit_info['dN_pred']
    df["pred_cum"] = fit_info['N_pred']

    results = [{
        "model": "constant_p_bass_dN_fit",
        "p": p, "q": q, "m": m,
        **metrics,
        "t_p": fit_info['tvals'][0], "p_p": fit_info['pvals'][0],
        "t_q": fit_info['tvals'][1], "p_q": fit_info['pvals'][1],
        "t_m": fit_info['tvals'][2], "p_m": fit_info['pvals'][2],
    }]

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

    print("\n--- 参数显著性检验 ---")
    for name, val, se_i, t_i, p_i in zip(["p", "q", "m"], popt, fit_info['se'], fit_info['tvals'], fit_info['pvals']):
        print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

    # --- 绘图 ---
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实 N(t)", color="black")
    plt.plot(df[DATE_COL], df["pred_cum"], "--", label="拟合 N(t)（已对齐 N0）")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black")
    plt.plot(df[DATE_COL], df["pred_new"], "--", label="拟合新增 (dN/dt)")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()