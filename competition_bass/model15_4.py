# 迁出：负面效应降低扩散速度
# =========================================================
# Competitive Bass with EXIT (Out-migration only)
# ΔN(t) = [ p(t) + q(t)·X(t−1)/m − Σ δ_k · M_k^out,norm(t−1) ] · (m − X(t−1))
# =========================================================

# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_daily_strict_rules.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "btc_bass_pqfit_results_exit_negative_network.csv"

# # 竞争币种列表（与迁出列对应）
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "DOGE"]

# # 迁出列名映射
# OUTFLOW_COLS = {
#     "BCH": "out_to_BCH",
#     "BSV": "out_to_BSV",
#     "ETH": "out_to_ETH",
#     "LTC": "out_to_LTC",
#     "DOGE": "out_to_DOGE"
# }

# # ===================================
# # ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]

# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     """标准化函数：均值0，标准差1"""
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- 加载并对齐迁出数据 ---------
# def load_and_align_outflow_data(migration_path, main_df):
#     """
#     加载迁出数据并对齐到主数据框的日期
    
#     Args:
#         migration_path: 迁移数据CSV路径
#         main_df: 主数据框（包含date列）
    
#     Returns:
#         outflow_dict: {coin: outflow_array} 字典
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n{'='*80}")
#     print(f"📊 加载迁出数据")
#     print(f"{'='*80}")
#     print(f"迁移数据文件: {migration_path}")
#     print(f"迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"迁移数据行数: {len(df_mig)}")
    
#     # 对齐到main_df的日期
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
#     df_full = pd.DataFrame({'date': main_dates})
    
#     # 合并
#     df_merged = df_full.merge(df_mig, on='date', how='left')
    
#     # 构建迁出字典
#     outflow_dict = {}
#     for coin in COMPETITORS:
#         col_name = OUTFLOW_COLS.get(coin)
#         if col_name and col_name in df_merged.columns:
#             outflow_dict[coin] = df_merged[col_name].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁出数据列: {col_name}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {col_name}")
#             outflow_dict[coin] = np.zeros(len(df_merged))
    
#     # 统计
#     print(f"\n📈 迁出数据统计（窗口期内）:")
#     print("🔥 迁出产生负网络效应（降低扩散率）")
#     for coin in COMPETITORS:
#         M_out = outflow_dict[coin]
#         total = M_out.sum()
#         non_zero = (M_out > 0).sum()
#         if non_zero > 0:
#             max_val = M_out.max()
#             mean_val = M_out.mean()
#             std_val = M_out.std()
#             print(f"  {coin:10s}: 总数={total:6.0f}, 非零天数={non_zero:4d}, "
#                   f"均值={mean_val:5.2f}, 标准差={std_val:5.2f}, 最大={max_val:5.0f}")
#         else:
#             print(f"  {coin:10s}: 总数=     0, 非零天数=   0 (无数据)")
    
#     print(f"{'='*80}\n")
    
#     return outflow_dict

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
#     """计算q(t)"""
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# # --------- p(t) 计算 ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """计算p(t)"""
#     ev = normalize(df[p_event_col].values)
#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * ev
#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
#     else:
#         raise ValueError("未知 p_model")
#     return np.maximum(p_t, 0)

# # --------- 🔥 Bass增量（迁出负网络效应） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, outflow_dict_lag, delta_params):
#     """
#     迁出负网络效应的Bass模型
    
#     ΔN(t) = [p(t) + q(t)·X(t−1)/m − Σ δ_k · M_k^out,norm(t−1)] · (m − X(t−1))
    
#     Args:
#         N_lag: X(t-1)，期初累积用户
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 固定市场容量
#         outflow_dict_lag: {coin: M^out,lag(t-1)} 字典（滞后1期的迁出）
#         delta_params: [δ_BCH, δ_BSV, δ_ETH, δ_LTC, δ_DOGE]（负网络效应系数）
    
#     Returns:
#         ΔN(t) 预测值
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 🔥 迁出的负网络效应
#     negative_network = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in outflow_dict_lag:
#             M_out_lag = outflow_dict_lag[coin]
#             M_out_norm = normalize(M_out_lag)  # 标准化
#             negative_network += delta_params[i] * M_out_norm
    
#     # 总扩散率 = 内生 - 负网络效应
#     total_rate = base_rate - negative_network
    
