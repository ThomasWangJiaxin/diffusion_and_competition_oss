# 相比model1，在main函数中加入了7日滑动平均和对p(t)滞后网格参数
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# import matplotlib.pyplot as plt
# import os

# ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev_pinghua+zhihou.png" # 新增开发者图的文件名
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev_pinghua+zhihou.png" # 累积开发者图的文件名
# OUTPUT_CSV = "eth_bass_pricefit_results_pinghua+zhihou.csv"
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
#     # 计算价格变化率
#     df["price_lag"] = df[PRICE_COL].shift(1)
#     df["price_pct"] = (df[PRICE_COL] - df["price_lag"]) / df["price_lag"]
#     df["price_pct"] = df["price_pct"].replace([np.inf, -np.inf], 0).fillna(0)
#     return df


# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q, m):
#     """Bass 模型日新增预测值"""
#     # 确保 m-N 始终大于 0
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market


# def normalize(x):
#     """标准化（防止量级不一致）"""
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)


# def price_identity(price):
#     return normalize(price)


# def price_log(price):
#     val = np.log(np.maximum(price, 1e-8))
#     return normalize(val)


# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return normalize(pct)


# def compute_prediction(df, params, price_func):
#     """计算日新增预测值 (dN/dt) 和 动态 p(t)"""
#     p0, alpha, q, m = params
#     price = df[PRICE_COL].values
    
#     # 保证 p(t) 的输入与 normalize() 的输入是同一长度
#     p_input = price_func(price)
    
#     p_t = p0 + alpha * p_input
#     p_t = np.maximum(p_t, 0)
    
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m), p_t


# def objective(params, df, price_func):
#     p0, alpha, q, m = params
#     # 严格的边界约束
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _ = compute_prediction(df, params, price_func)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
#     return np.sum((dN_true - dN_predicted) ** 2)


# # --------- 累积曲线计算（新增） ----------
# def compute_cumulative(df, new_dev_pred):
#     """
#     通过累加日新增预测值，计算累积开发者数量（S曲线）。
    
#     注意：需要从第一个真实累积值开始累加。
#     """
#     N0 = df[CUM_COL].iloc[0]
#     # 使用 np.cumsum 进行累加，并加上初始值
#     cum_pred = N0 + np.cumsum(new_dev_pred)
#     # 累加的第一个值是 N0 + dN[0]，但我们希望第一个预测值就是 N0
#     # 由于 dN_pred[0] 已经包含在 cumsum 中，通常会略有误差，但这里我们相信 dN_pred
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     # 将 alpha 的边界放大，以便更好地探索
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9 * m_guess, 20 * m_guess)]
#     res = minimize(objective, init, args=(df, price_func), bounds=bounds, method="L-BFGS-B")
#     return res

# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     # === ✅ Step 1: 7日滑动平均（平滑噪声） ===
#     df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()

#     # === ✅ Step 2: 滞后网格 (Lag Grid Search) ===
#     lag_days = [0, 5, 14, 30, 60]
#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     summary_results = []  # 存放每个模型的最优结果
#     full_records = []     # 存放所有滞后 Δ 的结果（用于 CSV 输出）
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")

#         best_rmse = np.inf
#         best_res = None
#         best_lag = None

#         # === 针对每个滞后 Δ 单独拟合 ===
#         for lag in lag_days:
#             df_lag = df.copy()
#             df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#             df_lag = df_lag.dropna().reset_index(drop=True)

#             res = fit_bass(df_lag, func)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 continue

#             p0, alpha, q, m = res.x
#             dN_predicted, _ = compute_prediction(df_lag, res.x, func)
#             rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#             # 保存每个滞后的结果
#             full_records.append({
#                 "model": name,
#                 "lag_days": lag,
#                 "p0": p0,
#                 "alpha": alpha,
#                 "q": q,
#                 "m": m,
#                 "RMSE": rmse
#             })

#             print(f"Δ={lag:>2} 天 | p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#             if rmse < best_rmse:
#                 best_rmse = rmse
#                 best_res = res
#                 best_lag = lag

#         if best_res is None:
#             print(f"⚠️ 模型 {name} 拟合失败。")
#             continue

#         p0, alpha, q, m = best_res.x
#         print(f"✅ 模型 {name} 最佳滞后 Δ={best_lag} 天 | p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={best_rmse:.3f}")

