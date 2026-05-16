# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# competition_bass_pricefit_btc.py

# 对 BTC 开发者数量时间序列拟合 Bass 模型，
# p(t) 由价格驱动的三种方式：
#   1. 线性价格模型     p(t)=p0 + α·Price(t)
#   2. 对数价格模型     p(t)=p0 + α·ln(Price(t))
#   3. 百分比变化率模型 p(t)=p0 + α·(Price(t)-Price(t-1))/Price(t-1)
# """

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
competition_bass_pricefit_btc_v2.py

改进版：
- 对价格特征进行标准化
- 检查拟合结果的有效性
- 自动跳过异常模型，确保绘图完整
"""

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
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

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev.png" # 新增开发者图的文件名
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev.png" # 累积开发者图的文件名
# OUTPUT_CSV = "eth_bass_pricefit_results_v2.csv"
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


# # --------- 主程序（修改绘图部分） ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     results = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, func)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         p0, alpha, q, m = res.x
#         dN_predicted, p_t = compute_prediction(df, res.x, func)

#         if np.allclose(dN_predicted, 0) or np.any(np.isnan(dN_predicted)):
#             print(f"⚠️ 模型 {name} 预测为常数或 NaN，跳过绘图。")
#             continue

#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)
#         print(f"✅ 拟合成功：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#         # 计算累积预测值
#         cum_predicted = compute_cumulative(df, dN_predicted)
        
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted # 存储累积预测值
        
#         results.append({
#             "model": name,
#             "p0": p0, "alpha": alpha, "q": q, "m": m,
#             "SSE": sse, "RMSE": rmse
#         })
#         valid_models.append(name)

#     # 保存结果
#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果，退出。")
#         return

#     # --- 绘图 1: 新增开发者对比图（保持不变） ---
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")

#     plt.xlabel("日期")
#     plt.ylabel("ETH 新增开发者数 (dN/dt)")
#     plt.title("ETH 开发者 Bass 模型新增数量拟合对比")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")
#     # plt.show() # 可以选择性关闭以只显示最终图表

#     # --- 绘图 2: 累积 S 曲线对比图（新增） ---
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")

#     plt.xlabel("日期")
#     plt.ylabel("ETH 累积开发者数 N(t)")
#     plt.title("ETH 开发者 Bass 模型累积数量 S 曲线对比")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积 S 曲线图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()

# ============================================
# 加入了参数显著性检验
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bass 模型拟合 + 参数显著性检验
包含：线性价格、对数价格、百分比变化三种驱动方式
"""

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# from scipy.stats import t
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev.png"
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev.png"
# OUTPUT_CSV = "btc_bass_pricefit_results_t_p.csv"
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

# # 目标函数是针对新增开发者数（dN/dt，即 NEW_COL = btc_new_developers）的平方误差和 (SSE) 最小化
# def objective(params, df, price_func): 
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _ = compute_prediction(df, params, price_func)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return 1e12
#     return np.sum((dN_true - dN_predicted) ** 2)

# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9 * m_guess, 20 * m_guess)]
#     res = minimize(objective, init, args=(df, price_func), bounds=bounds, method="L-BFGS-B")

#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # 数值近似雅可比矩阵 J
#     y_pred, _ = compute_prediction(df, params, price_func)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, price_func)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     y_true = df[NEW_COL].values
#     residuals = y_true - y_pred
#     sigma2 = np.sum(residuals**2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k, k), np.nan)
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

#     # 打印显著性检验结果
#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p0", "alpha", "q", "m"], params, se, tvals, pvals):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     res.se, res.tvals, res.pvals = se, tvals, pvals
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     results = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, func)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         p0, alpha, q, m = res.x
#         dN_predicted, p_t = compute_prediction(df, res.x, func)
#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)
#         print(f"✅ 拟合成功：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#         cum_predicted = compute_cumulative(df, dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({
#             "model": name,
#             "p0": p0, "alpha": alpha, "q": q, "m": m,
#             "SSE": sse, "RMSE": rmse,
#             "t_p0": res.tvals[0], "p_p0": res.pvals[0],
#             "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
#             "t_q": res.tvals[2], "p_q": res.pvals[2],
#             "t_m": res.tvals[3], "p_m": res.pvals[3],
#         })
#         valid_models.append(name)

