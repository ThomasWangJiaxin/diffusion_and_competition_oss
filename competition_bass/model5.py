# 单改m(t),且平滑+滞后
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import minimize
from scipy.stats import t
import matplotlib.pyplot as plt
import os

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
PRICE_COL = "eth_price"
START_DATE = "2016-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "eth_bass_mfit_new_dev_pinghua+zhihou.png"
OUTPUT_PNG_CUM = "eth_bass_mfit_cum_dev_pinghua+zhihou.png"
OUTPUT_CSV = "eth_bass_mfit_results_pinghua+zhihou.csv"
# ===================================


# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df


def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    df = df.loc[mask].copy()
    df["price_lag"] = df[PRICE_COL].shift(1)
    df["price_pct"] = (df[PRICE_COL] - df["price_lag"]) / df["price_lag"]
    df["price_pct"] = df["price_pct"].replace([np.inf, -np.inf], 0).fillna(0)
    return df


# --------- 模型定义 ----------
def dN_pred(N, p, q, m):
    m = np.asarray(m)
    remaining_market = np.maximum(m - N, 0)
    return (p + q * (N / m)) * remaining_market


def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


def compute_prediction(df, params, m_type):
    p, q, m_base, beta = params
    price = df[PRICE_COL].values
    price_norm = normalize(price)

    if m_type == "add":
        m_t = m_base + beta * price_norm
    elif m_type == "mul":
        m_t = m_base * (1 + beta * price_norm)
    elif m_type == "exp":
        m_t = m_base * np.exp(beta * price_norm)
    else:
        raise ValueError("Invalid m_type")

    m_t = np.maximum(m_t, 1e-6)
    p_t = np.maximum(p, 0)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q, m_t), p_t


def objective(params, df, m_type):
    p, q, m_base, beta = params
    price = df[PRICE_COL].values
    price_norm = normalize(price)

    if m_type == "add":
        m_t = m_base + beta * price_norm
    elif m_type == "mul":
        m_t = m_base * (1 + beta * price_norm)
    elif m_type == "exp":
        m_t = m_base * np.exp(beta * price_norm)
    else:
        raise ValueError("Invalid m_type")

    m_t = np.maximum(m_t, 1e-6)
    if np.any(m_t <= df[CUM_COL].values) or q < 0 or p < 0:
        return 1e12

    dN_predicted, _ = compute_prediction(df, params, m_type)
    dN_true = df["smooth_new"].values  # 平滑后的新增
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return 1e12
    return np.sum((dN_true - dN_predicted) ** 2)


def compute_cumulative(df, new_dev_pred):
    N0 = df[CUM_COL].iloc[0]
    return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# --------- 参数拟合 + 显著性检验 ----------