#     return total_rate * remaining

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """计算预测值"""
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         delta_params = params[5:10]  # 5个δ参数
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         delta_params = params[6:11]  # 5个δ参数
#         m = params[11]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values
    
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, outflow_dict_lag, delta_params)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """计算残差"""
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """拟合Bass模型"""
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # params: [p0, alpha, beta, q0, beta_q, 
#             #          delta_BCH, delta_BSV, delta_ETH, delta_LTC, delta_DOGE, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001, 0.0001, 0.0001, 0.0001,  # delta初始值
#                     m_guess]
#             bounds = ([0, -10, -10, 0, -10, 
#                       0, 0, 0, 0, 0,  # delta >= 0（负效应通过减号体现）
#                       0.9*m_guess],
#                       [1, 10, 10, 1, 10, 
#                        0.01, 0.01, 0.01, 0.01, 0.01,  # delta上界
#                        20*m_guess])
#         else:
#             # params: [p0, alpha, beta, gamma, q0, beta_q, 
#             #          delta_BCH, delta_BSV, delta_ETH, delta_LTC, delta_DOGE, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 
#                     m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 
#                       0, 0, 0, 0, 0, 
#                       0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 
#                        0.01, 0.01, 0.01, 0.01, 0.01, 
#                        20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误、t值、p值
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T
        
#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except np.linalg.LinAlgError:
#             cond = np.nan
        
#         resid_vec = df[NEW_COL].values - y_pred
#         sigma2 = np.sum(resid_vec**2) / (n - k)
        
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except np.linalg.LinAlgError:
#             se = np.full(k, np.nan)
        
#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
#         return res
    
#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主数据
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     # 筛选日期窗口
#     df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
#                     (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
#     # 🔥 加载迁出数据
#     outflow_dict_global = load_and_align_outflow_data(MIGRATION_PATH, df_raw)
    
#     if outflow_dict_global is None:
#         print("⚠️ 无法加载迁出数据，程序退出")
#         sys.exit(1)
    
#     # 🔥 创建滞后1期的迁出数据
#     outflow_dict_lag_global = {}
#     for coin in COMPETITORS:
#         M_out = outflow_dict_global[coin]
#         # 滞后1期：t-1的迁出
#         M_out_lag = np.concatenate([[0], M_out[:-1]])
#         outflow_dict_lag_global[coin] = M_out_lag
    
#     # 添加N_lag
#     df_raw['N_lag'] = df_raw[CUM_COL].shift(1).fillna(df_raw[CUM_COL].iloc[0])
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # 主循环
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # 检查列
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 选择数据
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
#                          'N_lag'] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 🔥 对齐迁出数据到当前df
#             outflow_dict_lag = {}
#             for coin in COMPETITORS:
#                 # 使用全局的滞后迁出数据（已经对齐）
#                 outflow_dict_lag[coin] = outflow_dict_lag_global[coin][:len(df)]
            
#             # 价格变换
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 try:
#                     price_transforms = {
#                         "linear": normalize(raw_price),
#                         "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
#                         "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
#                     }
#                 except Exception:
#                     print(f"⚠️ price transform error for {price_col}, skipping.")
#                     continue
                
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # 计算RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 参数名称
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "delta_BCH", "delta_BSV", "delta_ETH", 
#                                              "delta_LTC", "delta_DOGE", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "delta_BCH", "delta_BSV", "delta_ETH", 
#                                              "delta_LTC", "delta_DOGE", "m"]
                            
#                             row = {
#                                 "P_event": p_event_col,
#                                 "Q_event": q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf": pt_name,
#                                 "p_model": p_model,
#                                 "q_form": q_form,
#                                 "RMSE": rmse,
#                                 "SSE": sse,
#                                 "cond": float(getattr(res, "cond", np.nan))
#                             }
                            
#                             for i, name in enumerate(param_names):
#                                 row[name] = float(params[i]) if i < len(params) else np.nan
#                                 row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
#                                 row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
#                                 row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            
#                             results.append(row)
    
#     # 保存结果
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n{'='*80}")
#     print(f"✅ 完成！")
#     print(f"{'='*80}")
#     print(f"成功拟合: {combos_done} 个组合")
#     print(f"跳过: {combos_skipped} 个组合")
#     print(f"结果已保存: {OUTPUT_CSV}")
#     print(f"{'='*80}\n")

