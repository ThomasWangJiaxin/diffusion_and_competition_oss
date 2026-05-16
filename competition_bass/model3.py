# =====================================
# ✅ 在原代码基础上加入 m(t) 动态函数 (加法/乘法/指数)
# 仅对开发者带平滑（没有对价格平滑）+滞后目前同时作用于𝑝(𝑡)与𝑚(𝑡)
# =====================================

# ============================================================
# ✅ Bass Diffusion with Dynamic m(t) (Linear / Multiplicative / Exponential)
# ============================================================

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev_m_dynamic.png"
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev_m_dynamic.png"
# OUTPUT_CSV = "eth_bass_pricefit_results_m_dynamic.csv"
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


# # --------- 工具函数 ----------
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


# # --------- Bass 模型 ----------
# def dN_pred(N, p_t, q, m_t):
#     remaining_market = np.maximum(m_t - N, 0)
#     return (p_t + q * (N / m_t)) * remaining_market


# def compute_prediction(df, params, price_func, m_type="additive"):
#     p0, alpha, q, m_base, m_beta = params
#     price = df[PRICE_COL].values
#     price_input = price_func(price)

#     # --- p(t) ---
#     p_t = np.maximum(p0 + alpha * price_input, 0)

#     # --- m(t) ---
#     if m_type == "additive":
#         m_t = m_base + m_beta * price_input
#     elif m_type == "multiplicative":
#         m_t = m_base * (1 + m_beta * price_input)
#     elif m_type == "exponential":
#         m_t = m_base * np.exp(m_beta * price_input)
#     else:
#         raise ValueError(f"未知 m_type: {m_type}")

#     m_t = np.maximum(m_t, df[CUM_COL].max() * 1.01)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m_t), p_t, m_t


# def objective(params, df, price_func, m_type):
#     p0, alpha, q, m_base, m_beta = params
#     if m_base <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, m_type)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
#     return np.sum((dN_true - dN_predicted) ** 2)


# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# def fit_bass(df, price_func, m_type="additive"):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess, 0.01]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9*m_guess, 20*m_guess), (-2, 2)]
#     res = minimize(objective, init, args=(df, price_func, m_type), bounds=bounds, method="L-BFGS-B")
#     return res


# # --------- 主程序 ----------
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
#     m_types = ["additive", "multiplicative", "exponential"]

#     summary_results, full_records, valid_models = [], [], []

#     for name, func in models.items():
#         for m_type in m_types:
#             print(f"\n=== 拟合模型：{name} | m(t): {m_type} ===")
#             best_rmse, best_res, best_lag = np.inf, None, None

#             for lag in lag_days:
#                 df_lag = df.copy()
#                 df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#                 df_lag = df_lag.dropna().reset_index(drop=True)

#                 res = fit_bass(df_lag, func, m_type)
#                 if (not res.success) or np.any(np.isnan(res.x)):
#                     continue

#                 p0, alpha, q, m_base, m_beta = res.x
#                 dN_predicted, _, m_t = compute_prediction(df_lag, res.x, func, m_type)
#                 rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#                 full_records.append({
#                     "model": name,
#                     "m_type": m_type,
#                     "lag_days": lag,
#                     "p0": p0, "alpha": alpha, "q": q,
#                     "m_base": m_base, "m_beta": m_beta,
#                     "m_mean": np.mean(m_t), "m_std": np.std(m_t), "m_max": np.max(m_t),
#                     "RMSE": rmse
#                 })

#                 print(f"Δ={lag:>2} 天 | p0={p0:.5f}, α={alpha:.5f}, q={q:.5f}, "
#                       f"m_base={m_base:.1f}, β={m_beta:.4f}, RMSE={rmse:.3f}")

#                 if rmse < best_rmse:
#                     best_rmse, best_res, best_lag = rmse, res, lag

#             if best_res is None:
#                 print(f"⚠️ 模型 {name}-{m_type} 拟合失败。")
#                 continue

#             p0, alpha, q, m_base, m_beta = best_res.x
#             print(f"✅ 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")

#             dN_predicted, _, m_t = compute_prediction(df, best_res.x, func, m_type)
#             cum_predicted = compute_cumulative(df, dN_predicted)

#             tag = f"{name}_{m_type}"
#             df[f"pred_new_{tag}"] = dN_predicted
#             df[f"pred_cum_{tag}"] = cum_predicted

#             summary_results.append({
#                 "model": name, "m_type": m_type,
#                 "best_lag": best_lag,
#                 "p0": p0, "alpha": alpha, "q": q,
#                 "m_base": m_base, "m_beta": m_beta,
#                 "m_mean": np.mean(m_t), "m_std": np.std(m_t), "m_max": np.max(m_t),
#                 "RMSE": best_rmse
#             })
#             valid_models.append(tag)

#     # === 保存结果 ===
#     if summary_results:
#         full_df = pd.DataFrame(full_records)
#         summary_df = pd.DataFrame(summary_results)