#     # 保存结果表
#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # 绘图：新增开发者曲线
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增数量拟合对比")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     # 绘图：累积开发者曲线
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 累积开发者数 N(t)")
#     plt.title("BTC Bass 模型累积数量 S 曲线拟合对比")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()

# ===============================
# 目标函数改成针对累计用户数的SSE

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import minimize
# from scipy.stats import t
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-07-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev.png"
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev.png"
# OUTPUT_CSV = "btc_bass_pricefit_results_t_p.csv"
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

# # 目标函数改为针对累积开发者数（N(t)，即 CUM_COL）的平方误差和 (SSE) 最小化
# def objective(params, df, price_func): 
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return 1e12
#     dN_predicted, _ = compute_prediction(df, params, price_func)
#     N_pred = compute_cumulative(df, dN_predicted)
#     N_true = df[CUM_COL].values
#     if np.any(np.isnan(N_pred)):
#         return 1e12
#     return np.sum((N_true - N_pred) ** 2)

# def compute_cumulative(df, new_dev_pred):
#     N0 = df[CUM_COL].iloc[0]
#     return N0 + np.insert(np.cumsum(new_dev_pred)[:-1], 0, 0)


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = [(0, 1), (-10, 10), (0, 1), (0.9 * m_guess, 20 * m_guess)]
#     res = minimize(objective, init, args=(df, price_func), bounds=bounds, method="L-BFGS-B")

#     if not res.success:
#         return res

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # 数值近似雅可比矩阵 J
#     dN_pred, _ = compute_prediction(df, params, price_func)
#     y_pred = compute_cumulative(df, dN_pred)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         dN_pred_eps, _ = compute_prediction(df, params_eps, price_func)
#         y_pred_eps = compute_cumulative(df, dN_pred_eps)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     y_true = df[CUM_COL].values
#     residuals = y_true - y_pred
#     sigma2 = np.sum(residuals**2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k, k), np.nan)
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

#     # 打印显著性检验结果
#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p0", "alpha", "q", "m"], params, se, tvals, pvals):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     res.se, res.tvals, res.pvals = se, tvals, pvals
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     results = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, func)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         p0, alpha, q, m = res.x
#         dN_predicted, p_t = compute_prediction(df, res.x, func)
#         cum_predicted = compute_cumulative(df, dN_predicted)
#         rmse = np.sqrt(np.mean((df[CUM_COL].values - cum_predicted) ** 2))
#         sse = np.sum((df[CUM_COL].values - cum_predicted) ** 2)
#         print(f"✅ 拟合成功：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({
#             "model": name,
#             "p0": p0, "alpha": alpha, "q": q, "m": m,
#             "SSE": sse, "RMSE": rmse,
#             "t_p0": res.tvals[0], "p_p0": res.pvals[0],
#             "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
#             "t_q": res.tvals[2], "p_q": res.pvals[2],
#             "t_m": res.tvals[3], "p_m": res.pvals[3],
#         })
#         valid_models.append(name)

#     # 保存结果表
#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # 绘图：新增开发者曲线
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增数量拟合对比")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     # 绘图：累积开发者曲线
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 累积开发者数 N(t)")
#     plt.title("BTC Bass 模型累积数量 S 曲线拟合对比")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()


# =====================
# 改用目标函数是新增用户数+least squares优化