# if __name__ == "__main__":
#     main()


# 只算BCH和BSV两个迁出负效应
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_daily_strict_rules.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "btc_bass_pqfit_results_exit_fork_only.csv"  # 🔥 修改输出文件名

# # 🔥 竞争币种列表：只保留硬分叉
# COMPETITORS = ["BCH", "BSV"]

# # 🔥 迁出列名映射：只保留硬分叉
# OUTFLOW_COLS = {
#     "BCH": "out_to_BCH",
#     "BSV": "out_to_BSV"
# }

# # ===================================
# # ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     # "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     # "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]

# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     """标准化函数：均值0，标准差1"""
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- 加载并对齐迁出数据 ---------
# def load_and_align_outflow_data(migration_path, main_df):
#     """
#     加载迁出数据并对齐到主数据框的日期
    
#     Args:
#         migration_path: 迁移数据CSV路径
#         main_df: 主数据框（包含date列）
    
#     Returns:
#         outflow_dict: {coin: outflow_array} 字典
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n{'='*80}")
#     print(f"📊 加载迁出数据（仅硬分叉：BCH & BSV）")
#     print(f"{'='*80}")
#     print(f"迁移数据文件: {migration_path}")
#     print(f"迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"迁移数据行数: {len(df_mig)}")
    
#     # 对齐到main_df的日期
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
#     df_full = pd.DataFrame({'date': main_dates})
    
#     # 合并
#     df_merged = df_full.merge(df_mig, on='date', how='left')
    
#     # 🔥 构建迁出字典（仅BCH和BSV）
#     outflow_dict = {}
#     for coin in COMPETITORS:
#         col_name = OUTFLOW_COLS.get(coin)
#         if col_name and col_name in df_merged.columns:
#             outflow_dict[coin] = df_merged[col_name].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁出数据列: {col_name}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {col_name}")
#             outflow_dict[coin] = np.zeros(len(df_merged))
    
#     # 统计
#     print(f"\n📈 迁出数据统计（窗口期内）:")
#     print("🔥 硬分叉迁出产生负网络效应（降低扩散率）")
#     for coin in COMPETITORS:
#         M_out = outflow_dict[coin]
#         total = M_out.sum()
#         non_zero = (M_out > 0).sum()
#         if non_zero > 0:
#             max_val = M_out.max()
#             mean_val = M_out.mean()
#             std_val = M_out.std()
#             print(f"  {coin:10s}: 总数={total:6.0f}, 非零天数={non_zero:4d}, "
#                   f"均值={mean_val:5.2f}, 标准差={std_val:5.2f}, 最大={max_val:5.0f}")
#         else:
#             print(f"  {coin:10s}: 总数=     0, 非零天数=   0 (无数据)")
    
#     # 🔥 计算总迁出（BCH + BSV）
#     total_fork_out = sum([outflow_dict[coin] for coin in COMPETITORS])
#     print(f"\n  总硬分叉迁出（BCH+BSV）: {total_fork_out.sum():6.0f}")
    
#     print(f"{'='*80}\n")
    
#     return outflow_dict

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
#     """计算q(t)"""
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# # --------- p(t) 计算 ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """计算p(t)"""
#     ev = normalize(df[p_event_col].values)
#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * ev
#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
#     else:
#         raise ValueError("未知 p_model")
#     return np.maximum(p_t, 0)

# # --------- 🔥 Bass增量（仅硬分叉迁出负网络效应） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, outflow_dict_lag, delta_params):
#     """
#     硬分叉迁出负网络效应的Bass模型
    
#     ΔN(t) = [p(t) + q(t)·X(t−1)/m − δ_BCH·M_BCH^norm(t−1) − δ_BSV·M_BSV^norm(t−1)] · (m − X(t−1))
    
#     Args:
#         N_lag: X(t-1)，期初累积用户
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 固定市场容量
#         outflow_dict_lag: {coin: M^out,lag(t-1)} 字典（滞后1期的迁出）
#         delta_params: [δ_BCH, δ_BSV]（负网络效应系数）
    
#     Returns:
#         ΔN(t) 预测值
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 🔥 硬分叉迁出的负网络效应（仅BCH和BSV）
#     negative_network = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):  # COMPETITORS = ["BCH", "BSV"]
#         if coin in outflow_dict_lag:
#             M_out_lag = outflow_dict_lag[coin]
#             M_out_norm = normalize(M_out_lag)  # 标准化
#             negative_network += delta_params[i] * M_out_norm
    