#         # 修复后的最佳标记逻辑 ✅
#         best_flags = []
#         for _, row in full_df.iterrows():
#             best_flag = ""
#             for sm in summary_results:
#                 if sm["model"] == row["model"] and sm["m_type"] == row["m_type"] and sm["best_lag"] == row["lag_days"]:
#                     best_flag = "⭐"
#             best_flags.append(best_flag)
#         full_df["best_flag"] = best_flags

#         full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         summary_df.to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 结果已保存：\n - {OUTPUT_CSV}\n - {OUTPUT_CSV.replace('.csv', '_full.csv')}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # === 绘图 ===
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{tag}"], "--", label=f"预测新增 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("新增开发者数 dN/dt")
#     plt.title("ETH 开发者 Bass 模型新增数量（动态 m(t)）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{tag}"], "--", label=f"预测累积 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("累积开发者数 N(t)")
#     plt.title("ETH 开发者 Bass 模型累积数量（动态 m(t)）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()

# =====================================================================
# ✅ 在原代码基础上加入参数显著性检验 (数值微分法估计标准误)
# 但使用的是数值微分 + 雅可比矩阵 J 估计协方差，更稳定，但计算量大。适合非线性模型。
# res = minimize(objective, …)，目标函数基于平滑后的真实值(df["smooth_new"])
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# from scipy.stats import t as t_dist # 用于计算 p 值
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers" # 当前拟合 ETH
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# # --- 搜索参数 ---
# ROLLING_WINDOW = 7  # 7日滑动平均窗口
# LAG_DAYS = [0, 5, 14, 30, 60] # 滞后天数网格
# # ----------------

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev_m_dynamic_sig.png" 
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev_m_dynamic_sig.png" 
# OUTPUT_CSV = "btc_bass_pricefit_results_m_dynamic_sig.csv"
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


# # --------- 核心工具函数 ----------
# def normalize(x):
#     """Z-Score 标准化"""
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

# # 将字符串映射到实际函数
# FUNC_MAP = {
#     "linear_price": price_identity,
#     "log_price": price_log,
#     "pct_change_price": price_pct
# }


# # --------- Bass 模型 (动态 m(t)) ----------
# def dN_pred(N, p_t, q, m_t):
#     """Bass 模型日新增预测值"""
#     remaining_market = np.maximum(m_t - N, 0)
#     # p(t) 是 [p_t]
#     return (p_t + q * (N / m_t)) * remaining_market


# def compute_prediction(df, params, price_func, m_type="additive"):
#     """计算 dN/dt 预测值 和 动态 p(t), m(t)"""
#     # 5 个参数: [p0, alpha, q, m_base, m_beta]
#     p0, alpha, q, m_base, m_beta = params
    
#     # 价格特征 V(t)
#     price_input = price_func(df[PRICE_COL].values)

#     # --- p(t) ---
#     p_t = np.maximum(p0 + alpha * price_input, 0)

#     # --- m(t) ---
#     if m_type == "additive":
#         m_t = m_base + m_beta * price_input
#     elif m_type == "multiplicative":
#         m_t = m_base * (1 + m_beta * price_input)
#     elif m_type == "exponential":
#         m_t = m_base * np.exp(m_beta * price_input)
#     else:
#         raise ValueError(f"未知 m_type: {m_type}")

#     # 确保 m(t) 始终大于当前累积用户数（或一个安全界限）
#     m_t = np.maximum(m_t, df[CUM_COL].max() * 1.01)
    
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m_t), p_t, m_t


# def objective(params, df, price_func, m_type):
#     """拟合目标函数：最小化平滑后的 dN/dt 残差平方和"""
#     p0, alpha, q, m_base, m_beta = params
#     # 严格的边界约束 (m_base 必须大于当前最大累积数, p0, q 必须非负)
#     if m_base <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
        
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, m_type)
#     dN_true = df["smooth_new"].values
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
        
#     return np.sum((dN_true - dN_predicted) ** 2)


# def compute_cumulative(df, new_dev_pred):
#     """通过累加 dN/dt 预测值，计算累积预测 N(t)"""
#     N0 = df[CUM_COL].iloc[0]
#     # N(t) = N0 + 积分(dN/dt)dt
#     # np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0) 确保长度和 N(t) 一致
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# def fit_bass(df, price_func, m_type="additive"):
#     """调用 scipy.optimize.minimize 进行拟合"""
#     m_guess = 1.2 * df[CUM_COL].max()
#     # 5 个参数的初始值: [p0, alpha, q, m_base, m_beta]
#     init = [1e-4, 0.01, 0.01, m_guess, 0.01]
#     # 边界: alpha 和 m_beta 可以为负
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9*m_guess, 20*m_guess), (-2, 2)]
#     res = minimize(objective, init, args=(df, price_func, m_type), bounds=bounds, method="L-BFGS-B")
#     return res


# # --------- 统计显著性检验函数（针对 5 个参数）----------
# def parameter_significance(df, params, price_func, m_type):
#     """
#     计算参数标准误、t值、p值。适用于 5 个参数: [p0, alpha, q, m_base, m_beta]
#     """
#     eps = 1e-6 # 数值微分步长
    
#     # 核心目标值和残差
#     y_pred, _, _ = compute_prediction(df, params, price_func, m_type)
#     y_true = df["smooth_new"].values
#     residuals = y_true - y_pred
    