# 问题：这个代码中p为常量的结果为什么和离散bass闭式解拟合结果一样，和连续bass闭式解拟合结果不一样
# 答案：您的代码实际上是采用了微分方程的代数结构，但用离散数据来驱动，使其在数值上等效于常用的离散 Bass 模型，而与严格的连续时间 $t$ 解析解是不同的。
# 你在 least_squares 里用的 dN_pred(N, p_t, q, m) = (p_t + q*(N/m)) * (m - N) 是 离散期（per-period）增量模型 的形式（把每期的新增当作一次“差分”更新）。
# 之前你用 bass_model_dN(t, p, q, m) / bass_model_N(t,...) 拟合的是 连续时间解析解（导数或连续函数），参数p,q 在数学上是“每单位时间的速率”。
# 这两类模型对参数的含义和尺度不一样（per-period vs per-time-unit），因此用同一数据拟合会得到不同的数值解——和离散模型相同 是合理的；不等于连续解析解 也很常见。
# 离散模型的 p,q 是“每期（one period）”的参数，和连续意义不同，数值不会相同。

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
PRICE_COL = "btc_price_lag1"
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev20202021.png"
OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev20202021.png"
OUTPUT_CSV = "btc_bass_pricefit_results_t_p20202021.csv"
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


# --------- Bass 离散模型 ----------
def dN_pred(N, p_t, q, m):
    remaining_market = np.maximum(m - N, 0)
    return (p_t + q * (N / m)) * remaining_market


# --------- 价格变换 ----------
def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)

def price_identity(price): return normalize(price)
def price_log(price): return normalize(np.log(np.maximum(price, 1e-8)))
def price_pct(price):
    lag = np.roll(price, 1)
    lag[0] = price[0]
    return normalize((price - lag) / np.where(lag == 0, 1, lag))


# --------- baseline：constant p ---------
def compute_pred_constant_p(df, params):
    p0, q, m = params
    N = df[CUM_COL].values
    p_t = np.full(len(df), p0)
    return dN_pred(N, p_t, q, m), p_t

def residuals_constant_p(params, df):
    p0, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6

    dN_predicted, _ = compute_pred_constant_p(df, params)
    dN_true = df[NEW_COL].values

    return dN_true - dN_predicted


# --------- price-driven model ---------
def compute_prediction(df, params, price_func):
    p0, alpha, q, m = params
    price = df[PRICE_COL].values
    p_input = price_func(price)
    p_t = np.maximum(p0 + alpha * p_input, 0)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q, m), p_t

def residuals(params, df, price_func):
    p0, alpha, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_prediction(df, params, price_func)
    return df[NEW_COL].values - dN_predicted


# --------- 打印参数显著性函数 (新增) ----------
def print_parameter_table(model_name, params, se, tvals, pvals, param_names):
    """打印格式化的参数估计值、SE、t值和p值"""
    print(f"\n--- {model_name} 参数显著性 ---")
    print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
    print("---------------------------------------------------")

    for name, val, s, tval, pval in zip(param_names, params, se, tvals, pvals):
        print(f"{name:<10}{val:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}")
    print("---------------------------------------------------\n")

# --------- 参数拟合 + 显著性检验 ----------
def significance(df, params, compute_pred_func, k):
    eps = 1e-8
    n = len(df)

    # 适配 compute_pred_func 的参数要求
    if k == 3:
        y_pred, _ = compute_pred_func(df, params)
    else:
        # 当 k=4 时，compute_pred_func 需要 price_func，这里使用 lambda 传递
        y_pred, _ = compute_pred_func(df, params) 

    # --- 数值求雅可比矩阵 ---
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        
        # 适配 compute_pred_func 的参数要求
        if k == 3:
             y_eps, _ = compute_pred_func(df, params_eps)
        else:
             y_eps, _ = compute_pred_func(df, params_eps)
             
        J.append((y_eps - y_pred) / eps)

    J = np.array(J).T

    y_true = df[NEW_COL].values
    residuals_vec = y_true - y_pred
    sigma2 = np.sum(residuals_vec**2) / (n - k)

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
    except:
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
    return se, tvals, pvals