#     # 总扩散率 = 内生 - 负网络效应
#     total_rate = base_rate - negative_network
    
#     return total_rate * remaining

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """计算预测值"""
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         delta_params = params[5:7]  # 🔥 2个δ参数（BCH, BSV）
#         m = params[7]  # 🔥 m在第8位
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         delta_params = params[6:8]  # 🔥 2个δ参数
#         m = params[8]  # 🔥 m在第9位
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values
    
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, outflow_dict_lag, delta_params)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """计算残差"""
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[7]  # 🔥 修改
#     else:
#         q0 = params[4]
#         m = params[8]  # 🔥 修改
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag):
#     """拟合Bass模型"""
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # 🔥 params: [p0, alpha, beta, q0, beta_q, delta_BCH, delta_BSV, m]
#             # 总共8个参数
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001,  # 🔥 2个delta
#                     m_guess]
#             bounds = ([0, -10, -10, 0, -10, 
#                       0, 0,  # 🔥 delta >= 0
#                       0.9*m_guess],
#                       [1, 10, 10, 1, 10, 
#                        0.01, 0.01,  # 🔥 delta上界
#                        20*m_guess])
#         else:
#             # 🔥 params: [p0, alpha, beta, gamma, q0, beta_q, delta_BCH, delta_BSV, m]
#             # 总共9个参数
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001,  # 🔥 2个delta
#                     m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 
#                       0, 0,  # 🔥 delta >= 0
#                       0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 
#                        0.01, 0.01,  # 🔥 delta上界
#                        20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误、t值、p值
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T
        
#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except np.linalg.LinAlgError:
#             cond = np.nan
        
#         resid_vec = df[NEW_COL].values - y_pred
#         sigma2 = np.sum(resid_vec**2) / (n - k)
        
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except np.linalg.LinAlgError:
#             se = np.full(k, np.nan)
        
#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
#         return res
    
#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主数据
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     # 筛选日期窗口
#     df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
#                     (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
#     # 🔥 加载迁出数据
#     outflow_dict_global = load_and_align_outflow_data(MIGRATION_PATH, df_raw)
    
#     if outflow_dict_global is None:
#         print("⚠️ 无法加载迁出数据，程序退出")
#         sys.exit(1)
    
#     # 🔥 创建滞后1期的迁出数据
#     outflow_dict_lag_global = {}
#     for coin in COMPETITORS:  # 🔥 只有BCH和BSV
#         M_out = outflow_dict_global[coin]
#         # 滞后1期：t-1的迁出
#         M_out_lag = np.concatenate([[0], M_out[:-1]])
#         outflow_dict_lag_global[coin] = M_out_lag
    
#     # 添加N_lag
#     df_raw['N_lag'] = df_raw[CUM_COL].shift(1).fillna(df_raw[CUM_COL].iloc[0])
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # 主循环
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # 检查列
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 选择数据
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
#                          'N_lag'] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 🔥 对齐迁出数据到当前df
#             outflow_dict_lag = {}
#             for coin in COMPETITORS:  # 🔥 只有BCH和BSV
#                 # 使用全局的滞后迁出数据（已经对齐）
#                 outflow_dict_lag[coin] = outflow_dict_lag_global[coin][:len(df)]
            
#             # 价格变换
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 try:
#                     price_transforms = {
#                         "linear": normalize(raw_price),
#                         "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
#                         "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
#                     }
#                 except Exception:
#                     print(f"⚠️ price transform error for {price_col}, skipping.")
#                     continue
                
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # 计算RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, outflow_dict_lag)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 🔥 参数名称（仅BCH和BSV）
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "delta_BCH", "delta_BSV", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "delta_BCH", "delta_BSV", "m"]
                            
#                             row = {
#                                 "P_event": p_event_col,
#                                 "Q_event": q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf": pt_name,
#                                 "p_model": p_model,
#                                 "q_form": q_form,
#                                 "RMSE": rmse,
#                                 "SSE": sse,
#                                 "cond": float(getattr(res, "cond", np.nan))
#                             }
                            