#         # --- 生成预测 ---
#         dN_predicted, _ = compute_prediction(df, best_res.x, func)
#         cum_predicted = compute_cumulative(df, dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         # --- 保存最优结果 ---
#         summary_results.append({
#             "model": name,
#             "best_lag": best_lag,
#             "p0": p0,
#             "alpha": alpha,
#             "q": q,
#             "m": m,
#             "RMSE": best_rmse
#         })
#         valid_models.append(name)

#     # === 保存结果 ===
#     if summary_results:
#         # 保存每个滞后Δ的完整搜索结果
#         full_df = pd.DataFrame(full_records)
#         summary_df = pd.DataFrame(summary_results)

#         # 标记最佳滞后（方便论文表格用）
#         best_flags = []
#         for _, row in full_df.iterrows():
#             best_flag = ""
#             for sm in summary_results:
#                 if sm["model"] == row["model"] and sm["best_lag"] == row["lag_days"]:
#                     best_flag = "⭐"
#             best_flags.append(best_flag)
#         full_df["best_flag"] = best_flags

#         # 输出两个文件
#         full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         summary_df.to_csv(OUTPUT_CSV, index=False)

#         print(f"\n✅ 详细结果已保存：")
#         print(f"  - 最优结果表：{OUTPUT_CSV}")
#         print(f"  - 全滞后搜索表：{OUTPUT_CSV.replace('.csv', '_full.csv')}")
#     else:
#         print("❌ 无有效模型结果，退出。")
#         return

#     # === 绘图 ===
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日滑动平均 (真实新增)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("ETH 新增开发者数 (dN/dt)")
#     plt.title("ETH 开发者 Bass 模型新增数量拟合对比（含7日平滑 + 滞后搜索）")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("ETH 累积开发者数 N(t)")
#     plt.title("ETH 开发者 Bass 模型累积数量对比（含7日平滑 + 滞后搜索）")
#     plt.legend()
#     plt.grid(True, linestyle="--")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积 S 曲线图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()

# if __name__ == "__main__":
#     main()