# --------- 主程序 (已修改) ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    results = []
    valid_models = []

    # ✅ 1. baseline: constant p
    print(f"\n=== 拟合模型：constant_p ===")
    m_guess = 1.2 * df[CUM_COL].max()
    res0 = least_squares(residuals_constant_p,
                         x0=[0.01, 0.3, m_guess],
                         bounds=([1e-6, 0, 0.5*m_guess], [0.99, 1.0, 20*m_guess]),
                         args=(df,), method="trf")

    if res0.success:
        params = res0.x
        p0, q, m = params
        dN_pred0, _ = compute_pred_constant_p(df, params)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_pred0)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred0)**2))

        print(f"✅ baseline 成功：p0={p0:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

        se, tvals, pvals = significance(df, params, compute_pred_constant_p, 3)

        # 打印参数显著性 (新增)
        print_parameter_table("constant_p", params, se, tvals, pvals, ["p0", "q", "m"])


        results.append({
            "model": "constant_p",
            "p0": p0, "alpha": 0,
            "q": q, "m": m,
            "RMSE": rmse,
            "t_p0": tvals[0], "p_p0": pvals[0],
            "t_alpha": np.nan, "p_alpha": np.nan,
            "t_q": tvals[1], "p_q": pvals[1],
            "t_m": tvals[2], "p_m": pvals[2],
        })

        df["pred_new_constant_p"] = dN_pred0
        df["pred_cum_constant_p"] = cum_pred
        valid_models.append("constant_p")


    # ✅ 2–4. price-driven models
    models = {
        "linear_price": price_identity,
        "log_price": price_log,
        "pct_change_price": price_pct
    }

    for name, func in models.items():
        print(f"\n=== 拟合模型：{name} ===")
        m_guess = 1.2 * df[CUM_COL].max()
        res = least_squares(residuals,
                            x0=[1e-4, 0.01, 0.01, m_guess],
                            bounds=([0, -10, 0, 0.9*m_guess],
                                    [1, 10, 1, 20*m_guess]),
                            args=(df, func), method="trf")

        if not res.success:
            print("⚠️ 优化失败")
            continue

        params = res.x
        p0, alpha, q, m = params
        dN_predicted, p_t = compute_prediction(df, params, func)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted)**2))

        # 这里的 lambda 函数用于适配 significance 函数的结构
        se, tvals, pvals = significance(df, params,
                                        lambda df, p: compute_prediction(df, p, func), 
                                        4)

        print(f"✅ {name} 成功：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

        # 打印参数显著性 (新增)
        print_parameter_table(name, params, se, tvals, pvals, ["p0", "alpha", "q", "m"])

        results.append({
            "model": name,
            "p0": p0, "alpha": alpha,
            "q": q, "m": m,
            "RMSE": rmse,
            "t_p0": tvals[0], "p_p0": pvals[0],
            "t_alpha": tvals[1], "p_alpha": pvals[1],
            "t_q": tvals[2], "p_q": pvals[2],
            "t_m": tvals[3], "p_m": pvals[3],
        })

        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_pred
        valid_models.append(name)


    # ✅ 保存结果
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 拟合结果已保存至 {OUTPUT_CSV}")


    # ---------- 绘图 ----------
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"{name}")
    plt.xlabel("日期"); plt.ylabel("新增 dN/dt")
    plt.title("Bass 新增开发者拟合（含 baseline）")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)


    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实 N(t)", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"{name}")
    plt.xlabel("日期"); plt.ylabel("累积 N(t)")
    plt.title("Bass 累积曲线（含 baseline）")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)

    plt.show()


if __name__ == "__main__":
    main()


# ==========
# 为了消融实验 和model8设置除了p(t) 其他都不一样
# 和上面那个代码的区别在于标准化流程 上面代码是在每个函数里做标准化 这里是在load_data里做全局标准化

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# # 注意：路径可能需要根据您的环境调整，这里使用变量名
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv" 
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_priceonly_new.png"
# OUTPUT_PNG_CUM = "btc_bass_priceonly_cum.png"
# OUTPUT_CSV = "btc_bass_priceonly_results.csv"
# # ===================================