#                             for i, name in enumerate(param_names):
#                                 row[name] = float(params[i]) if i < len(params) else np.nan
#                                 row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
#                                 row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
#                                 row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            
#                             results.append(row)
    
#     # 保存结果
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n{'='*80}")
#     print(f"✅ 完成！")
#     print(f"{'='*80}")
#     print(f"成功拟合: {combos_done} 个组合")
#     print(f"跳过: {combos_skipped} 个组合")
#     print(f"结果已保存: {OUTPUT_CSV}")
#     print(f"{'='*80}\n")

# if __name__ == "__main__":
#     main()



# 只用total_out一个作为负面效应，然后只有一个delta参数
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_daily_strict_rules.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "btc_bass_pqfit_results_exit_only_total_out.csv"  # 🔥 修改输出文件名

# # ===================================
# # ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     # "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     # "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]

# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     """标准化函数：均值0，标准差1"""
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- 🔥 加载total_out列 ---------
# def load_and_align_total_outflow(migration_path, main_df):
#     """
#     加载total_out列并对齐到主数据框的日期
    
#     Args:
#         migration_path: 迁移数据CSV路径
#         main_df: 主数据框（包含date列）
    
#     Returns:
#         total_out_aligned: 对齐后的总迁出数组
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n{'='*80}")
#     print(f"📊 加载总迁出数据（total_out列）")
#     print(f"{'='*80}")
#     print(f"迁移数据文件: {migration_path}")
#     print(f"迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"迁移数据行数: {len(df_mig)}")
    
#     # 检查total_out列
#     if 'total_out' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'total_out' 列")
#         return None
    
#     # 对齐到main_df的日期
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
#     df_full = pd.DataFrame({'date': main_dates})
    
#     # 合并
#     df_merged = df_full.merge(df_mig[['date', 'total_out']], on='date', how='left')
    
#     # 缺失日期填充为0
#     total_out_aligned = df_merged['total_out'].fillna(0).values
    
#     # 统计
#     total_sum = total_out_aligned.sum()
#     non_zero_days = (total_out_aligned > 0).sum()
    
#     print(f"\n📈 总迁出数据统计（窗口期内）:")
#     print(f"  总迁出人数:    {total_sum:,.0f}")
#     print(f"  非零天数:      {non_zero_days:,d} / {len(total_out_aligned):,d}")
#     print(f"  平均每天:      {total_out_aligned.mean():.2f}")
#     print(f"  标准差:        {total_out_aligned.std():.2f}")
#     print(f"  最大单日:      {total_out_aligned.max():.0f}")
    
#     if non_zero_days > 0:
#         print(f"  非零日均值:    {total_out_aligned[total_out_aligned > 0].mean():.2f}")
    
#     print(f"{'='*80}\n")
    
#     return total_out_aligned

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
#     """计算q(t)"""
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# # --------- p(t) 计算 ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """计算p(t)"""
#     ev = normalize(df[p_event_col].values)
#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * ev
#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
#     else:
#         raise ValueError("未知 p_model")
#     return np.maximum(p_t, 0)

# # --------- 🔥 Bass增量（总迁出负网络效应） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, total_out_lag, delta):
#     """
#     总迁出负网络效应的Bass模型
    
#     ΔN(t) = [p(t) + q(t)·X(t−1)/m − δ · total_out^norm(t−1)] · (m − X(t−1))
    
#     Args:
#         N_lag: X(t-1)，期初累积用户
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 固定市场容量
#         total_out_lag: 总迁出（滞后1期）
#         delta: 负网络效应系数（单个参数）
    
#     Returns:
#         ΔN(t) 预测值
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 🔥 总迁出的负网络效应
#     total_out_norm = normalize(total_out_lag)
#     negative_network = delta * total_out_norm
    
#     # 总扩散率 = 内生 - 负网络效应
#     total_rate = base_rate - negative_network
    
