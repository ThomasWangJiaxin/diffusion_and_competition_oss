# 仅修改q-->q(t)

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
QEVENT_COL = "eth_q_eip_event"
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "eth_bass_qfit_new_dev.png"
OUTPUT_PNG_CUM = "eth_bass_qfit_cum_dev.png"
OUTPUT_CSV = "eth_bass_qfit_results_t_p.csv"
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
def dN_pred(N, p, q_t, m):
    remaining_market = np.maximum(m - N, 0)
    return (p + q_t * (N / m)) * remaining_market


def compute_q_t(df, q_params, q_form="exp"):
    q0, beta = q_params
    event = normalize(df[QEVENT_COL].values)
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
    return dN_pred(N, p, q_t, m), q_t


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
        return res, None

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

    y_true = df[NEW_COL].values
    residuals_vec = y_true - y_pred
    sigma2 = np.sum(residuals_vec**2) / (n - k)
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)
    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

    print("\n--- 参数显著性检验 ---")
    for name, val, se_i, t_i, p_i in zip(["p", "q0", "beta", "m"], params, se, tvals, pvals):
        print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

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

    # 保存所有形式的结果
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有 q_form 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")


if __name__ == "__main__":
    main()


# 在上面基础上加入滞后+平滑

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
# PRICE_COL = "eth_price"
# QEVENT_COL = "eth_q_event"

# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# Q_FORM = "exp"   # 可选: "linear", "log", "exp"
# LAG_DAYS = 3     # ✅ 滞后期数
# SMOOTH_WINDOW = 5  # ✅ 平滑窗口长度（rolling mean）

# OUTPUT_PNG_NEW = "eth_bass_qfit_new_dev_lagsmooth.png"
# OUTPUT_PNG_CUM = "eth_bass_qfit_cum_dev_lagsmooth.png"
# OUTPUT_CSV = "eth_bass_qfit_results_t_p_lagsmooth.csv"
# # ===================================


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     df = df.loc[mask].copy()
#     return df


# # --------- 工具函数 ----------
# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)


# # --------- 模型定义 ----------
# def dN_pred(N, p, q_t, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p + q_t * (N / m)) * remaining_market


# # --------- q(t) 定义（新增：滞后 + 平滑） ----------
# def compute_q_t(df, q_params, q_form="exp", lag=LAG_DAYS, smooth_window=SMOOTH_WINDOW):
#     q0, beta = q_params

#     # 1️⃣ 提取并标准化事件序列
#     event = df[QEVENT_COL].values

#     # 2️⃣ 平滑（滚动平均）
#     if smooth_window > 1:
#         event = pd.Series(event).rolling(window=smooth_window, min_periods=1, center=False).mean().values

#     # 3️⃣ 滞后（shift）
#     if lag > 0:
#         event = np.roll(event, lag)
#         event[:lag] = event[lag]  # 填充前几项，避免nan

#     event = normalize(event)

#     # 4️⃣ 不同形式的 q(t)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * event, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * event)
#     else:
#         raise ValueError("未知 q_form，请选择 'linear' / 'log' / 'exp'")

#     return q_t


# def compute_prediction(df, params, q_form):
#     p, q0, beta, m = params
#     q_t = compute_q_t(df, (q0, beta), q_form)
#     N = df[CUM_COL].values
#     return dN_pred(N, p, q_t, m), q_t


# # --------- least_squares 残差函数 ----------
# def residuals(params, df, q_form):
#     p, q0, beta, m = params
#     if m <= df[CUM_COL].max() or q0 < 0 or p < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _ = compute_prediction(df, params, q_form)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, q_form):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = ([0, 0, -10, 0.9 * m_guess], [1, 1, 10, 20 * m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, q_form), method="trf")

#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # ===== 数值近似雅可比矩阵 =====
#     y_pred, _ = compute_prediction(df, params, q_form)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, q_form)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     # ===== 条件数输出 =====
#     try:
#         cond = np.linalg.cond(J.T @ J)
#         print(f"⚙️ Hessian 条件数 cond={cond:.2e}")
#     except np.linalg.LinAlgError:
#         cond = np.nan
#         print("⚠️ Hessian 条件数计算失败（矩阵奇异）")

#     # ===== 显著性检验 =====
#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred
#     sigma2 = np.sum(residuals_vec**2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k, k), np.nan)
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p", "q0", "beta", "m"], params, se, tvals, pvals):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     print(f"\n=== 拟合模型：q_form = {Q_FORM}, lag={LAG_DAYS}, smooth={SMOOTH_WINDOW} ===")
#     res = fit_bass(df, Q_FORM)
#     if (not res.success) or np.any(np.isnan(res.x)):
#         print("❌ 模型优化失败。")
#         return

#     p, q0, beta, m = res.x
#     dN_predicted, q_t = compute_prediction(df, res.x, Q_FORM)
#     rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#     sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)
#     print(f"✅ 拟合成功：p={p:.6f}, q0={q0:.6f}, β={beta:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#     cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
#     df["pred_new"] = dN_predicted
#     df["pred_cum"] = cum_predicted
#     df["q_t"] = q_t

#     result = {
#         "q_form": Q_FORM,
#         "lag_days": LAG_DAYS,
#         "smooth_window": SMOOTH_WINDOW,
#         "p": p, "q0": q0, "beta": beta, "m": m,
#         "SSE": sse, "RMSE": rmse,
#         "t_p": res.tvals[0], "p_p": res.pvals[0],
#         "t_q0": res.tvals[1], "p_q0": res.pvals[1],
#         "t_beta": res.tvals[2], "p_beta": res.pvals[2],
#         "t_m": res.tvals[3], "p_m": res.pvals[3],
#     }
#     pd.DataFrame([result]).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     plt.plot(df[DATE_COL], df["pred_new"], "--", label=f"预测新增 ({Q_FORM}, lag={LAG_DAYS}, smooth={SMOOTH_WINDOW})")
#     plt.xlabel("日期")
#     plt.ylabel("新增开发者数 dN/dt")
#     plt.title(f"Bass 模型：q(t)={Q_FORM} 拟合结果（滞后+平滑）")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     plt.plot(df[DATE_COL], df["pred_cum"], "--", label=f"预测累积 ({Q_FORM})")
#     plt.xlabel("日期")
#     plt.ylabel("累积开发者数 N(t)")
#     plt.title(f"Bass 模型 S 曲线拟合：q(t)={Q_FORM}（滞后+平滑）")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()