# # --------- 数据准备 ----------
# def load_data():
#     try:
#         # 使用当前目录下的文件名，而不是绝对路径
#         df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except FileNotFoundError:
#         print(f"❌ 错误: 文件 '{CSV_PATH}' 未找到。请确保文件存在于执行环境中。")
#         raise

#     # 1. 确保只选择需要的列，并进行前向填充
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)

#     # 2. 计算原始价格的对数和百分比变化
#     P_raw = df[PRICE_COL]
    
#     # --- A. 计算百分比变化 (Price Pct Change) ---
#     # 必须在原始价格上计算
#     df["price_lag"] = P_raw.shift(1)
#     # 计算变化率 (防止分母为 0)
#     df["price_pct"] = (P_raw - df["price_lag"]) / (df["price_lag"].replace(0, np.nan))
#     df["price_pct"] = df["price_pct"].replace([np.inf, -np.inf], 0).fillna(0)

#     # --- B. 计算对数价格 (Log Price) ---
#     # 对原始价格取对数
#     df["price_log"] = np.log(np.maximum(P_raw, 1e-8))

#     # --- C. 对所有协变量进行全局标准化 (Z-Score) ---
#     # price_identity, price_log, price_pct
    
#     # 定义标准化函数 (只用于 load_data 内部)
#     def z_score_normalize(series):
#         mean_val, std_val = series.mean(), series.std()
#         if std_val > 0:
#             return (series - mean_val) / (std_val)
#         else:
#             return series

#     # 对三个协变量进行标准化，并用标准化后的列名替换原始列
#     df[PRICE_COL + '_std'] = z_score_normalize(P_raw)
#     df['price_log_std'] = z_score_normalize(df['price_log'])
#     df['price_pct_std'] = z_score_normalize(df['price_pct'])
    
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     # Bass 公式的核心部分
#     return (p_t + q * (N / (m + 1e-12))) * remaining_market


# def compute_p_t(df, params, model_type):
#     """
#     三种形式:
#       1. linear_price  : p0 + α * price_std
#       2. log_price     : p0 + α * price_log_std
#       3. pct_price     : p0 + α * price_pct_std
#     """
#     p0, alpha, q, m = params
    
#     if model_type == "linear_price":
#         P_std = df[PRICE_COL + '_std'].values
#     elif model_type == "log_price":
#         P_std = df['price_log_std'].values
#     elif model_type == "pct_price":
#         P_std = df['price_pct_std'].values
#     else:
#         raise ValueError("未知模型类型")
        
#     p_t = np.maximum(p0 + alpha * P_std, 0)
#     return p_t


# def compute_prediction(df, params, model_type):
#     p_t = compute_p_t(df, params, model_type)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, params[-2], params[-1]), p_t


# # --------- 残差函数 ----------
# def residuals(params, df, model_type):
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
        
#     dN_predicted, _ = compute_prediction(df, params, model_type)
#     dN_true = df[NEW_COL].values
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
        
#     # least_squares 最小化新增量残差平方和
#     return dN_true - dN_predicted


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, model_type):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     # alpha 的边界放宽到 10，因为 alpha 现在是标准化系数
#     bounds = ([0, -10, 0, 0.9 * m_guess], [1, 10, 1, 20 * m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, model_type), method="trf")
#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)
#     y_pred, _ = compute_prediction(df, params, model_type)

#     # 数值雅可比矩阵
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, model_type)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T

#     cond = np.linalg.cond(J.T @ J)
#     print(f"⚙️ Hessian 条件数 cond={cond:.2e}")

#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred
#     sigma2 = np.sum(residuals_vec**2) / (n - k)

#     try:
#         # 使用 pinv 提高鲁棒性，而非 np.linalg.inv
#         cov = sigma2 * np.linalg.pinv(J.T @ J, rcond=1e-6)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond

#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p0", "alpha(price_std)", "q", "m"], params, se, tvals, pvals):
#         print(f"{name:18s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     return res


# # --------- 主程序 ----------
# def main():
#     try:
#         df = load_data()
#     except Exception:
#         return

