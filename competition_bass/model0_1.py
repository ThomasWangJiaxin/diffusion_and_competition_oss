# === Discrete Bass Model with full statistical output ===
# ✔ 使用上一期的 N[i-1]，而不是真实数据
# ✔ 通过 difference equation 预测 dN，累积得到 N

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# import scipy.stats as stats
# import matplotlib.pyplot as plt
# import os
# from datetime import datetime

# # ============= Parameters =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_new_dev_discrete.png"
# OUTPUT_PNG_CUM = "btc_bass_cum_dev_discrete.png"
# OUTPUT_CSV = "btc_bass_results_discrete.csv"
# # ======================================


# # --------- Load Data ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# # --------- Discrete Bass Model ----------
# def bass_discrete_new(t, p, q, m, N0):
#     T = len(t)
#     N = np.zeros(T)
#     dN = np.zeros(T)

#     N[0] = N0

#     for i in range(1, T):
#         dN[i] = (p + q * (N[i-1] / m)) * (m - N[i-1])
#         N[i] = N[i-1] + dN[i]

#     return dN


# def simulate_bass_discrete(p, q, m, N0, T):
#     N = np.zeros(T)
#     dN = np.zeros(T)
#     N[0] = N0

#     for i in range(1, T):
#         dN[i] = (p + q * (N[i-1] / m)) * (m - N[i-1])
#         N[i] = N[i-1] + dN[i]

#     return N, dN


# # --------- Model Fitting ----------
# def fit_bass_discrete(df):
#     y_true_dN = df[NEW_COL].values
#     y_true_cum = df[CUM_COL].values
#     N0 = y_true_cum[0]

#     t = np.arange(len(df))

#     # initial guess
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

#     # statistics
#     se = np.sqrt(np.diag(pcov))
#     residuals = y_true_dN - dN_pred
#     n = len(df)
#     k = 3  # parameters

#     sigma2 = np.sum(residuals ** 2) / (n - k)
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


# # --------- Main ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     print("\n=== Fitting Discrete Bass Model ===")
#     popt, fit_info = fit_bass_discrete(df)

#     p, q, m = popt
#     rmse = fit_info["rmse_dN"]

#     se_p, se_q, se_m = fit_info["se"]
#     t_p, t_q, t_m = fit_info["tvals"]
#     p_pval, p_qval, p_mval = fit_info["pvals"]

#     print(f"\n=== Parameter Estimates ===")
#     print(f"p = {p:.6f}  (SE={se_p:.6f}, t={t_p:.3f}, p={p_pval:.3f})")
#     print(f"q = {q:.6f}  (SE={se_q:.6f}, t={t_q:.3f}, p={p_qval:.3f})")
#     print(f"m = {m:.1f}  (SE={se_m:.1f}, t={t_m:.3f}, p={p_mval:.3f})")
#     print(f"RMSE (ΔN) = {rmse:.4f}")
#     print(f"N0 (initial cumulative) = {fit_info['N0']}")

#     # save predictions
#     df["pred_new"] = fit_info["dN_pred"]
#     df["pred_cum"] = fit_info["N_pred"]

#     # save results CSV
#     pd.DataFrame([{
#         "param": "p", "estimate": p, "se": se_p, "t": t_p, "p_value": p_pval
#     }, {
#         "param": "q", "estimate": q, "se": se_q, "t": t_q, "p_value": p_qval
#     }, {
#         "param": "m", "estimate": m, "se": se_m, "t": t_m, "p_value": p_mval
#     }, {
#         "param": "RMSE_dN", "estimate": rmse
#     }]).to_csv(OUTPUT_CSV, index=False)

#     # --------- Plots ---------

#     # Cumulative plot
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="Actual cumulative N(t)")
#     plt.plot(df[DATE_COL], df["pred_cum"], "--", label="Predicted Bass N(t)")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

#     # New developers plot
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="Actual daily ΔN")
#     plt.plot(df[DATE_COL], df["pred_new"], "--", label="Predicted Bass ΔN")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()