# =============================================================
# 在上面代码基础上加入了参数显著性检验
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bass 模型拟合 + 平滑 + 滞后搜索 + 参数显著性检验
"""
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev_pinghua+zhihou.png"
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev_pinghua+zhihou.png"
# OUTPUT_CSV = "btc_bass_pricefit_results_pinghua+zhihou.csv"
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
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market

# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# def price_identity(price):
#     return normalize(price)

# def price_log(price):
#     val = np.log(np.maximum(price, 1e-8))
#     return normalize(val)

# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return normalize(pct)

# def compute_prediction(df, params, price_func):
#     p0, alpha, q, m = params
#     price = df[PRICE_COL].values
#     p_input = price_func(price)
#     p_t = np.maximum(p0 + alpha * p_input, 0)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m), p_t

# def objective(params, df, price_func):
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _ = compute_prediction(df, params, price_func)
#     dN_true = df["smooth_new"].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
#     return np.sum((dN_true - dN_predicted) ** 2)

# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# # --------- 参数显著性检验 ----------
# def parameter_significance(df, params, price_func):
#     """计算参数标准误、t值、p值"""
#     eps = 1e-6
#     y_pred, _ = compute_prediction(df, params, price_func)
#     y_true = df["smooth_new"].values
#     residuals = y_true - y_pred
#     n = len(df)
#     k = len(params)
#     sigma2 = np.sum(residuals**2) / (n - k)

#     # 数值近似雅可比矩阵 J
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, price_func)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k, k), np.nan)
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     return se, tvals, pvals


# # --------- 模型拟合 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9 * m_guess, 20 * m_guess)]
#     res = minimize(objective, init, args=(df, price_func), bounds=bounds, method="L-BFGS-B")
#     return res


# # --------- 主函数 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()

#     lag_days = [0, 5, 14, 30, 60]
#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     summary_results = []
#     full_records = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")

#         best_rmse = np.inf
#         best_res, best_lag = None, None

#         for lag in lag_days:
#             df_lag = df.copy()
#             df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#             df_lag = df_lag.dropna().reset_index(drop=True)

#             res = fit_bass(df_lag, func)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 continue

#             p0, alpha, q, m = res.x
#             dN_predicted, _ = compute_prediction(df_lag, res.x, func)
#             rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#             full_records.append({
#                 "model": name, "lag_days": lag,
#                 "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": rmse
#             })

#             print(f"Δ={lag:>2}天 | p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#             if rmse < best_rmse:
#                 best_rmse, best_res, best_lag = rmse, res, lag

#         if best_res is None:
#             print(f"⚠️ 模型 {name} 拟合失败。")
#             continue

#         p0, alpha, q, m = best_res.x
#         se, tvals, pvals = parameter_significance(df, best_res.x, func)

#         print(f"✅ 模型 {name} 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")
#         print("--- 参数显著性 ---")
#         for nm, v, s, t_, p_ in zip(["p0", "alpha", "q", "m"], best_res.x, se, tvals, pvals):
#             print(f"{nm:6s}: {v:10.6f} | SE={s:10.6f} | t={t_:8.3f} | p={p_:8.4f}")

#         dN_predicted, _ = compute_prediction(df, best_res.x, func)
#         cum_predicted = compute_cumulative(df, dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         summary_results.append({
#             "model": name, "best_lag": best_lag,
#             "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": best_rmse,
#             "SE_p0": se[0], "t_p0": tvals[0], "p_p0": pvals[0],
#             "SE_alpha": se[1], "t_alpha": tvals[1], "p_alpha": pvals[1],
#             "SE_q": se[2], "t_q": tvals[2], "p_q": pvals[2],
#             "SE_m": se[3], "t_m": tvals[3], "p_m": pvals[3],
#         })
#         valid_models.append(name)

#     if summary_results:
#         pd.DataFrame(summary_results).to_csv(OUTPUT_CSV, index=False)
#         pd.DataFrame(full_records).to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         print(f"\n✅ 拟合结果 + 显著性检验已保存：\n  - {OUTPUT_CSV}\n  - {OUTPUT_CSV.replace('.csv', '_full.csv')}")
#     else:
#         print("❌ 无有效模型结果，退出。")
#         return

#     # 绘图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend()
#     plt.xlabel("日期"); plt.ylabel("ETH 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增开发者（含显著性检验）")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测 N(t) ({name})")
#     plt.legend()
#     plt.xlabel("日期"); plt.ylabel("累积开发者 N(t)")
#     plt.title("BTC Bass 模型累积开发者（含显著性检验）")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()

# ======================
# 讲minimize改成least_squares优化
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
START_DATE = "2016-03-10"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev_ls.png"
OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev_ls.png"
OUTPUT_CSV = "eth_bass_pricefit_results_ls.csv"
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
def dN_pred(N, p_t, q, m):
    remaining_market = np.maximum(m - N, 0)
    return (p_t + q * (N / m)) * remaining_market

def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)

def price_identity(price):
    return normalize(price)

def price_log(price):
    val = np.log(np.maximum(price, 1e-8))
    return normalize(val)

def price_pct(price):
    lag = np.roll(price, 1)
    lag[0] = price[0]
    pct = (price - lag) / np.where(lag == 0, 1, lag)
    return normalize(pct)

def compute_prediction(df, params, price_func):
    p0, alpha, q, m = params
    price = df[PRICE_COL].values
    p_input = price_func(price)
    p_t = np.maximum(p0 + alpha * p_input, 0)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q, m), p_t

# --------- 残差与目标函数 ----------
def residuals(params, df, price_func):
    """用于 least_squares 的残差函数"""
    p0, alpha, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.full(len(df), 1e6)
    dN_predicted, _ = compute_prediction(df, params, price_func)
    dN_true = df["smooth_new"].values
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.full(len(df), 1e6)
    return dN_true - dN_predicted

def compute_cumulative(df, new_dev_pred):
    N0 = df[CUM_COL].iloc[0]
    return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)

# --------- 参数显著性检验 ----------
def parameter_significance(df, params, price_func):
    """计算参数标准误、t值、p值 + Hessian 条件数"""
    eps = 1e-6
    y_pred, _ = compute_prediction(df, params, price_func)
    y_true = df["smooth_new"].values
    residuals_ = y_true - y_pred
    n = len(df)
    k = len(params)
    sigma2 = np.sum(residuals_**2) / (n - k)

    # 数值近似雅可比矩阵 J
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _ = compute_prediction(df, params_eps, price_func)
        grad_i = (y_pred_eps - y_pred) / eps
        J.append(grad_i)
    J = np.array(J).T  # n×k

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
        cond = np.linalg.cond(J.T @ J)
    except np.linalg.LinAlgError:
        cov = np.full((k, k), np.nan)
        se = np.full(k, np.nan)
        cond = np.nan

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
    return se, tvals, pvals, cond

# --------- 模型拟合 ----------
def fit_bass(df, price_func):
    """使用最小二乘优化 Bass 模型参数"""
    m_guess = 1.2 * df[CUM_COL].max()
    init = [1e-4, 0.01, 0.01, m_guess]
    bounds = ([0, -10, 0, 0.9 * m_guess], [1, 10, 1, 20 * m_guess])
    res = least_squares(
        residuals, init, args=(df, price_func),
        bounds=bounds, method="trf", loss="linear", jac="2-point"
    )
    return res

# --------- 主函数 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)
    df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()

    lag_days = [0, 5, 14, 30, 60]
    models = {
        "linear_price": price_identity,
        "log_price": price_log,
        "pct_change_price": price_pct
    }

    summary_results = []
    full_records = []
    valid_models = []

    for name, func in models.items():
        print(f"\n=== 拟合模型：{name} ===")

        best_rmse = np.inf
        best_res, best_lag = None, None

        for lag in lag_days:
            df_lag = df.copy()
            df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
            df_lag = df_lag.dropna().reset_index(drop=True)

            res = fit_bass(df_lag, func)
            if (not res.success) or np.any(np.isnan(res.x)):
                continue

            p0, alpha, q, m = res.x
            rmse = np.sqrt(np.mean(res.fun ** 2))

            full_records.append({
                "model": name, "lag_days": lag,
                "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": rmse
            })

            print(f"Δ={lag:>2}天 | p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

            if rmse < best_rmse:
                best_rmse, best_res, best_lag = rmse, res, lag

        if best_res is None:
            print(f"⚠️ 模型 {name} 拟合失败。")
            continue

        p0, alpha, q, m = best_res.x
        se, tvals, pvals, cond = parameter_significance(df, best_res.x, func)

        print(f"⚙️ Hessian 条件数 cond={cond:.2e}")
        print(f"✅ 模型 {name} 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")
        print("--- 参数显著性 ---")
        for nm, v, s, t_, p_ in zip(["p0", "alpha", "q", "m"], best_res.x, se, tvals, pvals):
            print(f"{nm:6s}: {v:10.6f} | SE={s:10.6f} | t={t_:8.3f} | p={p_:8.6f}")

        dN_predicted, _ = compute_prediction(df, best_res.x, func)
        cum_predicted = compute_cumulative(df, dN_predicted)
        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_predicted

        summary_results.append({
            "model": name, "best_lag": best_lag,
            "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": best_rmse,
            "cond": cond,
            "SE_p0": se[0], "t_p0": tvals[0], "p_p0": pvals[0],
            "SE_alpha": se[1], "t_alpha": tvals[1], "p_alpha": pvals[1],
            "SE_q": se[2], "t_q": tvals[2], "p_q": pvals[2],
            "SE_m": se[3], "t_m": tvals[3], "p_m": pvals[3],
        })
        valid_models.append(name)

    if summary_results:
        pd.DataFrame(summary_results).to_csv(OUTPUT_CSV, index=False)
        pd.DataFrame(full_records).to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
        print(f"\n✅ 拟合结果 + 显著性检验已保存：\n  - {OUTPUT_CSV}\n  - {OUTPUT_CSV.replace('.csv', '_full.csv')}")
    else:
        print("❌ 无有效模型结果，退出。")
        return

    # 绘图
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
    plt.legend()
    plt.xlabel("日期"); plt.ylabel("ETH 新增开发者数 dN/dt")
    plt.title("ETH Bass 模型新增开发者（least squares 拟合）")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实 N(t)", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测 N(t) ({name})")
    plt.legend()
    plt.xlabel("日期"); plt.ylabel("ETH 累积开发者 N(t)")
    plt.title("ETH Bass 模型累积开发者（least squares 拟合）")
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")
    plt.show()


if __name__ == "__main__":
    main()

# =============================================================
# 在上面代码基础上将目标函数改成平滑后的累积数N(t)

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev_pinghua+zhihou.png"
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev_pinghua+zhihou.png"
# OUTPUT_CSV = "btc_bass_pricefit_results_pinghua+zhihou.csv"
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
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market

# def normalize(x):
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# def price_identity(price):
#     return normalize(price)

# def price_log(price):
#     val = np.log(np.maximum(price, 1e-8))
#     return normalize(val)

# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     return normalize(pct)

# def compute_prediction(df, params, price_func):
#     p0, alpha, q, m = params
#     price = df[PRICE_COL].values
#     p_input = price_func(price)
#     p_t = np.maximum(p0 + alpha * p_input, 0)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m), p_t

# def objective(params, df, price_func):
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _ = compute_prediction(df, params, price_func)
#     N_pred = compute_cumulative(df, dN_predicted)
#     N_true = df["smooth_cum"].values
#     if np.any(np.isnan(N_pred)):
#         return 1e12
#     return np.sum((N_true - N_pred) ** 2)

# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# # --------- 参数显著性检验 ----------
# def parameter_significance(df, params, price_func):
#     """计算参数标准误、t值、p值"""
#     eps = 1e-6
#     dN_pred, _ = compute_prediction(df, params, price_func)
#     y_pred = compute_cumulative(df, dN_pred)
#     y_true = df["smooth_cum"].values
#     residuals = y_true - y_pred
#     n = len(df)
#     k = len(params)
#     sigma2 = np.sum(residuals**2) / (n - k)

#     # 数值近似雅可比矩阵 J
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         dN_pred_eps, _ = compute_prediction(df, params_eps, price_func)
#         y_pred_eps = compute_cumulative(df, dN_pred_eps)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k, k), np.nan)
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     return se, tvals, pvals


# # --------- 模型拟合 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9 * m_guess, 20 * m_guess)]
#     res = minimize(objective, init, args=(df, price_func), bounds=bounds, method="L-BFGS-B")
#     return res


# # --------- 主函数 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     df["smooth_new"] = df[NEW_COL].rolling(window=7, center=True, min_periods=1).mean()
#     df["smooth_cum"] = df[CUM_COL].rolling(window=7, center=True, min_periods=1).mean()

#     lag_days = [0, 5, 14, 30, 60]
#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     summary_results = []
#     full_records = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")

#         best_rmse = np.inf
#         best_res, best_lag = None, None

#         for lag in lag_days:
#             df_lag = df.copy()
#             df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#             df_lag = df_lag.dropna().reset_index(drop=True)

#             res = fit_bass(df_lag, func)
#             if (not res.success) or np.any(np.isnan(res.x)):
#                 continue

#             p0, alpha, q, m = res.x
#             dN_predicted, _ = compute_prediction(df_lag, res.x, func)
#             cum_predicted = compute_cumulative(df_lag, dN_predicted)
#             rmse = np.sqrt(np.mean((df_lag["smooth_cum"].values - cum_predicted) ** 2))

#             full_records.append({
#                 "model": name, "lag_days": lag,
#                 "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": rmse
#             })

#             print(f"Δ={lag:>2}天 | p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#             if rmse < best_rmse:
#                 best_rmse, best_res, best_lag = rmse, res, lag

#         if best_res is None:
#             print(f"⚠️ 模型 {name} 拟合失败。")
#             continue

#         p0, alpha, q, m = best_res.x
#         se, tvals, pvals = parameter_significance(df, best_res.x, func)

#         print(f"✅ 模型 {name} 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")
#         print("--- 参数显著性 ---")
#         for nm, v, s, t_, p_ in zip(["p0", "alpha", "q", "m"], best_res.x, se, tvals, pvals):
#             print(f"{nm:6s}: {v:10.6f} | SE={s:10.6f} | t={t_:8.3f} | p={p_:8.4f}")

#         dN_predicted, _ = compute_prediction(df, best_res.x, func)
#         cum_predicted = compute_cumulative(df, dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         summary_results.append({
#             "model": name, "best_lag": best_lag,
#             "p0": p0, "alpha": alpha, "q": q, "m": m, "RMSE": best_rmse,
#             "SE_p0": se[0], "t_p0": tvals[0], "p_p0": pvals[0],
#             "SE_alpha": se[1], "t_alpha": tvals[1], "p_alpha": pvals[1],
#             "SE_q": se[2], "t_q": tvals[2], "p_q": pvals[2],
#             "SE_m": se[3], "t_m": tvals[3], "p_m": pvals[3],
#         })
#         valid_models.append(name)

#     if summary_results:
#         pd.DataFrame(summary_results).to_csv(OUTPUT_CSV, index=False)
#         pd.DataFrame(full_records).to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         print(f"\n✅ 拟合结果 + 显著性检验已保存：\n  - {OUTPUT_CSV}\n  - {OUTPUT_CSV.replace('.csv', '_full.csv')}")
#     else:
#         print("❌ 无有效模型结果，退出。")
#         return

#     # 绘图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend()
#     plt.xlabel("日期"); plt.ylabel("ETH 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增开发者（含显著性检验）")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_cum"], label="7日平滑真实 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测 N(t) ({name})")
#     plt.legend()
#     plt.xlabel("日期"); plt.ylabel("累积开发者 N(t)")
#     plt.title("BTC Bass 模型累积开发者（含显著性检验）")
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()