#     df = select_date(df, START_DATE, END_DATE)
    
#     # 模型名称与对应的标准化协变量列
#     models = {
#         "linear_price": 'linear_price',
#         "log_price": 'log_price',
#         "pct_price": 'pct_price'
#     }
#     results = []
#     valid_models = []

#     for name, model_type in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, model_type)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         dN_predicted, p_t = compute_prediction(df, res.x, model_type)
#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted)**2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted)**2)

#         print(f"✅ 拟合成功：{name}, RMSE={rmse:.3f}")
#         cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({
#             "model": name, 
#             **{f"param_{i}": val for i, val in enumerate(res.x)}, 
#             "SSE": sse, 
#             "RMSE": rmse,
#             "t_alpha": res.tvals[1], "p_alpha": res.pvals[1]
#         })
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # 绘图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")


# if __name__ == "__main__":
#     main()

# =======
# ================== 局部标准化+a反标准化 ==================
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
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_pricefit_new_dev.png"
# OUTPUT_PNG_CUM = "eth_bass_pricefit_cum_dev.png"
# OUTPUT_CSV = "eth_bass_pricefit_results_t_p.csv"
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


# def normalize_with_scale(x):
#     """标准化并返回标准差，用于拟合后还原参数"""
#     x = np.array(x)
#     mean, std = np.mean(x), np.std(x) + 1e-8
#     z = (x - mean) / std
#     return z, std


# def price_identity(price):
#     z, std = normalize_with_scale(price)
#     return z, std

# def price_log(price):
#     val = np.log(np.maximum(price, 1e-8))
#     z, std = normalize_with_scale(val)
#     return z, std

# def price_pct(price):
#     lag = np.roll(price, 1)
#     lag[0] = price[0]
#     pct = (price - lag) / np.where(lag == 0, 1, lag)
#     z, std = normalize_with_scale(pct)
#     return z, std


# def compute_prediction(df, params, price_func):
#     p0, alpha, q, m = params
#     price = df[PRICE_COL].values
#     p_input, price_std = price_func(price)
#     p_t = np.maximum(p0 + alpha * p_input, 0)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, q, m), p_t, price_std


# # --------- least_squares 残差函数 ----------
# def residuals(params, df, price_func):
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _, _ = compute_prediction(df, params, price_func)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = ([0, -10, 0, 0.9 * m_guess], [1, 10, 1, 20 * m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func), method="trf")

#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # ===== 数值近似雅可比矩阵 =====
#     y_pred, _, price_std = compute_prediction(df, params, price_func)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _, _ = compute_prediction(df, params_eps, price_func)
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
#     for name, val, se_i, t_i, p_i in zip(["p0", "alpha", "q", "m"], params, se, tvals, pvals):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     # 还原 α 到真实价格尺度
#     alpha_real = params[1] / price_std
#     print(f"→ α(norm)={params[1]:.6f}, α(real)={alpha_real:.6f}")

#     res.se, res.tvals, res.pvals, res.cond, res.alpha_real = se, tvals, pvals, cond, alpha_real
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     results = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, func)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         p0, alpha, q, m = res.x
#         alpha_real = res.alpha_real
#         dN_predicted, _, _ = compute_prediction(df, res.x, func)
#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)
#         print(f"✅ 拟合成功：p0={p0:.6f}, α(norm)={alpha:.6f}, α(real)={alpha_real:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#         cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({
#             "model": name,
#             "p0": p0, "alpha_norm": alpha, "alpha_real": alpha_real, "q": q, "m": m,
#             "SSE": sse, "RMSE": rmse,
#             "t_p0": res.tvals[0], "p_p0": res.pvals[0],
#             "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
#             "t_q": res.tvals[2], "p_q": res.pvals[2],
#             "t_m": res.tvals[3], "p_m": res.pvals[3],
#             "cond": res.cond
#         })
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增数量拟合对比")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 累积开发者数 N(t)")
#     plt.title("BTC Bass 模型累积数量 S 曲线拟合对比")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()