def fit_bass(df, m_type):
    m_guess = 1.2 * df[CUM_COL].max()
    init = [1e-4, 0.01, m_guess, 0.01]
    bounds = [(0, 1), (0, 1), (0.9 * m_guess, 20 * m_guess), (0, 1)]

    res = minimize(objective, init, args=(df, m_type), bounds=bounds, method="L-BFGS-B")
    if not res.success:
        res.se = res.tvals = res.pvals = [np.nan]*4
        return res

    params = res.x
    eps = 1e-6
    n = len(df)
    k = len(params)

    y_pred, _ = compute_prediction(df, params, m_type)
    residuals = df["smooth_new"].values - y_pred
    sigma2 = np.sum(residuals**2) / (n - k)

    # 数值近似雅可比矩阵
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _ = compute_prediction(df, params_eps, m_type)
        grad_i = (y_pred_eps - y_pred) / eps
        J.append(grad_i)
    J = np.array(J).T

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        cov = np.full((k, k), np.nan)
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

    print("\n--- 参数显著性检验 ---")
    for name, val, se_i, t_i, p_i in zip(["p", "q", "m_base", "beta"], params, se, tvals, pvals):
        print(f"{name:8s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

    res.se, res.tvals, res.pvals = se, tvals, pvals
    return res


# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    # ====== 平滑 + 滞后配置 ======
    df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()
    lag_days = [0, 5, 14, 30, 60]
    # ============================

    m_types = {"add": "add", "mul": "mul", "exp": "exp"}

    results = []
    valid_models = []

    for name, m_type in m_types.items():
        print(f"\n=== 拟合模型：m_{name} ===")

        best_rmse = np.inf
        best_res, best_lag = None, None

        for lag in lag_days:
            df_lag = df.copy()
            df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
            df_lag = df_lag.dropna().reset_index(drop=True)

            res = fit_bass(df_lag, m_type)
            if (not res.success) or np.any(np.isnan(res.x)):
                continue

            p, q, m_base, beta = res.x
            dN_predicted, _ = compute_prediction(df_lag, res.x, m_type)
            rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

            print(f"Δ={lag:>2}天 | p={p:.6f}, q={q:.6f}, m={m_base:.1f}, β={beta:.6f}, RMSE={rmse:.3f}")

            if rmse < best_rmse:
                best_rmse, best_res, best_lag = rmse, res, lag

        if best_res is None:
            print(f"⚠️ 模型 {name} 优化失败。")
            continue

        p, q, m_base, beta = best_res.x
        print(f"✅ 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")

        dN_predicted, _ = compute_prediction(df, best_res.x, m_type)
        cum_predicted = compute_cumulative(df, dN_predicted)
        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_predicted

        results.append({
            "model": name, "best_lag": best_lag,
            "p": p, "q": q, "m_base": m_base, "beta": beta, "RMSE": best_rmse,
            "t_p": best_res.tvals[0], "p_p": best_res.pvals[0],
            "t_q": best_res.tvals[1], "p_q": best_res.pvals[1],
            "t_m_base": best_res.tvals[2], "p_m_base": best_res.pvals[2],
            "t_beta": best_res.tvals[3], "p_beta": best_res.pvals[3],
        })
        valid_models.append(name)

    if results:
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
    else:
        print("❌ 无有效模型结果。")
        return

    # 绘图
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
    plt.xlabel("日期"); plt.ylabel("ETH 新增开发者数 dN/dt")
    plt.title("ETH Bass 模型新增开发者（平滑 + 滞后）")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测 N(t) ({name})")
    plt.xlabel("日期"); plt.ylabel("ETH 累积开发者数 N(t)")
    plt.title("ETH Bass 模型累积开发者（平滑 + 滞后）")
    plt.legend(); plt.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
    plt.show()


if __name__ == "__main__":
    main()


# =======
# 把minimize改成least_squares优化

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t as student_t
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_ls_new_dev.png"
# OUTPUT_PNG_CUM = "eth_bass_ls_cum_dev.png"
# OUTPUT_CSV = "eth_bass_ls_results.csv"
# # ===================================


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     df = df.loc[mask].copy()
#     df["price_lag"] = df[PRICE_COL].shift(1)
#     df["price_pct"] = (df[PRICE_COL] - df["price_lag"]) / df["price_lag"]
#     df["price_pct"] = df["price_pct"].replace([np.inf, -np.inf], 0).fillna(0)
#     return df


# # --------- 模型定义 ----------
# def dN_pred(N, p, q, m):
#     m = np.asarray(m)
#     remaining_market = np.maximum(m - N, 0)
#     return (p + q * (N / m)) * remaining_market


# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)


# def compute_prediction(df, params, m_type):
#     p, q, m_base, beta = params
#     price = df[PRICE_COL].values
#     price_norm = normalize(price)

#     if m_type == "add":
#         m_t = m_base + beta * price_norm
#     elif m_type == "mul":
#         m_t = m_base * (1 + beta * price_norm)
#     elif m_type == "exp":
#         m_t = m_base * np.exp(beta * price_norm)
#     else:
#         raise ValueError("Invalid m_type")

#     m_t = np.maximum(m_t, 1e-6)
#     p_t = np.maximum(p, 0)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m_t), p_t


# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# # --------- least_squares 残差函数 ----------
# def residuals_func(params, df, m_type):
#     """返回残差向量，用于 least_squares 拟合"""
#     p, q, m_base, beta = params
#     price = df[PRICE_COL].values
#     price_norm = normalize(price)

#     if m_type == "add":
#         m_t = m_base + beta * price_norm
#     elif m_type == "mul":
#         m_t = m_base * (1 + beta * price_norm)
#     elif m_type == "exp":
#         m_t = m_base * np.exp(beta * price_norm)
#     else:
#         raise ValueError("Invalid m_type")

#     m_t = np.maximum(m_t, 1e-6)
#     if np.any(m_t <= df[CUM_COL].values) or q < 0 or p < 0:
#         return np.full_like(df["smooth_new"].values, 1e6)

#     dN_predicted, _ = compute_prediction(df, params, m_type)
#     dN_true = df["smooth_new"].values
#     return dN_true - dN_predicted  # 残差向量


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, m_type):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, m_guess, 0.01]
#     lower_bounds = [0, 0, 0.9 * m_guess, 0]
#     upper_bounds = [1, 1, 20 * m_guess, 1]