#     n = len(df)
#     k = len(params) # k=5
    
#     # 估计残差方差：sigma^2
#     sigma2 = np.sum(residuals**2) / (n - k)

#     # 1. 数值近似雅可比矩阵 J (n x k)
#     J = []
#     for i in range(k):
#         params_eps = list(params.copy())
#         params_eps[i] += eps # 对第 i 个参数增加微小扰动
        
#         # 重新计算预测值
#         y_pred_eps, _, _ = compute_prediction(df, params_eps, price_func, m_type)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
        
#     J = np.array(J).T  # J 的维度: (n观测值) x (k参数)

#     try:
#         # 2. 协方差矩阵 Cov = sigma^2 * (J^T * J)^-1
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov)) # 标准误差 SE
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     # 3. 计算双侧 p 值 (自由度 df = n - k)
#     pvals = 2 * (1 - t_dist.cdf(np.abs(tvals), df=n - k))
    
#     return se, tvals, pvals


# # --------- 主函数 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     df["smooth_new"] = df[NEW_COL].rolling(window=ROLLING_WINDOW, center=True, min_periods=1).mean()

#     lag_days = [0, 5, 14, 30, 60]
#     m_types = ["additive", "multiplicative", "exponential"]

#     summary_results, full_records, valid_models = [], [], []

#     for name, func in FUNC_MAP.items(): # name: linear_price, func: price_identity
#         for m_type in m_types:
#             print(f"\n=== 拟合模型：{name} | m(t): {m_type} ===")
#             best_rmse, best_res, best_lag = np.inf, None, None

#             for lag in lag_days:
#                 df_lag = df.copy()
#                 # --- 应用滞后 ---
#                 df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#                 df_lag = df_lag.dropna().reset_index(drop=True)
                
#                 # --- 拟合 ---
#                 res = fit_bass(df_lag, func, m_type)
#                 if (not res.success) or np.any(np.isnan(res.x)):
#                     continue

#                 p0, alpha, q, m_base, m_beta = res.x
#                 dN_predicted, _, m_t = compute_prediction(df_lag, res.x, func, m_type)
#                 rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#                 # --- 显著性计算 ---
#                 se, tvals, pvals = parameter_significance(df_lag, res.x, func, m_type)

#                 full_records.append({
#                     "model": name, "m_type": m_type, "lag_days": lag,
#                     "p0": p0, "alpha": alpha, "q": q, "m_base": m_base, "m_beta": m_beta,
#                     "m_mean": np.mean(m_t), "RMSE": rmse,
                    
#                     # 记录显著性结果 (参数顺序: p0, alpha, q, m_base, m_beta)
#                     "t_p0": tvals[0], "p_p0": pvals[0], "t_alpha": tvals[1], "p_alpha": pvals[1],
#                     "t_q": tvals[2], "p_q": pvals[2], "t_m_base": tvals[3], "p_m_base": pvals[3],
#                     "t_m_beta": tvals[4], "p_m_beta": pvals[4]
#                 })

#                 print(f"Δ={lag:>2}d | RMSE={rmse:.3f} | α={alpha:.5f} (p={pvals[1]:.4f}), β={m_beta:.4f} (p={pvals[4]:.4f})")

#                 if rmse < best_rmse:
#                     best_rmse, best_res, best_lag = rmse, res, lag

#             if best_res is None:
#                 continue

#             # 提取最佳结果的显著性
#             se, tvals, pvals = parameter_significance(df, best_res.x, func, m_type)
#             p0, alpha, q, m_base, m_beta = best_res.x

#             # --- 生成预测 ---
#             dN_predicted, _, m_t = compute_prediction(df, best_res.x, func, m_type)
#             cum_predicted = compute_cumulative(df, dN_predicted)

#             tag = f"{name}_{m_type}"
#             df[f"pred_new_{tag}"] = dN_predicted
#             df[f"pred_cum_{tag}"] = cum_predicted

#             summary_results.append({
#                 "model": name, "m_type": m_type, "best_lag": best_lag,
#                 "p0": p0, "alpha": alpha, "q": q, "m_base": m_base, "m_beta": m_beta,
#                 "RMSE": best_rmse, "m_mean": np.mean(m_t),
                
#                 # 记录显著性结果
#                 "t_p0": tvals[0], "p_p0": pvals[0], "t_alpha": tvals[1], "p_alpha": pvals[1],
#                 "t_q": tvals[2], "p_q": pvals[2], "t_m_base": tvals[3], "p_m_base": pvals[3],
#                 "t_m_beta": tvals[4], "p_m_beta": pvals[4]
#             })
#             valid_models.append(tag)

#     # --- 结果输出和绘图 ---
#     if summary_results:
#         full_df = pd.DataFrame(full_records)
#         summary_df = pd.DataFrame(summary_results)
        
#         # 保存详细和总结结果
#         full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         summary_df.to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果 + 显著性检验已保存至：\n  - {OUTPUT_CSV}\n  - {OUTPUT_CSV.replace('.csv', '_full.csv')}")