# =====================
# 改用目标函数是累积用户数+least squares优化

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
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_pricefit_new_dev.png"
# OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_dev.png"
# OUTPUT_CSV = "btc_bass_pricefit_results_t_p.csv"
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


# # --------- 预测函数（返回 N_pred） ----------
# def compute_prediction(df, params, price_func):
#     p0, alpha, q, m = params
#     price = df[PRICE_COL].values
#     p_input = price_func(price)
#     p_t = np.maximum(p0 + alpha * p_input, 0)

#     N_pred = np.zeros(len(df))
#     N_pred[0] = df[CUM_COL].iloc[0]

#     for t in range(1, len(df)):
#         dN = dN_pred(N_pred[t-1], p_t[t-1], q, m)
#         N_pred[t] = min(N_pred[t-1] + dN, m)

#     return N_pred, p_t


# # --------- least_squares 残差函数 ----------
# def residuals(params, df, price_func):
#     p0, alpha, q, m = params
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
#     N_pred, _ = compute_prediction(df, params, price_func)
#     N_true = df[CUM_COL].values
#     if np.any(np.isnan(N_pred)) or np.allclose(N_pred, 0):
#         return np.ones(len(df)) * 1e6
#     return N_true - N_pred


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, price_func):
#     m_guess = 1.2 * df[CUM_COL].max()
#     init = [1e-4, 0.01, 0.01, m_guess]
#     bounds = ([0, -10, 0, 0.9 * m_guess], [1, 10, 1, 20 * m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, price_func), method="trf")

#     if not res.success:
#         return res, None

#     params = res.x
#     eps = 1e-6
#     n = len(df)
#     k = len(params)

#     # 数值近似雅可比矩阵 J
#     y_pred, _ = compute_prediction(df, params, price_func)
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, price_func)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T  # n×k

#     y_true = df[CUM_COL].values
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
#     for name, val, se_i, t_i, p_i in zip(["p0", "alpha", "q", "m"], params, se, tvals, pvals):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     res.se, res.tvals, res.pvals = se, tvals, pvals
#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = {
#         "linear_price": price_identity,
#         "log_price": price_log,
#         "pct_change_price": price_pct
#     }

#     results = []
#     valid_models = []

#     for name, func in models.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, func)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         p0, alpha, q, m = res.x
#         N_pred, p_t = compute_prediction(df, res.x, func)
#         rmse = np.sqrt(np.mean((df[CUM_COL].values - N_pred) ** 2))
#         sse = np.sum((df[CUM_COL].values - N_pred) ** 2)
#         print(f"✅ 拟合成功：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

#         dN_pred = np.diff(np.insert(N_pred, 0, df[CUM_COL].iloc[0]))
#         df[f"pred_new_{name}"] = dN_pred
#         df[f"pred_cum_{name}"] = N_pred

#         results.append({
#             "model": name,
#             "p0": p0, "alpha": alpha, "q": q, "m": m,
#             "SSE": sse, "RMSE": rmse,
#             "t_p0": res.tvals[0], "p_p0": res.pvals[0],
#             "t_alpha": res.tvals[1], "p_alpha": res.pvals[1],
#             "t_q": res.tvals[2], "p_q": res.pvals[2],
#             "t_m": res.tvals[3], "p_m": res.pvals[3],
#         })
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果与显著性检验已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # ---------- 绘图 ----------
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 新增开发者数 dN/dt")
#     plt.title("BTC Bass 模型新增数量拟合对比（基于累积拟合）")
#     plt.legend()
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增开发者图已保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.xlabel("日期")
#     plt.ylabel("BTC 累积开发者数 N(t)")
#     plt.title("BTC Bass 模型累积数量 S 曲线拟合（Least Squares）")
#     plt.legend()
#     plt.grid(True, linestyle='--')
#     plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积开发者图已保存至 {OUTPUT_PNG_CUM}")
#     plt.show()


# if __name__ == "__main__":
#     main()