# # === 改为离散 Bass 拟合版本（chatgpt二版） ，两个版本结果一样===
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
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "btc_bass_new_dev_dNfit.png"
OUTPUT_PNG_CUM = "btc_bass_cum_dev_dNfit.png"
OUTPUT_CSV = "btc_bass_results_dNfit.csv"
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

# --------- 离散 Bass 模型 ----------
def bass_model_dN_discrete(t, p, q, m, N0):
    """
    离散 Bass：ΔN_t = (m - N_t) * (p + q * N_t / m)
    t: 时间步序列，必须是整数
    返回每期新增量数组
    """
    t = t.astype(int)
    n = len(t)
    dN = np.zeros(n)
    N = np.zeros(n)
    N[0] = N0

    for i in range(1, n):
        dN[i] = (m - N[i-1]) * (p + q * N[i-1] / m)
        N[i] = N[i-1] + dN[i]

    return dN

# 封装给 curve_fit 的函数（不允许 N0 做参数）
def bass_model_dN_fitfunc(t, p, q, m):
    global g_N0
    return bass_model_dN_discrete(t, p, q, m, g_N0)

# --------- 参数拟合 ----------
def fit_bass(df):
    global g_N0

    start_date = pd.to_datetime(START_DATE)
    df['t'] = (df[DATE_COL] - start_date).dt.days.values
    t = df['t'].values

    y_true_dN = df[NEW_COL].values
    y_true_cum = df[CUM_COL].values

    g_N0 = y_true_cum[0]  # 存为全局变量供拟合用

    # 初始 guess
    m_guess = np.max(y_true_cum) * 1.2
    p0 = [0.01, 0.3, m_guess]
    bounds_lower = [1e-6, 0, np.max(y_true_cum) * 0.5]
    bounds_upper = [0.99, 1.0, np.max(y_true_cum) * 20.0]

    try:
        popt, pcov = curve_fit(
            bass_model_dN_fitfunc, t, y_true_dN,
            p0=p0, bounds=(bounds_lower, bounds_upper),
            maxfev=10000
        )
        p, q, m = popt
    except Exception as e:
        print(f"拟合失败: {e}")
        return None, None

    # 预测新增量
    dN_pred = bass_model_dN_discrete(t, p, q, m, g_N0)

    # 预测累计量
    N_pred = np.cumsum(dN_pred) + 0*g_N0
    N_pred[0] = g_N0

    # 误差
    rmse_dN = np.sqrt(np.mean((y_true_dN - dN_pred)**2))

    se = np.sqrt(np.diag(pcov))
    n = len(df)
    k = 3
    residuals = y_true_dN - dN_pred

    if n - k > 0:
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
        'dN_pred': dN_pred,
        'N0': g_N0
    }

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    print("\n=== 拟合模型：离散 Bass 新增 ΔN_t（带 N0） ===")
    popt, fit_info = fit_bass(df)
    if popt is None:
        print(f"⚠️ 模型优化失败，跳过")
        return

    p, q, m = popt
    rmse = fit_info['rmse_dN']
    sse = np.sum((df[NEW_COL].values - fit_info['dN_pred']) ** 2)

    print(f"✅ 拟合成功：p={p:.6f}, q={q:.6f}, m={m:.1f}, RMSE_dN={rmse:.3f}")
    print(f"初始累计 N0 = {fit_info['N0']}")

    df["pred_new"] = fit_info["dN_pred"]
    df["pred_cum"] = fit_info["N_pred"]

    results = [{
        "model": "discrete_bass_dN_fit",
        "p": p, "q": q, "m": m,
        "SSE_dN": sse, "RMSE_dN": rmse,
        "t_p": fit_info['tvals'][0], "p_p": fit_info['pvals'][0],
        "t_q": fit_info['tvals'][1], "p_q": fit_info['pvals'][1],
        "t_m": fit_info['tvals'][2], "p_m": fit_info['pvals'][2],
    }]
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 结果已保存：{OUTPUT_CSV}")

    # --- 绘图 ---
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实 N(t)", color="black")
    plt.plot(df[DATE_COL], df["pred_cum"], "--", label="离散 Bass 拟合 N(t)")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black")
    plt.plot(df[DATE_COL], df["pred_new"], "--", label="离散 Bass 新增 ΔN_t")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()