#         if summary_df.shape[0] > 0:
#             best_row = summary_df.loc[summary_df['RMSE'].idxmin()]
#             print("\n=======================================================")
#             print("|  🥇 最佳拟合模型 (含显著性)                          |")
#             print("=======================================================")
#             print(f"模型: {best_row['model']} | m(t): {best_row['m_type']} (滞后 {best_row['best_lag']} 天)")
#             print(f"RMSE: {best_row['RMSE']:.3f}")
#             print("--- 关键参数显著性 (P < 0.05 为显著) ---")
#             print(f"α (价格敏感): {best_row['alpha']:.6f} (t={best_row['t_alpha']:.2f}, P={best_row['p_alpha']:.4f})")
#             print(f"β (潜能敏感): {best_row['m_beta']:.4f} (t={best_row['t_m_beta']:.2f}, P={best_row['p_m_beta']:.4f})")
#             print(f"q (内部口碑): {best_row['q']:.6f} (t={best_row['t_q']:.2f}, P={best_row['p_q']:.4f})")
#             print(f"m_base (基准潜能): {best_row['m_base']:.0f} (t={best_row['t_m_base']:.2f}, P={best_row['p_m_base']:.4f})")


#     # --- 绘图 1: 新增开发者对比图 ---
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label=f"真实新增 (平滑 {ROLLING_WINDOW}日)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{tag}"], "--", label=f"预测新增 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("BTC 新增开发者数 dN/dt")
#     plt.title("BTC 开发者 Bass 模型新增数量（动态 m(t)）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)

#     # --- 绘图 2: 累积 S 曲线对比图 ---
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{tag}"], "--", label=f"预测累积 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("BTC 累积开发者数 N(t)")
#     plt.title("BTC 开发者 Bass 模型累积数量（动态 m(t)）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()

# ====================================
# 把minimize改成least square优化：
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t as t_dist
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# ROLLING_WINDOW = 0
# LAG_DAYS = [0, 5, 14, 30, 60]

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev_ls.png"
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev_ls.png"
# OUTPUT_CSV = "eth_bass_pricefit_results_ls.csv"
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

# # --------- 核心函数 ----------
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

# FUNC_MAP = {
#     "linear_price": price_identity,
#     "log_price": price_log,
#     "pct_change_price": price_pct
# }

# def dN_pred(N, p_t, q, m_t):
#     remaining_market = np.maximum(m_t - N, 0)
#     return (p_t + q * (N / m_t)) * remaining_market

# def compute_prediction(df, params, price_func, m_type="additive"):
#     p0, alpha, q, m_base, m_beta = params
#     price_input = price_func(df[PRICE_COL].values)

#     p_t = np.maximum(p0 + alpha * price_input, 0)

#     if m_type == "additive":
#         m_t = m_base + m_beta * price_input
#     elif m_type == "multiplicative":
#         m_t = m_base * (1 + m_beta * price_input)
#     elif m_type == "exponential":
#         m_t = m_base * np.exp(m_beta * price_input)
#     else:
#         raise ValueError(f"未知 m_type: {m_type}")

#     m_t = np.maximum(m_t, df[CUM_COL].max() * 1.01)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m_t), p_t, m_t

# def residuals(params, df, price_func, m_type):
#     """返回残差向量，用于 least_squares 拟合"""
#     p0, alpha, q, m_base, m_beta = params
#     if m_base <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
#     y_pred, _, _ = compute_prediction(df, params, price_func, m_type)
#     return df["smooth_new"].values - y_pred

# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)

# # --------- 拟合函数（Least Squares） ----------
# def fit_bass(df, price_func, m_type="additive"):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess, 0.01]
#     bounds = ([0, -10, 0, 0.9*m_guess, -2],
#               [1, 10, 1, 20*m_guess, 2])
#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, m_type), method="trf")
#     return res

# # --------- 显著性检验 ----------
# def parameter_significance(df, params, price_func, m_type):
#     eps = 1e-6
#     y_pred, _, _ = compute_prediction(df, params, price_func, m_type)
#     y_true = df["smooth_new"].values
#     residuals = y_true - y_pred

#     n = len(df)
#     k = len(params)
#     sigma2 = np.sum(residuals**2) / (n - k)

#     J = []
#     for i in range(k):
#         params_eps = list(params.copy())
#         params_eps[i] += eps
#         y_pred_eps, _, _ = compute_prediction(df, params_eps, price_func, m_type)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t_dist.cdf(np.abs(tvals), df=n - k))
#     return se, tvals, pvals

# # --------- 主函数 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     df["smooth_new"] = df[NEW_COL].rolling(window=ROLLING_WINDOW, center=True, min_periods=1).mean()

#     m_types = ["additive", "multiplicative", "exponential"]
#     summary_results, full_records, valid_models = [], [], []

#     for name, func in FUNC_MAP.items():
#         for m_type in m_types:
#             print(f"\n=== 拟合模型：{name} | m(t): {m_type} (least squares) ===")
#             best_rmse, best_res, best_lag = np.inf, None, None

#             for lag in LAG_DAYS:
#                 df_lag = df.copy()
#                 df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#                 df_lag = df_lag.dropna().reset_index(drop=True)

#                 res = fit_bass(df_lag, func, m_type)
#                 if (not res.success) or np.any(np.isnan(res.x)):
#                     continue