#     return total_rate * remaining

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
#     """计算预测值"""
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         delta = params[5]  # 🔥 单个δ参数
#         m = params[6]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         delta = params[6]  # 🔥 单个δ参数
#         m = params[7]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values
#     total_out_lag = df["total_out_lag"].values  # 🔥 使用total_out_lag
    
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, total_out_lag, delta)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
#     """计算残差"""
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[6]
#     else:
#         q0 = params[4]
#         m = params[7]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form):
#     """拟合Bass模型"""
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # 🔥 params: [p0, alpha, beta, q0, beta_q, delta_total, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001,  # 🔥 单个delta初始值
#                     m_guess]
#             bounds = ([0, -10, -10, 0, -10, 
#                       0,  # 🔥 delta >= 0
#                       0.9*m_guess],
#                       [1, 10, 10, 1, 10, 
#                        0.01,  # 🔥 delta上界
#                        20*m_guess])
#         else:
#             # 🔥 params: [p0, alpha, beta, gamma, q0, beta_q, delta_total, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 
#                     m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 
#                       0, 
#                       0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 
#                        0.01, 
#                        20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误、t值、p值
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T
        
#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except np.linalg.LinAlgError:
#             cond = np.nan
        
#         resid_vec = df[NEW_COL].values - y_pred
#         sigma2 = np.sum(resid_vec**2) / (n - k)
        
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except np.linalg.LinAlgError:
#             se = np.full(k, np.nan)
        
#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
#         return res
    
#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主数据
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     # 筛选日期窗口
#     df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
#                     (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
#     # 🔥 加载total_out数据
#     total_out_data = load_and_align_total_outflow(MIGRATION_PATH, df_raw)
    
#     if total_out_data is None:
#         print("⚠️ 无法加载迁出数据，程序退出")
#         sys.exit(1)
    
#     # 🔥 创建滞后1期的total_out
#     total_out_lag = np.concatenate([[0], total_out_data[:-1]])
    
#     # 🔥 添加到df_raw
#     df_raw['total_out'] = total_out_data
#     df_raw['total_out_lag'] = total_out_lag
#     df_raw['N_lag'] = df_raw[CUM_COL].shift(1).fillna(df_raw[CUM_COL].iloc[0])
    
#     # 🔥 诊断信息
#     final_cum = df_raw[CUM_COL].iloc[-1]
#     outflow_ratio = total_out_data.sum() / final_cum * 100
    
#     print(f"📊 迁出占比分析:")
#     print(f"  窗口期末累积用户: {final_cum:,.0f}")
#     print(f"  窗口期总迁出:     {total_out_data.sum():,.0f}")
#     print(f"  迁出占比:         {outflow_ratio:.2f}%")
    
#     if outflow_ratio < 2:
#         print(f"  ⚠️  迁出占比较小（<2%），δ可能不显著")
#     print()
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # 主循环
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # 检查列
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 选择数据
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
#                          'N_lag', 'total_out_lag'] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # 价格变换
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 try:
#                     price_transforms = {
#                         "linear": normalize(raw_price),
#                         "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
#                         "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
#                     }
#                 except Exception:
#                     print(f"⚠️ price transform error for {price_col}, skipping.")
#                     continue
                
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # 计算RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 🔥 参数名称（简化）
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "delta_total_out", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "delta_total_out", "m"]
                            
#                             row = {
#                                 "P_event": p_event_col,
#                                 "Q_event": q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf": pt_name,
#                                 "p_model": p_model,
#                                 "q_form": q_form,
#                                 "RMSE": rmse,
#                                 "SSE": sse,
#                                 "cond": float(getattr(res, "cond", np.nan))
#                             }
                            
#                             for i, name in enumerate(param_names):
#                                 row[name] = float(params[i]) if i < len(params) else np.nan
#                                 row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
#                                 row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
#                                 row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            
#                             results.append(row)
    
#     # 保存结果
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n{'='*80}")
#     print(f"✅ 完成！")
#     print(f"{'='*80}")
#     print(f"成功拟合: {combos_done} 个组合")
#     print(f"跳过: {combos_skipped} 个组合")
#     print(f"结果已保存: {OUTPUT_CSV}")
#     print(f"{'='*80}\n")

# if __name__ == "__main__":
#     main()


# 只用total_out的累积迁出比例作为负面效应

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
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
START_DATE = "2020-10-01"
END_DATE = "2021-10-01"
OUTPUT_CSV = "btc_bass_pqfit_results_exit_cumulative_ratio20202021.csv"  # 🔥 修改文件名

# ===================================
# ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
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

# ----------------- 工具函数 -----------------
def normalize(x):
    """标准化函数：均值0，标准差1"""
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