#     res = least_squares(
#         residuals_func,
#         init,
#         args=(df, m_type),
#         bounds=(lower_bounds, upper_bounds),
#         method="trf",  # trust region reflective
#         jac="2-point",
#     )

#     if not res.success:
#         res.se = res.tvals = res.pvals = [np.nan] * 4
#         return res

#     params = res.x
#     y_pred, _ = compute_prediction(df, params, m_type)
#     residuals = df["smooth_new"].values - y_pred
#     n, k = len(residuals), len(params)
#     sigma2 = np.sum(residuals ** 2) / (n - k)

#     # 雅可比矩阵与协方差
#     J = res.jac
#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - student_t.cdf(np.abs(tvals), df=n - k))

#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p", "q", "m_base", "beta"], params, se, tvals, pvals):
#         print(f"{name:8s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     res.se, res.tvals, res.pvals = se, tvals, pvals
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     # ====== 平滑 + 滞后配置 ======
#     df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()
#     lag_days = [0, 5, 14, 30, 60]
#     # ============================

#     m_types = {"add": "add", "mul": "mul", "exp": "exp"}

#     results = []
#     valid_models = []

#     for name, m_type in m_types.items():
#         print(f"\n=== 拟合模型：m_{name} ===")

#         best_rmse = np.inf
#         best_res, best_lag = None, None

#         for lag in lag_days:
#             df_lag = df.copy()
#             df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#             df_lag = df_lag.dropna().reset_index(drop=True)

#             res = fit_bass(df_lag, m_type)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 continue

#             p, q, m_base, beta = res.x
#             dN_predicted, _ = compute_prediction(df_lag, res.x, m_type)
#             rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#             print(f"Δ={lag:>2}天 | p={p:.6f}, q={q:.6f}, m={m_base:.1f}, β={beta:.6f}, RMSE={rmse:.3f}")

#             if rmse < best_rmse:
#                 best_rmse, best_res, best_lag = rmse, res, lag

#         if best_res is None:
#             print(f"⚠️ 模型 {name} 优化失败。")
#             continue

#         p, q, m_base, beta = best_res.x
#         print(f"✅ 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")

#         dN_predicted, _ = compute_prediction(df, best_res.x, m_type)
#         cum_predicted = compute_cumulative(df, dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({
#             "model": name, "best_lag": best_lag,
#             "p": p, "q": q, "m_base": m_base, "beta": beta, "RMSE": best_rmse,
#             "t_p": best_res.tvals[0], "p_p": best_res.pvals[0],
#             "t_q": best_res.tvals[1], "p_q": best_res.pvals[1],
#             "t_m_base": best_res.tvals[2], "p_m_base": best_res.pvals[2],
#             "t_beta": best_res.tvals[3], "p_beta": best_res.pvals[3],
#         })
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # 绘图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期"); plt.ylabel("ETH 新增开发者数 dN/dt")
#     plt.title("ETH Bass 模型新增开发者（least_squares 平滑 + 滞后）")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测 N(t) ({name})")
#     plt.xlabel("日期"); plt.ylabel("ETH 累积开发者数 N(t)")
#     plt.title("ETH Bass 模型累积开发者（least_squares 平滑 + 滞后）")
#     plt.legend(); plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()