#                 dN_predicted, _, m_t = compute_prediction(df_lag, res.x, func, m_type)
#                 rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))
#                 se, tvals, pvals = parameter_significance(df_lag, res.x, func, m_type)

#                 full_records.append({
#                     "model": name, "m_type": m_type, "lag_days": lag,
#                     "p0": res.x[0], "alpha": res.x[1], "q": res.x[2],
#                     "m_base": res.x[3], "m_beta": res.x[4],
#                     "RMSE": rmse, "m_mean": np.mean(m_t),
#                     "t_p0": tvals[0], "p_p0": pvals[0],
#                     "t_alpha": tvals[1], "p_alpha": pvals[1],
#                     "t_q": tvals[2], "p_q": pvals[2],
#                     "t_m_base": tvals[3], "p_m_base": pvals[3],
#                     "t_m_beta": tvals[4], "p_m_beta": pvals[4],
#                 })

#                 print(f"Δ={lag:>2}d | RMSE={rmse:.3f} | α={res.x[1]:.5f} (p={pvals[1]:.4f}), β={res.x[4]:.4f} (p={pvals[4]:.4f})")

#                 if rmse < best_rmse:
#                     best_rmse, best_res, best_lag = rmse, res, lag

#             if best_res is None:
#                 continue

#             se, tvals, pvals = parameter_significance(df, best_res.x, func, m_type)
#             dN_predicted, _, m_t = compute_prediction(df, best_res.x, func, m_type)
#             cum_predicted = compute_cumulative(df, dN_predicted)

#             tag = f"{name}_{m_type}"
#             df[f"pred_new_{tag}"] = dN_predicted
#             df[f"pred_cum_{tag}"] = cum_predicted

#             summary_results.append({
#                 "model": name, "m_type": m_type, "best_lag": best_lag,
#                 "RMSE": best_rmse, "m_mean": np.mean(m_t),
#                 "p0": best_res.x[0], "alpha": best_res.x[1], "q": best_res.x[2],
#                 "m_base": best_res.x[3], "m_beta": best_res.x[4],
#                 "t_p0": tvals[0], "p_p0": pvals[0],
#                 "t_alpha": tvals[1], "p_alpha": pvals[1],
#                 "t_q": tvals[2], "p_q": pvals[2],
#                 "t_m_base": tvals[3], "p_m_base": pvals[3],
#                 "t_m_beta": tvals[4], "p_m_beta": pvals[4],
#             })
#             valid_models.append(tag)

#     if summary_results:
#         full_df = pd.DataFrame(full_records)
#         summary_df = pd.DataFrame(summary_results)
#         full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         summary_df.to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")

#         best_row = summary_df.loc[summary_df['RMSE'].idxmin()]
#         print("\n🥇 最佳模型：", best_row['model'], best_row['m_type'], f"(滞后 {best_row['best_lag']} 天)")
#         print(f"RMSE={best_row['RMSE']:.3f}, α={best_row['alpha']:.4f}, β={best_row['m_beta']:.4f}")

#     # --- 绘图 ---
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label=f"真实新增 (平滑 {ROLLING_WINDOW}日)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{tag}"], "--", label=f"预测新增 ({tag})")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{tag}"], "--", label=f"预测累积 ({tag})")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()

# =========
# 在上面基础上删除平滑和滞后
# 并加入参数显著性
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt
import os

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
PRICE_COL = "eth_price"
START_DATE = "2016-03-10"
END_DATE = "2024-12-31"

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
    return df

# --------- 价格函数 ----------
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

FUNC_MAP = {
    "linear_price": price_identity,
    "log_price": price_log,
    "pct_change_price": price_pct
}

# --------- 核心模型函数 ----------
def dN_pred(N, p_t, q, m_t):
    remaining_market = np.maximum(m_t - N, 0)
    return (p_t + q * (N / m_t)) * remaining_market

def compute_prediction(df, params, price_func, m_type):
    """
    根据 m_type 处理不同数量的参数，并计算 P(t) 和 M(t)。
    P(t) 在所有扇面模型中都依赖于价格。
    """
    price_input = price_func(df[PRICE_COL].values)
    N = df[CUM_COL].values
    
    if m_type == "constant":
        # 4 parameters: [p0, alpha, q, m_base]
        p0, alpha, q, m_base = params
        p_t = np.maximum(p0 + alpha * price_input, 0)
        m_t = np.full_like(N, m_base) # M(t) 是一个常数
    else:
        # 5 parameters: [p0, alpha, q, m_base, m_beta]
        p0, alpha, q, m_base, m_beta = params
        p_t = np.maximum(p0 + alpha * price_input, 0)
        
        if m_type == "additive":
            m_t = m_base + m_beta * price_input
        elif m_type == "multiplicative":
            m_t = m_base * (1 + m_beta * price_input)
        elif m_type == "exponential":
            m_t = m_base * np.exp(m_beta * price_input)
        else:
            raise ValueError(f"未知 m_type: {m_type}")

    # 确保市场规模大于当前的累积用户数
    m_t = np.maximum(m_t, df[CUM_COL].max() * 1.01)
    
    return dN_pred(N, p_t, q, m_t), p_t, m_t