# --------- 🔥 加载并对齐迁出数据（使用total_out） ---------
def load_and_align_outflow_data(migration_path, main_df):
    """
    加载迁出数据并对齐到主数据框的日期
    
    🔥 修改：只使用total_out列（总迁出）
    
    Args:
        migration_path: 迁移数据CSV路径
        main_df: 主数据框（包含date列）
    
    Returns:
        total_out_array: 对齐后的总迁出数组
    """
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None
    
    print(f"\n{'='*80}")
    print(f"📊 加载迁出数据（累积比例模式）")
    print(f"{'='*80}")
    print(f"迁移数据文件: {migration_path}")
    print(f"迁移数据列名: {df_mig.columns.tolist()}")
    print(f"迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
    print(f"迁移数据行数: {len(df_mig)}")
    
    # 检查total_out列
    if 'total_out' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'total_out' 列")
        return None
    
    # 对齐到main_df的日期
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    df_full = pd.DataFrame({'date': main_dates})
    
    # 合并
    df_merged = df_full.merge(df_mig[['date', 'total_out']], on='date', how='left')
    
    # 缺失日期填充为0
    total_out_array = df_merged['total_out'].fillna(0).values
    
    # 🔥 统计
    total_sum = total_out_array.sum()
    non_zero_days = (total_out_array > 0).sum()
    
    print(f"\n📈 总迁出数据统计（窗口期内）:")
    print(f"🔥 使用累积迁出比例作为负网络效应指标")
    print(f"  总迁出人数:  {total_sum:,.0f}")
    print(f"  非零天数:    {non_zero_days} / {len(total_out_array)} ({non_zero_days/len(total_out_array)*100:.1f}%)")
    
    if non_zero_days > 0:
        print(f"  平均每天:    {total_out_array.mean():.2f}")
        print(f"  标准差:      {total_out_array.std():.2f}")
        print(f"  最大单日:    {total_out_array.max():.0f}")
        print(f"  非零日均值:  {total_out_array[total_out_array > 0].mean():.2f}")
    
    print(f"{'='*80}\n")
    
    return total_out_array

# --------- q(t) 计算 ----------
def compute_q_t_from_array(event_arr, q_params, q_form):
    """计算q(t)"""
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * ev)
    else:
        raise ValueError("未知 q_form")
    return q_t

# --------- p(t) 计算 ----------
def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    """计算p(t)"""
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

# --------- 🔥 Bass增量（累积迁出比例版本） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, outflow_ratio_norm, delta):
    """
    累积迁出比例的负网络效应Bass模型
    
    ΔN(t) = [p(t) + q(t)·X(t−1)/m − δ · outflow_ratio^norm(t−1)] · (m − X(t−1))
    
    其中：
        outflow_ratio(t-1) = cumulative_out(t-1) / X(t-1)
        outflow_ratio^norm = normalize(outflow_ratio)
    
    Args:
        N_lag: X(t-1)，期初累积用户
        p_t_arr: p(t) 数组
        q_t_arr: q(t) 数组
        m: 固定市场容量
        outflow_ratio_norm: 标准化的累积迁出比例
        delta: 负网络效应系数（单个参数）
    
    Returns:
        ΔN(t) 预测值
    """
    remaining = np.maximum(m - N_lag, 0)
    
    # Bass内生扩散率
    base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
    # 🔥 累积迁出比例的负网络效应
    negative_network = delta * outflow_ratio_norm
    
    # 总扩散率 = 内生 - 负网络效应
    total_rate = base_rate - negative_network
    
    return total_rate * remaining

# --------- compute_prediction ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
    """计算预测值"""
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q = params[3:5]
        delta = params[5]  # 🔥 单个δ参数
        m = params[6]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q = params[4:6]
        delta = params[6]  # 🔥 单个δ参数
        m = params[7]
    
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    N_lag = df["N_lag"].values
    
    # 🔥 使用预先计算的累积迁出比例
    outflow_ratio_norm = df["outflow_ratio_norm"].values
    
    dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, outflow_ratio_norm, delta)
    
    return dN, p_t, q_t

# --------- residuals ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
    """计算残差"""
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[6]
    else:
        q0 = params[4]
        m = params[7]
    
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    
    return df[NEW_COL].values - dN_predicted