def residuals(params, df, price_func, m_type):
    """根据 m_type 检查约束条件"""
    m_base_index = 3
    
    if m_type == "constant":
        m_base = params[m_base_index]
        q = params[2]
        p0 = params[0]
    else:
        m_base = params[m_base_index]
        q = params[2]
        p0 = params[0]

    # 约束：m_base 必须大于当前最大累积用户数，p0, q 必须大于等于 0
    if m_base <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
        
    y_pred, _, _ = compute_prediction(df, params, price_func, m_type)
    
    # 拟合目标是原始新增量 NEW_COL
    return df[NEW_COL].values - y_pred 

def compute_cumulative(df, new_dev_pred):
    N0 = df[CUM_COL].iloc[0]
    return N0 + np.cumsum(new_dev_pred)

# --------- 拟合函数（Least Squares） ----------
def fit_bass(df, price_func, m_type):
    m_guess = 1.2 * df[CUM_COL].max()
    
    if m_type == "constant":
        # 4 parameters: [p0, alpha, q, m_base]
        init = [1e-4, 0.01, 0.01, m_guess]
        # p0, alpha, q, m_base
        bounds = ([0, -10, -10, 0.9*m_guess], 
                  [1, 10, 1, 20*m_guess])
    else:
        # 5 parameters: [p0, alpha, q, m_base, m_beta]
        init = [1e-4, 0.01, 0.01, m_guess, 0.01]
        # p0, alpha, q, m_base, m_beta
        bounds = ([0, -10, -10, 0.9*m_guess, -2], 
                  [1, 10, 1, 20*m_guess, 2])
                  
    res = least_squares(residuals, init, bounds=bounds, args=(df, price_func, m_type), method="trf")
    return res

# --------- 显著性检验 ----------
def parameter_significance(df, params, price_func, m_type):
    eps = 1e-6
    y_pred, _, _ = compute_prediction(df, params, price_func, m_type)
    y_true = df[NEW_COL].values 
    residuals = y_true - y_pred

    n = len(df)
    k = len(params) # k 自动匹配参数数量
    sigma2 = np.sum(residuals**2) / (n - k)

    J = []
    for i in range(k):
        params_eps = list(params.copy())
        params_eps[i] += eps
        y_pred_eps, _, _ = compute_prediction(df, params_eps, price_func, m_type)
        grad_i = (y_pred_eps - y_pred) / eps
        J.append(grad_i)
    J = np.array(J).T

    try:
        cov = sigma2 * np.linalg.pinv(J.T @ J) 
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t_dist.cdf(np.abs(tvals), df=n - k))
    return se, tvals, pvals

# --------- 打印参数显著性函数 (包含 RMSE) ----------
def print_parameter_table(model_tag, rmse, params, se, tvals, pvals, param_names):
    """打印格式化的 RMSE、参数估计值、SE、t值和p值"""
    
    print(f"\n--- {model_tag} 结果 ---")
    print(f"拟合指标：RMSE = {rmse:.4f}") 
    print("---------------------------------------------------")
    # 调整列宽以适应不同的参数数量
    print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
    print("---------------------------------------------------")

    for name, val, s, tval, pval in zip(param_names, params, se, tvals, pvals):
        # 突出显示显著参数 
        marker = ""
        if pval < 0.01:
            marker = " ***"
        elif pval < 0.05:
            marker = " **"
        elif pval < 0.10:
            marker = " *"
            
        print(f"{name:<10}{val:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}{marker}")
    print("---------------------------------------------------\n")

# --------- 主函数 (已修改) ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    df["smooth_new"] = df[NEW_COL] 

    # 包含新增的 constant 类型
    m_types_variable = ["additive", "multiplicative", "exponential"]
    m_types_all = m_types_variable + ["constant"]
    
    summary_results, full_records, valid_models = [], [], []
    df_lag = df.copy() 
    
    # 定义不同模型的参数名称列表
    param_names_variable_M = ["p0", "alpha", "q", "m_base", "m_beta"]
    param_names_constant_M = ["p0", "alpha", "q", "m_base"]
    
    # 循环拟合所有 Price Function 和 m(t) Type
    for name, func in FUNC_MAP.items():
        for m_type in m_types_all:
            model_tag = f"{name} | M(t): {m_type}"
            print(f"\n=== 拟合模型：{model_tag} ===")
            
            res = fit_bass(df_lag, func, m_type)

            if (not res.success) or np.any(np.isnan(res.x)):
                print(f"⚠️ {model_tag} 优化失败或参数异常")
                continue

            params = res.x
            dN_predicted, _, m_t = compute_prediction(df_lag, params, func, m_type)
            rmse = np.sqrt(np.mean((df_lag[NEW_COL].values - dN_predicted) ** 2)) 
            se, tvals, pvals = parameter_significance(df_lag, params, func, m_type)

            # 根据模型类型选择参数名称列表
            current_param_names = param_names_constant_M if m_type == "constant" else param_names_variable_M
            
            # 打印参数显著性表 (包含 RMSE)
            print_parameter_table(model_tag, rmse, params, se, tvals, pvals, current_param_names)
            
            # 准备记录结果
            record = {
                "model": name, "m_type": m_type, "lag_days": 0,
                "RMSE": rmse, "m_mean": np.mean(m_t),
            }
            # 动态添加参数和显著性结果
            for i, p_name in enumerate(current_param_names):
                record[p_name] = params[i]
                record[f"t_{p_name}"] = tvals[i]
                record[f"p_{p_name}"] = pvals[i]
                
            # 确保 5 参数模型中的 m_beta 字段也被记录（即使 constant 模型中没有）
            if m_type != "constant":
                record["m_beta"] = params[4]
                record["t_m_beta"] = tvals[4]
                record["p_m_beta"] = pvals[4]
            else:
                # 为 constant 模型设置缺失参数的默认值
                record["m_beta"] = np.nan 
                record["t_m_beta"] = np.nan
                record["p_m_beta"] = np.nan

            full_records.append(record)
            summary_results.append(record)
            
            # 准备绘图数据
            tag = f"{name}_{m_type}"
            cum_predicted = compute_cumulative(df_lag, dN_predicted)
            
            df[f"pred_new_{tag}"] = dN_predicted
            df[f"pred_cum_{tag}"] = cum_predicted
            valid_models.append(tag)


    if summary_results:
        # 统一 DataFrame 列名
        column_order = (["model", "m_type", "lag_days", "RMSE", "m_mean"] + 
                        ["p0", "alpha", "q", "m_base", "m_beta"] +
                        [f"t_{p}" for p in ["p0", "alpha", "q", "m_base", "m_beta"]] +
                        [f"p_{p}" for p in ["p0", "alpha", "q", "m_base", "m_beta"]])

        full_df = pd.DataFrame(full_records).reindex(columns=column_order)
        summary_df = pd.DataFrame(summary_results).reindex(columns=column_order)
        
        full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
        summary_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ 拟合结果总结保存至 {OUTPUT_CSV}")

        # 打印最佳模型总结
        best_row = summary_df.loc[summary_df['RMSE'].idxmin()]
        print("\n🥇 最佳模型总结 🥇")
        print(f"模型：{best_row['model']} | M(t): {best_row['m_type']}")
        print(f"**RMSE={best_row['RMSE']:.4f}**")
        print(f"参数: p0={best_row['p0']:.4f}, alpha={best_row['alpha']:.4f}, q={best_row['q']:.4f}, m_base={best_row['m_base']:.4f}")
        if best_row['m_type'] != 'constant':
            print(f"m_beta={best_row['m_beta']:.4f}")


    # --- 绘图 ---
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2) 
    for tag in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{tag}"], "--", label=f"预测新增 ({tag})")
    plt.title("新增开发者预测"); plt.xlabel("日期"); plt.ylabel("数量")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
    for tag in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{tag}"], "--", label=f"预测累积 ({tag})")
    plt.title("累积开发者预测"); plt.xlabel("日期"); plt.ylabel("数量")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

if __name__ == "__main__":
    main()


# =====================================================================
# ✅ 在原代码基础上加入参数显著性检验 
# 但使用的是L-BFGS-B 内部 Hessian 近似求协方差，计算快但近似粗糙。L-BFGS-B 的 hess_inv 是近似逆，不等价于真实 Hessian。可能导致 t/p 值偏差。
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
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev_m_dynamic_ttest.png"
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev_m_dynamic_ttest.png"
# OUTPUT_CSV = "eth_bass_pricefit_results_m_dynamic_ttest.csv"
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


# # --------- 工具函数 ----------
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


# # --------- Bass 模型 ----------
# def dN_pred(N, p_t, q, m_t):
#     remaining_market = np.maximum(m_t - N, 0)
#     return (p_t + q * (N / m_t)) * remaining_market


# def compute_prediction(df, params, price_func, m_type="additive"):
#     p0, alpha, q, m_base, m_beta = params
#     price = df[PRICE_COL].values
#     price_input = price_func(price)

#     # --- p(t) ---
#     p_t = np.maximum(p0 + alpha * price_input, 0)

#     # --- m(t) ---
#     if m_type == "additive":
#         m_t = m_base + m_beta * price_input
#     elif m_type == "multiplicative":
#         m_t = m_base * (1 + m_beta * price_input)
#     elif m_type == "exponential":
#         m_t = m_base * np.exp(m_beta * price_input)
#     else:
#         raise ValueError(f"未知 m_type: {m_type}")

#     m_t = np.maximum(m_t, df[CUM_COL].max() * 1.01)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m_t), p_t, m_t


# def objective(params, df, price_func, m_type):
#     p0, alpha, q, m_base, m_beta = params
#     if m_base <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _, _ = compute_prediction(df, params, price_func, m_type)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
#     return np.sum((dN_true - dN_predicted) ** 2)


# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# def fit_bass(df, price_func, m_type="additive"):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess, 0.01]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9*m_guess, 20*m_guess), (-2, 2)]
#     res = minimize(objective, init, args=(df, price_func, m_type), bounds=bounds, method="L-BFGS-B")