# --------- fit ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form):
    """拟合Bass模型"""
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            # 🔥 params: [p0, alpha, beta, q0, beta_q, delta, m]
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 
                    0.001,  # 🔥 delta初始值（单个参数）
                    m_guess]
            bounds = ([0, -10, -10, 0, -10, 
                      0,  # 🔥 delta >= 0
                      0.9*m_guess],
                      [1, 10, 10, 1, 10, 
                       0.1,  # 🔥 delta上界（更大，因为是比例）
                       20*m_guess])
        else:
            # 🔥 params: [p0, alpha, beta, gamma, q0, beta_q, delta, m]
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
                    0.001, 
                    m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 
                      0, 
                      0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 
                       0.1, 
                       20*m_guess])
        
        res = least_squares(residuals_pair, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form), 
                            method="trf")
        
        if not res.success:
            return None
        
        params = res.x
        
        # 计算标准误、t值、p值
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
        
        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
        return res
    
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None

# ----------------- 主程序 -----------------
def main():
    # 读取主数据
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)
    
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
    # 筛选日期窗口
    df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
                    (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    # 🔥 加载迁出数据（total_out）
    total_out_array = load_and_align_outflow_data(MIGRATION_PATH, df_raw)
    
    if total_out_array is None:
        print("⚠️ 无法加载迁出数据，程序退出")
        sys.exit(1)
    
    # 🔥 计算累积迁出
    cumulative_out = np.cumsum(total_out_array)
    
    # 🔥 滞后1期
    cumulative_out_lag = np.concatenate([[0], cumulative_out[:-1]])
    
    # 🔥 添加到df_raw
    df_raw['total_out'] = total_out_array
    df_raw['cumulative_out'] = cumulative_out
    df_raw['cumulative_out_lag'] = cumulative_out_lag
    
    # 添加N_lag
    df_raw['N_lag'] = df_raw[CUM_COL].shift(1).fillna(df_raw[CUM_COL].iloc[0])
    
    # 🔥 计算累积迁出比例 = cumulative_out(t-1) / X(t-1)
    # 避免除以0
    outflow_ratio = cumulative_out_lag / (df_raw['N_lag'] + 1)
    
    # 🔥 标准化
    outflow_ratio_norm = normalize(outflow_ratio)
    
    df_raw['outflow_ratio'] = outflow_ratio
    df_raw['outflow_ratio_norm'] = outflow_ratio_norm
    
    # 🔥 诊断信息
    print(f"\n📊 累积迁出比例统计:")
    print(f"{'='*80}")
    print(f"  最终累积用户（X）:        {df_raw[CUM_COL].iloc[-1]:,.0f}")
    print(f"  最终累积迁出:              {cumulative_out[-1]:,.0f}")
    print(f"  最终迁出比例:              {outflow_ratio.iloc[-1]*100:.2f}%")
    print(f"  平均迁出比例:              {outflow_ratio.mean()*100:.2f}%")
    print(f"  迁出比例标准差:            {outflow_ratio.std()*100:.2f}%")
    print(f"  迁出比例最大值:            {outflow_ratio.max()*100:.2f}%")
    print(f"{'='*80}\n")
    
    results = []
    combos_done = 0
    combos_skipped = 0
    
    total_price_cols = [c for c in PRICE_LAG_COLS]
    total_p_events = [c for c in P_EVENT_LIST]
    total_q_events = [c for c in Q_EVENT_LIST]
    
    # 主循环
    for p_event_col in total_p_events:
        for q_event_col in total_q_events:
            # 检查列
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # 选择数据
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
                         'N_lag', 'outflow_ratio_norm'] + total_price_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            
            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # 价格变换
            for price_col in total_price_cols:
                raw_price = df[price_col].values.astype(float)
                
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    print(f"⚠️ price transform error for {price_col}, skipping.")
                    continue
                
                for pt_name, price_arr in price_transforms.items():
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
                            print(f"\n→ 拟合: {model_tag}")
                            
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form)
                            
                            if res is None:
                                print(" ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue
                            
                            combos_done += 1
                            params = res.x
                            
                            # 计算RMSE/SSE
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
                            # 🔥 参数名称（简化为单个delta）
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", "delta", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "delta", "m"]
                            
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
    
    # 保存结果
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n{'='*80}")
    print(f"✅ 完成！")
    print(f"{'='*80}")
    print(f"成功拟合: {combos_done} 个组合")
    print(f"跳过: {combos_skipped} 个组合")
    print(f"结果已保存: {OUTPUT_CSV}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()