#     # ===== 计算参数显著性 (t / p 值) =====
#     t_vals, p_vals = [np.nan]*len(res.x), [np.nan]*len(res.x)
#     if hasattr(res, 'hess_inv') and not isinstance(res.hess_inv, float):
#         try:
#             cov_matrix = res.hess_inv.todense() if hasattr(res.hess_inv, 'todense') else res.hess_inv
#             se = np.sqrt(np.diag(cov_matrix))
#             t_vals = res.x / se
#             df_resid = len(df) - len(res.x)
#             p_vals = 2 * (1 - t.cdf(np.abs(t_vals), df=df_resid))
#         except Exception as e:
#             print(f"⚠️ Hessian 无法计算显著性: {e}")
#     return res, t_vals, p_vals


# # --------- 主程序 ----------
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
#     m_types = ["additive", "multiplicative", "exponential"]

#     summary_results, full_records, valid_models = [], [], []

#     for name, func in models.items():
#         for m_type in m_types:
#             print(f"\n=== 拟合模型：{name} | m(t): {m_type} ===")
#             best_rmse, best_res, best_lag = np.inf, None, None
#             best_t, best_p = None, None

#             for lag in lag_days:
#                 df_lag = df.copy()
#                 df_lag[PRICE_COL] = df_lag[PRICE_COL].shift(lag)
#                 df_lag = df_lag.dropna().reset_index(drop=True)

#                 res, t_vals, p_vals = fit_bass(df_lag, func, m_type)
#                 if (not res.success) or np.any(np.isnan(res.x)):
#                     continue

#                 p0, alpha, q, m_base, m_beta = res.x
#                 dN_predicted, _, m_t = compute_prediction(df_lag, res.x, func, m_type)
#                 rmse = np.sqrt(np.mean((df_lag["smooth_new"].values - dN_predicted) ** 2))

#                 full_records.append({
#                     "model": name,
#                     "m_type": m_type,
#                     "lag_days": lag,
#                     "p0": p0, "alpha": alpha, "q": q,
#                     "m_base": m_base, "m_beta": m_beta,
#                     "t_p0": t_vals[0], "t_alpha": t_vals[1], "t_q": t_vals[2],
#                     "t_m_base": t_vals[3], "t_m_beta": t_vals[4],
#                     "p_p0": p_vals[0], "p_alpha": p_vals[1], "p_q": p_vals[2],
#                     "p_m_base": p_vals[3], "p_m_beta": p_vals[4],
#                     "RMSE": rmse
#                 })

#                 print(f"Δ={lag:>2} 天 | p0={p0:.5f}, α={alpha:.5f}, q={q:.5f}, "
#                       f"m_base={m_base:.1f}, β={m_beta:.4f}, RMSE={rmse:.3f}")

#                 if rmse < best_rmse:
#                     best_rmse, best_res, best_lag, best_t, best_p = rmse, res, lag, t_vals, p_vals

#             if best_res is None:
#                 print(f"⚠️ 模型 {name}-{m_type} 拟合失败。")
#                 continue

#             p0, alpha, q, m_base, m_beta = best_res.x
#             print(f"✅ 最佳滞后 Δ={best_lag} 天 | RMSE={best_rmse:.3f}")
#             print(f"t-values: {best_t}")
#             print(f"p-values: {best_p}")

#             dN_predicted, _, m_t = compute_prediction(df, best_res.x, func, m_type)
#             cum_predicted = compute_cumulative(df, dN_predicted)

#             tag = f"{name}_{m_type}"
#             df[f"pred_new_{tag}"] = dN_predicted
#             df[f"pred_cum_{tag}"] = cum_predicted

#             summary_results.append({
#                 "model": name, "m_type": m_type, "best_lag": best_lag,
#                 "p0": p0, "alpha": alpha, "q": q,
#                 "m_base": m_base, "m_beta": m_beta,
#                 "t_p0": best_t[0], "t_alpha": best_t[1], "t_q": best_t[2],
#                 "t_m_base": best_t[3], "t_m_beta": best_t[4],
#                 "p_p0": best_p[0], "p_alpha": best_p[1], "p_q": best_p[2],
#                 "p_m_base": best_p[3], "p_m_beta": best_p[4],
#                 "RMSE": best_rmse
#             })
#             valid_models.append(tag)

#     # === 保存结果 ===
#     if summary_results:
#         full_df = pd.DataFrame(full_records)
#         summary_df = pd.DataFrame(summary_results)
#         full_df.to_csv(OUTPUT_CSV.replace(".csv", "_full.csv"), index=False)
#         summary_df.to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 结果已保存：\n - {OUTPUT_CSV}\n - {OUTPUT_CSV.replace('.csv', '_full.csv')}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # === 绘图 ===
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df["smooth_new"], label="7日平滑真实新增", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{tag}"], "--", label=f"预测新增 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("新增开发者数 dN/dt")
#     plt.title("ETH 开发者 Bass 模型新增数量（动态 m(t) + 参数显著性）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for tag in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{tag}"], "--", label=f"预测累积 ({tag})")
#     plt.xlabel("日期"); plt.ylabel("累积开发者数 N(t)")
#     plt.title("ETH 开发者 Bass 模型累积数量（动态 m(t) + 参数显著性）")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()