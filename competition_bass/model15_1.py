# 在model12_1基础上用真实的迁入数据
# Δ𝑋_𝐵𝑇𝐶 (𝑡)=[𝑝(𝑡)+𝑞(𝑡)(𝑋_𝐵𝑇𝐶 (𝑡−1))/𝑚+∑_(𝑗∈𝒞)▒𝛾_(𝑗→𝐵𝑇𝐶)(𝑀_(𝑗→𝐵𝑇𝐶) (𝑡))/𝑚]⋅(𝑚−𝑋_𝐵𝑇𝐶 (𝑡−1))
# 2017.01.01-2019.01.01阶段中Dogecoin和BSV的gamma系数不显著
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
# OUTPUT_CSV = "btc_bass_pqfit_results_competition.csv"

# # 竞争币种列表
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# # ===================================
# # ============= 显式写入你要求的 P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]

# # ============= 价格滞后变量集合（你要求的） =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- q(t) 计算（使用指定的 QEVENT 列） ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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

# # --------- p(t) 计算（price_array 已由外部转换/normalize） ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """
#     params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     price_array: already-normalized numpy array for price transform
#     p_event_col: column name in df for p-event (raw values)
#     returns p_t (array)
#     """
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

# # --------- Bass 增量（加入竞争迁入项） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     计算 ΔX_BTC(t) = [p(t) + q(t)*N(t-1)/m + Σ γ_j * M_j(t)/m] * (m - N(t-1))
    
#     Args:
#         N_lag: N(t-1) 数组
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 市场容量
#         migration_dict: {coin: migration_array} 字典
#         gamma_params: [gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin]
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # 基础扩散率: p(t) + q(t) * N(t-1)/m
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 竞争迁入率: Σ γ_j * M_j(t)/m
#     migration_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             migration_rate += gamma_params[i] * (migration_dict[coin] / m)
    
#     # 总扩散率
#     total_rate = base_rate + migration_rate
    
#     return total_rate * remaining

# # --------- compute_prediction 针对单个组合 ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     params layout depends on p_model:
#       if p_model in ['additive','nonlinear_event']:
#          params = [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#       else:
#          params = [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     """
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:10]  # 5个竞争币种的gamma
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:11]  # 5个竞争币种的gamma
#         m = params[11]
    
#     # p_t from price_array and p-event column
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    
#     # q_t from q-event column
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # N_lag
#     N_lag = df["N_lag"].values
    
#     # 计算增量（含竞争迁入）
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals for least_squares ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     # basic checks for param plausibility
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit for one pair ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     Fit params for given df (which must have N_lag and event cols).
#     Returns res or None on failure.
#     """
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # params: [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
#         else:
#             # params: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # compute numeric jacobian for se/t/p
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载并处理迁移数据 ----------
# def load_migration_data(migration_path, main_df):
#     """
#     读取迁移数据并对齐到主数据框的日期
#     返回: {coin: migration_array} 字典
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         # 自动解析日期列（支持多种格式）
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")
    
#     # 确保日期列名一致
#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列")
#         return None
    
#     # 创建完整日期范围的数据框（与主数据框对齐）
#     date_range = pd.date_range(start=main_df[DATE_COL].min(), 
#                                end=main_df[DATE_COL].max(), 
#                                freq='D')
#     df_full = pd.DataFrame({DATE_COL: date_range})
    
#     # 合并迁移数据（左连接，缺失值填充为0）
#     df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
#     # 列名映射：代码中的币种名 -> CSV文件中的列名
#     col_mapping = {
#         "BCH": "in_from_BCH",
#         "BSV": "in_from_BSV",
#         "ETH": "in_from_ETH",
#         "LTC": "in_from_LTC",
#         "Dogecoin": "in_from_DOGE"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
#         else: 
#             print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
#             migration_dict[coin] = np.zeros(len(df_merged))

#     # 只保留与main_df日期对应的部分
#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)

#     migration_dict_aligned = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             # 对齐到main_df的日期索引
#             aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             migration_dict_aligned[coin] = aligned
#         else:
#             migration_dict_aligned[coin] = np.zeros(len(main_df))
    
#     # 打印迁移数据的基本统计
#     print("\n📈 迁移数据统计（窗口期内）:")
#     for coin in COMPETITORS:
#         total = np.sum(migration_dict_aligned[coin])
#         non_zero_days = np.sum(migration_dict_aligned[coin] > 0)
#         if non_zero_days > 0:
#             max_daily = np.max(migration_dict_aligned[coin])
#             mean_daily = np.mean(migration_dict_aligned[coin][migration_dict_aligned[coin] > 0])
#             print(f"  {coin:10s}: 总迁入={total:6.0f}, 非零天数={non_zero_days:4.0f}, 最大单日={max_daily:5.0f}, 非零日均={mean_daily:6.2f}")
#         else:
#             print(f"  {coin:10s}: 总迁入=     0, 非零天数=   0 (窗口期内无迁入数据)")
    
#     return migration_dict_aligned

# # ----------------- 主程序 -----------------
# def main():
#     # 读取全表一次，后续切片
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     # ensure date ordering
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # iterate all P x Q combos
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # check the required columns exist for combinations
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
#                 combos_skipped += 1
#                 continue
            
#             # select date window
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # add N_lag = N(t-1) (first row fill with initial cum)
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 加载迁移数据（对齐到当前df的日期）
#             migration_dict = load_migration_data(MIGRATION_PATH, df)
#             if migration_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # iterate price cols and transforms
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 # three transforms: linear, log, exp (normalized)
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
#                     # loop p_model and q_form
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # compute prediction to get RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # param names depending on p_model
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
                            
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
    
#     # write results to csv
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()


# ===================================
# 没有除以m：Δ𝑋_𝐵𝑇𝐶 (𝑡)=[𝑝(𝑡)+𝑞(𝑡)(𝑋_𝐵𝑇𝐶 (𝑡−1))/𝑚+∑_(𝑗∈𝒞)▒𝛾_(𝑗→𝐵𝑇𝐶)(𝑀_(𝑗→𝐵𝑇𝐶) (𝑡))]⋅(𝑚−𝑋_𝐵𝑇𝐶 (𝑡−1))
# 结果不同在于gamma系数变小
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
# OUTPUT_CSV = "btc_bass_pqfit_results_competition.csv"

# # 竞争币种列表
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# # ===================================
# # ============= 显式写入你要求的 P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
# ]

# # ============= 价格滞后变量集合（你要求的） =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- q(t) 计算（使用指定的 QEVENT 列） ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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

# # --------- p(t) 计算（price_array 已由外部转换/normalize） ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """
#     params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     price_array: already-normalized numpy array for price transform
#     p_event_col: column name in df for p-event (raw values)
#     returns p_t (array)
#     """
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

# # --------- Bass 增量（加入竞争迁入项，不除以m） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     计算 ΔX_BTC(t) = [p(t) + q(t)*N(t-1)/m + Σ γ_j * M_j(t-1)] * (m - N(t-1))
    
#     注意：迁移项现在不除以m了！
    
#     Args:
#         N_lag: N(t-1) 数组
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 市场容量
#         migration_dict: {coin: migration_array} 字典
#         gamma_params: [gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin]
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # 基础扩散率: p(t) + q(t) * N(t-1)/m
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 竞争迁入率: Σ γ_j * M_j(t-1)  【修改：不除以m了】
#     migration_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             migration_rate += gamma_params[i] * migration_dict[coin]
    
#     # 总扩散率
#     total_rate = base_rate + migration_rate
    
#     return total_rate * remaining

# # --------- compute_prediction 针对单个组合 ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     params layout depends on p_model:
#       if p_model in ['additive','nonlinear_event']:
#          params = [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#       else:
#          params = [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     """
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:10]  # 5个竞争币种的gamma
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:11]  # 5个竞争币种的gamma
#         m = params[11]
    
#     # p_t from price_array and p-event column
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    
#     # q_t from q-event column
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # N_lag
#     N_lag = df["N_lag"].values
    
#     # 计算增量（含竞争迁入）
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals for least_squares ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     # basic checks for param plausibility
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit for one pair ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     Fit params for given df (which must have N_lag and event cols).
#     Returns res or None on failure.
#     """
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # params: [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
#         else:
#             # params: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # compute numeric jacobian for se/t/p
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载并处理迁移数据 ----------
# def load_migration_data(migration_path, main_df):
#     """
#     读取迁移数据并对齐到主数据框的日期
#     返回: {coin: migration_array} 字典
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         # 自动解析日期列（支持多种格式）
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")
    
#     # 确保日期列名一致
#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列")
#         return None
    
#     # 创建完整日期范围的数据框（与主数据框对齐）
#     date_range = pd.date_range(start=main_df[DATE_COL].min(), 
#                                end=main_df[DATE_COL].max(), 
#                                freq='D')
#     df_full = pd.DataFrame({DATE_COL: date_range})
    
#     # 合并迁移数据（左连接，缺失值填充为0）
#     df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
#     # 列名映射：代码中的币种名 -> CSV文件中的列名
#     col_mapping = {
#         "BCH": "in_from_BCH",
#         "BSV": "in_from_BSV",
#         "ETH": "in_from_ETH",
#         "LTC": "in_from_LTC",
#         "Dogecoin": "in_from_DOGE"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
#             migration_dict[coin] = np.zeros(len(df_merged))
    
#     # 只保留与main_df日期对应的部分
#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
#     migration_dict_aligned = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             # 对齐到main_df的日期索引
#             aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             migration_dict_aligned[coin] = aligned
#         else:
#             migration_dict_aligned[coin] = np.zeros(len(main_df))
    
#     # 打印迁移数据的基本统计
#     print("\n📈 迁移数据统计（窗口期内）:")
#     for coin in COMPETITORS:
#         total = np.sum(migration_dict_aligned[coin])
#         non_zero_days = np.sum(migration_dict_aligned[coin] > 0)
#         if non_zero_days > 0:
#             max_daily = np.max(migration_dict_aligned[coin])
#             mean_daily = np.mean(migration_dict_aligned[coin][migration_dict_aligned[coin] > 0])
#             print(f"  {coin:10s}: 总迁入={total:6.0f}, 非零天数={non_zero_days:4.0f}, 最大单日={max_daily:5.0f}, 非零日均={mean_daily:6.2f}")
#         else:
#             print(f"  {coin:10s}: 总迁入=     0, 非零天数=   0 (窗口期内无迁入数据)")
    
#     return migration_dict_aligned

# # ----------------- 主程序 -----------------
# def main():
#     # 读取全表一次，后续切片
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     # ensure date ordering
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # iterate all P x Q combos
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # check the required columns exist for combinations
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
#                 combos_skipped += 1
#                 continue
            
#             # select date window
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # add N_lag = N(t-1) (first row fill with initial cum)
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 加载迁移数据（对齐到当前df的日期）
#             migration_dict = load_migration_data(MIGRATION_PATH, df)
#             if migration_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # iterate price cols and transforms
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 # three transforms: linear, log, exp (normalized)
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
#                     # loop p_model and q_form
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # compute prediction to get RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # param names depending on p_model
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
                            
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
    
#     # write results to csv
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()


# ===================================
# 没有除以m：Δ𝑋_𝐵𝑇𝐶 (𝑡)=[𝑝(𝑡)+𝑞(𝑡)(𝑋_𝐵𝑇𝐶 (𝑡−1))/𝑚+∑_(𝑗∈𝒞)▒𝛾_(𝑗→𝐵𝑇𝐶)(𝑀_(𝑗→𝐵𝑇𝐶) (𝑡-1))]⋅(𝑚−𝑋_𝐵𝑇𝐶 (𝑡−1))
# 改成了𝑀_(𝑗→𝐵𝑇𝐶) (𝑡-1) RMSE变高，多了更多不显著的系数
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
# OUTPUT_CSV = "btc_bass_pqfit_results_competition_t-1.csv"

# # 竞争币种列表
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# # ===================================
# # ============= 显式写入你要求的 P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
# ]

# # ============= 价格滞后变量集合（你要求的） =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- q(t) 计算（使用指定的 QEVENT 列） ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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

# # --------- p(t) 计算（price_array 已由外部转换/normalize） ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """
#     params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     price_array: already-normalized numpy array for price transform
#     p_event_col: column name in df for p-event (raw values)
#     returns p_t (array)
#     """
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

# # --------- Bass 增量（加入竞争迁入项，不除以m） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     计算 ΔX_BTC(t) = [p(t) + q(t)*N(t-1)/m + Σ γ_j * M_j(t-1)] * (m - N(t-1))
    
#     注意：迁移项现在不除以m了！
    
#     Args:
#         N_lag: N(t-1) 数组
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 市场容量
#         migration_dict: {coin: migration_array} 字典（已经是lag1数据）
#         gamma_params: [gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin]
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # 基础扩散率: p(t) + q(t) * N(t-1)/m
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 竞争迁入率: Σ γ_j * M_j(t-1)  【修改：不除以m了】
#     migration_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             migration_rate += gamma_params[i] * migration_dict[coin]
    
#     # 总扩散率
#     total_rate = base_rate + migration_rate
    
#     return total_rate * remaining

# # --------- compute_prediction 针对单个组合 ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     params layout depends on p_model:
#       if p_model in ['additive','nonlinear_event']:
#          params = [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#       else:
#          params = [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     """
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:10]  # 5个竞争币种的gamma
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:11]  # 5个竞争币种的gamma
#         m = params[11]
    
#     # p_t from price_array and p-event column
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    
#     # q_t from q-event column
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # N_lag
#     N_lag = df["N_lag"].values
    
#     # 计算增量（含竞争迁入）
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals for least_squares ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     # basic checks for param plausibility
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit for one pair ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     Fit params for given df (which must have N_lag and event cols).
#     Returns res or None on failure.
#     """
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # params: [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
#         else:
#             # params: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, -10, -10, -10, -10, -10, 0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # compute numeric jacobian for se/t/p
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载并处理迁移数据（修改：返回lag1数据） ----------
# def load_migration_data(migration_path, main_df):
#     """
#     读取迁移数据并对齐到主数据框的日期
#     返回: {coin: migration_lag1_array} 字典（M_j(t-1)）
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         # 自动解析日期列（支持多种格式）
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")
    
#     # 确保日期列名一致
#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列")
#         return None
    
#     # 创建完整日期范围的数据框（与主数据框对齐）
#     date_range = pd.date_range(start=main_df[DATE_COL].min(), 
#                                end=main_df[DATE_COL].max(), 
#                                freq='D')
#     df_full = pd.DataFrame({DATE_COL: date_range})
    
#     # 合并迁移数据（左连接，缺失值填充为0）
#     df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
#     # 列名映射：代码中的币种名 -> CSV文件中的列名
#     col_mapping = {
#         "BCH": "in_from_BCH",
#         "BSV": "in_from_BSV",
#         "ETH": "in_from_ETH",
#         "LTC": "in_from_LTC",
#         "Dogecoin": "in_from_DOGE"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
#             migration_dict[coin] = np.zeros(len(df_merged))
    
#     # 只保留与main_df日期对应的部分
#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
#     migration_dict_aligned = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             # 对齐到main_df的日期索引
#             aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             migration_dict_aligned[coin] = aligned
#         else:
#             migration_dict_aligned[coin] = np.zeros(len(main_df))
    
#     # 🔧 关键修改：将 M_j(t) 转换为 M_j(t-1)
#     print("\n⚠️ 注意：迁移数据已滞后1天 (M_j(t) → M_j(t-1))")
    
#     migration_dict_lag1 = {}
#     for coin in COMPETITORS:
#         data = migration_dict_aligned[coin]
#         # 向后移动1天：第一个元素设为0，后面的元素前移
#         data_lag1 = np.concatenate([[0], data[:-1]])
#         migration_dict_lag1[coin] = data_lag1
    
#     # 打印迁移数据的基本统计（使用lag1数据）
#     print("\n📈 迁移数据统计（窗口期内，已滞后1天）:")
#     for coin in COMPETITORS:
#         total = np.sum(migration_dict_lag1[coin])
#         non_zero_days = np.sum(migration_dict_lag1[coin] > 0)
#         if non_zero_days > 0:
#             max_daily = np.max(migration_dict_lag1[coin])
#             mean_daily = np.mean(migration_dict_lag1[coin][migration_dict_lag1[coin] > 0])
#             print(f"  {coin:10s}: 总迁入={total:6.0f}, 非零天数={non_zero_days:4.0f}, 最大单日={max_daily:5.0f}, 非零日均={mean_daily:6.2f}")
#         else:
#             print(f"  {coin:10s}: 总迁入=     0, 非零天数=   0 (窗口期内无迁入数据)")
    
#     return migration_dict_lag1

# # ----------------- 主程序 -----------------
# def main():
#     # 读取全表一次，后续切片
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     # ensure date ordering
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # iterate all P x Q combos
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # check the required columns exist for combinations
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
#                 combos_skipped += 1
#                 continue
            
#             # select date window
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # add N_lag = N(t-1) (first row fill with initial cum)
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 加载迁移数据（对齐到当前df的日期，已转换为lag1）
#             migration_dict = load_migration_data(MIGRATION_PATH, df)
#             if migration_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # iterate price cols and transforms
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 # three transforms: linear, log, exp (normalized)
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
#                     # loop p_model and q_form
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # compute prediction to get RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # param names depending on p_model
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
                            
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
    
#     # write results to csv
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()
    

# ==================================
# 形式2：迁入作为独立项
# ΔNBTC(t)=[p(t)+q(t)X(t−1)m]⋅[m−X(t−1)]+∑jγjMj(t)\boxed{\Delta N_{BTC}(t) = \left[p(t) + q(t)\frac{X(t-1)}{m}\right] \cdot [m - X(t-1)] + \sum_j \gamma_j M_j(t)}ΔNBTC​(t)=[p(t)+q(t)mX(t−1)​]⋅[m−X(t−1)]+j∑​γj​Mj​(t)​
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
# OUTPUT_CSV = "btc_bass_pqfit_results_competition_independent.csv"

# # 竞争币种列表
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# # ===================================
# # ============= 显式写入你要求的 P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
# ]

# # ============= 价格滞后变量集合（你要求的） =============
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- q(t) 计算（使用指定的 QEVENT 列） ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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

# # --------- p(t) 计算（price_array 已由外部转换/normalize） ----------
# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     """
#     params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     price_array: already-normalized numpy array for price transform
#     p_event_col: column name in df for p-event (raw values)
#     returns p_t (array)
#     """
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

# # --------- Bass 增量（形式2：迁入作为独立项） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     计算 ΔX_BTC(t) = [p(t) + q(t)*N(t-1)/m] * (m - N(t-1)) + Σ γ_j * M_j(t)
    
#     形式2：迁入作为独立项，不受市场容量约束
    
#     Args:
#         N_lag: N(t-1) 数组
#         p_t_arr: p(t) 数组
#         q_t_arr: q(t) 数组
#         m: 市场容量（仅约束Bass内生扩散）
#         migration_dict: {coin: migration_array} 字典
#         gamma_params: [gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin]
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散（受市场容量约束）
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
#     bass_growth = base_rate * remaining
    
#     # 外生迁入贡献（不受市场容量约束）
#     migration_contribution = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             migration_contribution += gamma_params[i] * migration_dict[coin]
    
#     # 总增长 = Bass增长 + 迁入贡献
#     return bass_growth + migration_contribution

# # --------- compute_prediction 针对单个组合 ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     params layout depends on p_model:
#       if p_model in ['additive','nonlinear_event']:
#          params = [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#       else:
#          params = [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#     """
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:10]  # 5个竞争币种的gamma
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:11]  # 5个竞争币种的gamma
#         m = params[11]
    
#     # p_t from price_array and p-event column
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    
#     # q_t from q-event column
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # N_lag
#     N_lag = df["N_lag"].values
    
#     # 计算增量（形式2：迁入作为独立项）
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals for least_squares ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     # basic checks for param plausibility
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit for one pair ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """
#     Fit params for given df (which must have N_lag and event cols).
#     Returns res or None on failure.
#     """
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # params: [p0, alpha, beta, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 1.0, 1.0, 1.0, 1.0, 1.0, m_guess]
#             bounds = ([0, -10, -10, 0, -10, 0, 0, 0, 0, 0, 0.9*m_guess],
#                       [1, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
#         else:
#             # params: [p0, alpha, beta, gamma, q0, beta_q, gamma_BCH, gamma_BSV, gamma_ETH, gamma_LTC, gamma_Dogecoin, m]
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 1.0, 1.0, 1.0, 1.0, 1.0, m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 0, 0, 0, 0, 0, 0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 10, 10, 10, 10, 10, 20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # compute numeric jacobian for se/t/p
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载并处理迁移数据 ----------
# def load_migration_data(migration_path, main_df):
#     """
#     读取迁移数据并对齐到主数据框的日期
#     返回: {coin: migration_array} 字典
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         # 自动解析日期列（支持多种格式）
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")
    
#     # 确保日期列名一致
#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列")
#         return None
    
#     # 创建完整日期范围的数据框（与主数据框对齐）
#     date_range = pd.date_range(start=main_df[DATE_COL].min(), 
#                                end=main_df[DATE_COL].max(), 
#                                freq='D')
#     df_full = pd.DataFrame({DATE_COL: date_range})
    
#     # 合并迁移数据（左连接，缺失值填充为0）
#     df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
#     # 列名映射：代码中的币种名 -> CSV文件中的列名
#     col_mapping = {
#         "BCH": "in_from_BCH",
#         "BSV": "in_from_BSV",
#         "ETH": "in_from_ETH",
#         "LTC": "in_from_LTC",
#         "Dogecoin": "in_from_DOGE"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
#             migration_dict[coin] = np.zeros(len(df_merged))
    
#     # 只保留与main_df日期对应的部分
#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
#     migration_dict_aligned = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             # 对齐到main_df的日期索引
#             aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             migration_dict_aligned[coin] = aligned
#         else:
#             migration_dict_aligned[coin] = np.zeros(len(main_df))
    
#     # 打印迁移数据的基本统计
#     print("\n📈 迁移数据统计（窗口期内）:")
#     print("⚠️  注意：使用形式2，迁入作为独立项，不受市场容量约束")
#     for coin in COMPETITORS:
#         total = np.sum(migration_dict_aligned[coin])
#         non_zero_days = np.sum(migration_dict_aligned[coin] > 0)
#         if non_zero_days > 0:
#             max_daily = np.max(migration_dict_aligned[coin])
#             mean_daily = np.mean(migration_dict_aligned[coin][migration_dict_aligned[coin] > 0])
#             print(f"  {coin:10s}: 总迁入={total:6.0f}, 非零天数={non_zero_days:4.0f}, 最大单日={max_daily:5.0f}, 非零日均={mean_daily:6.2f}")
#         else:
#             print(f"  {coin:10s}: 总迁入=     0, 非零天数=   0 (窗口期内无迁入数据)")
    
#     return migration_dict_aligned

# # ----------------- 主程序 -----------------
# def main():
#     # 读取全表一次，后续切片
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     # ensure date ordering
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     total_price_cols = [c for c in PRICE_LAG_COLS]
#     total_p_events = [c for c in P_EVENT_LIST]
#     total_q_events = [c for c in Q_EVENT_LIST]
    
#     # iterate all P x Q combos
#     for p_event_col in total_p_events:
#         for q_event_col in total_q_events:
#             # check the required columns exist for combinations
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
#                 combos_skipped += 1
#                 continue
            
#             # select date window
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # add N_lag = N(t-1) (first row fill with initial cum)
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 加载迁移数据（对齐到当前df的日期）
#             migration_dict = load_migration_data(MIGRATION_PATH, df)
#             if migration_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # iterate price cols and transforms
#             for price_col in total_price_cols:
#                 raw_price = df[price_col].values.astype(float)
                
#                 # three transforms: linear, log, exp (normalized)
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
#                     # loop p_model and q_form
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
#                             print(f"\n→ 拟合: {model_tag}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # compute prediction to get RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # param names depending on p_model
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_Dogecoin", "m"]
                            
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
    
#     # write results to csv
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()

# ========
# 独立项+网络效应扩散速度 但网络效应中用的是Mj(t)且标准化,独立项用Mj(t)且不标准化 btc
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
OUTPUT_CSV = "btc_bass_pqfit_results_competition_dependent+speed_notlag_standardized20202021.csv"  # 修改文件名

# 竞争币种列表
COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

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

# --------- q(t) 计算 ----------
def compute_q_t_from_array(event_arr, q_params, q_form):
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

# --------- Bass 增量（形式3：标准化迁移的网络效应） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
    """
    形式3（标准化版本）：
    
    ΔN(t) = [p(t) + q(t)·X(t-1)/m + Σγ_j·M_j^norm(t)] · (m-X(t-1)) + Σ M_j(t)
    
    关键修改：
    - 网络效应项使用标准化的 M_j(t)
    - 直接迁入项使用原始的 M_j(t)
    
    Args:
        N_lag: N(t-1) 数组
        p_t_arr: p(t) 数组
        q_t_arr: q(t) 数组
        m: 市场容量
        migration_dict: {coin: migration_array} 字典（原始值）
        gamma_params: [γ_BCH, γ_BSV, γ_ETH, γ_LTC, γ_Dogecoin]（标准化系数）
    """
    remaining = np.maximum(m - N_lag, 0)
    
    # Bass内生扩散率
    base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
    # 🔥 关键修改：迁入网络效应（使用标准化的M）
    migration_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in migration_dict:
            M_raw = migration_dict[coin]  # 原始迁入数据
            M_norm = normalize(M_raw)      # 🔥 标准化
            migration_network_rate += gamma_params[i] * M_norm
    
    # 总扩散率（受市场容量约束）
    total_rate = base_rate + migration_network_rate
    constrained_growth = total_rate * remaining
    
    # 🔥 直接迁入（使用原始值，不标准化）
    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in migration_dict:
            direct_migration += migration_dict[coin]  # 原始值
    
    # 总增长
    return constrained_growth + direct_migration

# --------- compute_prediction ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
    """计算预测值"""
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q = params[3:5]
        gamma_params = params[5:10]
        m = params[10]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q = params[4:6]
        gamma_params = params[6:11]
        m = params[11]
    
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    N_lag = df["N_lag"].values
    
    dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
    return dN, p_t, q_t

# --------- residuals ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
    """计算残差"""
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[10]
    else:
        q0 = params[4]
        m = params[11]
    
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    
    return df[NEW_COL].values - dN_predicted

# --------- fit ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
    """拟合Bass模型"""
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            # 🔥 修改：γ初始值和边界（标准化后）
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 
                    0.0001, 0.0001, 0.0001, 0.0001, 0.0001,  # gamma初始值
                    m_guess]
            bounds = ([0, -10, -10, 0, -10, 
                      -0.01, -0.01, -0.01, -0.01, -0.01,  # gamma下界
                      0.9*m_guess],
                      [1, 10, 10, 1, 10, 
                       0.01, 0.01, 0.01, 0.01, 0.01,  # gamma上界
                       20*m_guess])
        else:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
                    0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 
                    m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 
                      -0.01, -0.01, -0.01, -0.01, -0.01, 
                      0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 
                       0.01, 0.01, 0.01, 0.01, 0.01, 
                       20*m_guess])
        
        res = least_squares(residuals_pair, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
                            method="trf")
        
        if not res.success:
            return None
        
        params = res.x
        
        # 计算标准误、t值、p值
        eps = 1e-6
        n = len(df)
        k = len(params)
        
        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# --------- 加载迁移数据 ----------
def load_migration_data(migration_path, main_df):
    """
    读取迁移数据并对齐到主数据框的日期
    返回: {coin: migration_array} 字典（原始值）
    """
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None
    
    print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
    print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
    print(f"📊 迁移数据行数: {len(df_mig)}")
    
    if 'date' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'date' 列")
        return None
    
    # 创建完整日期范围
    date_range = pd.date_range(start=main_df[DATE_COL].min(), 
                               end=main_df[DATE_COL].max(), 
                               freq='D')
    df_full = pd.DataFrame({DATE_COL: date_range})
    
    # 合并
    df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
    # 列名映射
    col_mapping = {
        "BCH": "in_from_BCH",
        "BSV": "in_from_BSV",
        "ETH": "in_from_ETH",
        "LTC": "in_from_LTC",
        "Dogecoin": "in_from_DOGE"
    }
    
    # 构建迁移字典
    migration_dict = {}
    for coin in COMPETITORS:
        actual_col = col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            migration_dict[coin] = df_merged[actual_col].fillna(0).values
            print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
        else:
            print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
            migration_dict[coin] = np.zeros(len(df_merged))
    
    # 对齐到main_df
    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
    migration_dict_aligned = {}
    for coin in COMPETITORS:
        actual_col = col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
            migration_dict_aligned[coin] = aligned
        else:
            migration_dict_aligned[coin] = np.zeros(len(main_df))
    
    # 打印统计
    print("\n📈 迁移数据统计（窗口期内）:")
    print("🔥 方法2：网络效应项使用标准化M，直接迁入项使用原始M")
    for coin in COMPETITORS:
        M_raw = migration_dict_aligned[coin]
        total = np.sum(M_raw)
        non_zero_days = np.sum(M_raw > 0)
        if non_zero_days > 0:
            max_daily = np.max(M_raw)
            mean_daily = np.mean(M_raw)
            std_daily = np.std(M_raw)
            print(f"  {coin:10s}: 总数={total:6.0f}, 非零天数={non_zero_days:4d}, "
                  f"均值={mean_daily:5.2f}, 标准差={std_daily:5.2f}, 最大={max_daily:5.0f}")
        else:
            print(f"  {coin:10s}: 总数=     0, 非零天数=   0 (无数据)")
    
    return migration_dict_aligned

# ----------------- 主程序 -----------------
def main():
    # 读取主数据
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)
    
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
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
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
                combos_skipped += 1
                continue
            
            # 选择日期窗口
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # N_lag
            df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
            # 加载迁移数据
            migration_dict = load_migration_data(MIGRATION_PATH, df)
            if migration_dict is None:
                print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
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
                            
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
                            if res is None:
                                print(" ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue
                            
                            combos_done += 1
                            params = res.x
                            
                            # 计算RMSE/SSE
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
                            # 🔥 修改参数名称（标准化版本）
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
                                             "gamma_std_BCH", "gamma_std_BSV", "gamma_std_ETH", 
                                             "gamma_std_LTC", "gamma_std_Dogecoin", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
                                             "gamma_std_BCH", "gamma_std_BSV", "gamma_std_ETH", 
                                             "gamma_std_LTC", "gamma_std_Dogecoin", "m"]
                            
                            # 保存结果
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
    
    print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()
    

# ========
# 独立项+网络效应扩散速度 但网络效应中用的是Mj(t)且标准化,独立项用Mj(t)且不标准化 但是是eth
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"  # 🔥 ETH数据
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"  # 🔥 ETH迁移数据
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"  # 🔥 修改为ETH
# CUM_COL = "eth_cum_users"  # 🔥 修改为ETH
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "eth_bass_pqfit_results_competition_dependent+speed_notlag_standardized.csv"  # 🔥 ETH输出文件

# # 🔥 竞争币种列表（ETH的竞争对手）
# COMPETITORS = ["BTC", "SOLANA", "BNB", "OPTIMISM", "APTOS", "SUI", "NEAR", "ZKSYNC", "ARBITRUM", "HARMONY", "ETC", "ETHPOW"]

# # ===================================
# # ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "eth_p_event_lag1", "eth_p_event_sum_7", "eth_p_event_mean_7", "eth_p_event_vol_7",  # 🔥 修改为ETH
#     "eth_p_eip_p_event_lag1", "eth_p_eip_p_event_sum_7", "eth_p_eip_p_event_mean_7", "eth_p_eip_p_event_vol_7",  # 🔥 EIP
#     "eth_p_eip_event_lag1", "eth_p_eip_event_sum_7", "eth_p_eip_event_mean_7", "eth_p_eip_event_vol_7"  # 🔥 EIP
# ]
# Q_EVENT_LIST = [
#     "eth_q_event_lag1", "eth_q_event_sum_7", "eth_q_event_mean_7",  # 🔥 修改为ETH
#     "eth_q_eip_q_event_lag1", "eth_q_eip_q_event_sum_7", "eth_q_eip_q_event_mean_7",  # 🔥 EIP
#     "eth_q_eip_event_lag1", "eth_q_eip_event_sum_7", "eth_q_eip_event_mean_7"  # 🔥 EIP
# ]

# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "eth_price_lag1", "eth_ma_7d", "eth_ma_14d", "eth_ma_21d", "eth_ma_30d"  # 🔥 修改为ETH
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

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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

# # --------- Bass 增量（标准化迁移的网络效应） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     ΔN(t) = [p(t) + q(t)·X(t-1)/m + Σγ_j·M_j^norm(t)] · (m-X(t-1)) + Σ M_j(t)
    
#     - 网络效应项使用标准化的 M_j(t)
#     - 直接迁入项使用原始的 M_j(t)
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 🔥 迁入网络效应（使用标准化的M）
#     migration_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             M_raw = migration_dict[coin]
#             M_norm = normalize(M_raw)
#             migration_network_rate += gamma_params[i] * M_norm
    
#     # 总扩散率
#     total_rate = base_rate + migration_network_rate
#     constrained_growth = total_rate * remaining
    
#     # 🔥 直接迁入（使用原始值）
#     direct_migration = np.zeros_like(N_lag)
#     for coin in COMPETITORS:
#         if coin in migration_dict:
#             direct_migration += migration_dict[coin]
    
#     return constrained_growth + direct_migration

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """计算预测值"""
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:17]  # 🔥 12个γ参数
#         m = params[17]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:18]  # 🔥 12个γ参数
#         m = params[18]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values
    
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """计算残差"""
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[17]
#     else:
#         q0 = params[4]
#         m = params[18]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """拟合Bass模型"""
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # 🔥 12个γ参数
#             init = [0.001, 0.01, 0.01, 0.01, 0.01] + [0.0001] * 12 + [m_guess]
#             bounds = ([0, -10, -10, 0, -10] + [-0.01] * 12 + [0.9*m_guess],
#                       [1, 10, 10, 1, 10] + [0.01] * 12 + [20*m_guess])
#         else:
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01] + [0.0001] * 12 + [m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10] + [-0.01] * 12 + [0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10] + [0.01] * 12 + [20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误、t值、p值
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载迁移数据 ----------
# def load_migration_data(migration_path, main_df):
#     """
#     读取ETH迁移数据并对齐到主数据框的日期
#     返回: {coin: migration_array} 字典（原始值）
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")
    
#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列")
#         return None
    
#     # 创建完整日期范围
#     date_range = pd.date_range(start=main_df[DATE_COL].min(), 
#                                end=main_df[DATE_COL].max(), 
#                                freq='D')
#     df_full = pd.DataFrame({DATE_COL: date_range})
    
#     # 合并
#     df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
#     # 🔥 列名映射（ETH版本）
#     col_mapping = {
#         "BTC": "in_from_BTC",
#         "SOLANA": "in_from_SOLANA",
#         "BNB": "in_from_BNB",
#         "OPTIMISM": "in_from_OPTIMISM",
#         "APTOS": "in_from_APTOS",
#         "SUI": "in_from_SUI",
#         "NEAR": "in_from_NEAR",
#         "ZKSYNC": "in_from_ZKSYNC",
#         "ARBITRUM": "in_from_ARBITRUM",
#         "HARMONY": "in_from_HARMONY",
#         "ETC": "in_from_ETC",
#         "ETHPOW": "in_from_ETHPOW"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁移数据列: {actual_col}")
#         else:
#             print(f"⚠️ 未找到 {coin} 对应的列: {actual_col}")
#             migration_dict[coin] = np.zeros(len(df_merged))
    
#     # 对齐到main_df
#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
#     migration_dict_aligned = {}
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             migration_dict_aligned[coin] = aligned
#         else:
#             migration_dict_aligned[coin] = np.zeros(len(main_df))
    
#     # 打印统计
#     print("\n📈 迁移数据统计（窗口期内）:")
#     print("🔥 方法：网络效应项使用标准化M，直接迁入项使用原始M")
#     for coin in COMPETITORS:
#         M_raw = migration_dict_aligned[coin]
#         total = np.sum(M_raw)
#         non_zero_days = np.sum(M_raw > 0)
#         if non_zero_days > 0:
#             max_daily = np.max(M_raw)
#             mean_daily = np.mean(M_raw)
#             std_daily = np.std(M_raw)
#             print(f"  {coin:10s}: 总数={total:6.0f}, 非零天数={non_zero_days:4d}, "
#                   f"均值={mean_daily:5.2f}, 标准差={std_daily:5.2f}, 最大={max_daily:5.0f}")
#         else:
#             print(f"  {coin:10s}: 总数=     0, 非零天数=   0 (无数据)")
    
#     return migration_dict_aligned

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主数据
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
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
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
#                 combos_skipped += 1
#                 continue
            
#             # 选择日期窗口
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # N_lag
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 加载迁移数据
#             migration_dict = load_migration_data(MIGRATION_PATH, df)
#             if migration_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
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
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # 计算RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 🔥 参数名称（12个γ）
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q"] + \
#                                     [f"gamma_std_{coin}" for coin in COMPETITORS] + ["m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q"] + \
#                                     [f"gamma_std_{coin}" for coin in COMPETITORS] + ["m"]
                            
#                             # 保存结果
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
    
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()

    
# ========
# 独立项+网络效应扩散速度 但网络效应中用的是Mj(t-1)且标准化，独立项还是用Mj(t)不标准化
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
# OUTPUT_CSV = "btc_bass_pqfit_results_competition_dependent+speed_lag1_standardized.csv"  # 修改文件名以区分

# # 竞争币种列表
# COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# # ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
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

# # --------- q(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
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
#     """
#     params layout depends on p_model
#     """
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

# # --------- Bass 增量（形式3：标准化迁移） ----------
# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, migration_dict, gamma_params):
#     """
#     形式3（方法2：标准化）
    
#     ΔN(t) = [p(t) + q(t)*X(t-1)/m + Σγ_j·M_j^norm(t-1)] · (m-X(t-1)) + Σ M_j(t)
    
#     关键特性：
#     - 网络效应项使用标准化的迁移数据
#     - 直接迁入项使用原始值
#     - 所有扩散率项（p, q, γ·M^norm）在相同尺度
    
#     Args:
#         N_lag: N(t-1) 数组
#         p_t_arr: p(t) 数组（已通过标准化的price/event计算）
#         q_t_arr: q(t) 数组（已通过标准化的event计算）
#         m: 市场容量
#         migration_dict: {coin: migration_array} 字典（原始值）
#         gamma_params: [γ_BCH, γ_BSV, γ_ETH, γ_LTC, γ_Dogecoin]（标准化系数）
    
#     Returns:
#         ΔN(t) 预测值
#     """
#     remaining = np.maximum(m - N_lag, 0)
    
#     # Bass内生扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
#     # 迁入网络效应（标准化）
#     migration_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in migration_dict:
#             M_current = migration_dict[coin]
#             # 滞后1期
#             M_lag = np.concatenate([[0], M_current[:-1]])
            
#             # 🔥 关键：标准化迁移数据
#             M_lag_norm = normalize(M_lag)
            
#             # 累加网络效应
#             migration_network_rate += gamma_params[i] * M_lag_norm
    
#     # 总扩散率（受市场容量约束）
#     total_rate = base_rate + migration_network_rate
#     constrained_growth = total_rate * remaining
    
#     # 直接迁入（不受约束，使用原始值）
#     direct_migration = np.zeros_like(N_lag)
#     for coin in COMPETITORS:
#         if coin in migration_dict:
#             direct_migration += migration_dict[coin]
    
#     # 总增长
#     return constrained_growth + direct_migration

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """计算预测值"""
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:10]
#         m = params[10]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:11]
#         m = params[11]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values
    
#     dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, migration_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """计算残差"""
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[10]
#     else:
#         q0 = params[4]
#         m = params[11]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict):
#     """拟合Bass模型"""
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # 🔥 修改：γ初始值和边界（标准化后的合理范围）
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001, 0.0001, 0.0001, 0.0001,  # gamma初始值
#                     m_guess]
#             bounds = ([0, -10, -10, 0, -10, 
#                       -0.01, -0.01, -0.01, -0.01, -0.01,  # gamma下界
#                       0.9*m_guess],
#                       [1, 10, 10, 1, 10, 
#                        0.01, 0.01, 0.01, 0.01, 0.01,  # gamma上界
#                        20*m_guess])
#         else:
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
#                     0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 
#                     m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 
#                       -0.01, -0.01, -0.01, -0.01, -0.01, 
#                       0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 
#                        0.01, 0.01, 0.01, 0.01, 0.01, 
#                        20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误、t值、p值
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, migration_dict)
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

# # --------- 加载迁移数据（全局，只加载一次） ----------
# def load_migration_data_once(migration_path, start_date, end_date):
#     """
#     全局加载迁移数据（只调用一次）
    
#     Returns:
#         migration_dict: {coin: migration_array} 字典（对齐到日期范围）
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None
    
#     print(f"\n{'='*80}")
#     print(f"📊 加载迁移数据")
#     print(f"{'='*80}")
#     print(f"文件路径: {migration_path}")
#     print(f"列名: {df_mig.columns.tolist()}")
#     print(f"日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"总行数: {len(df_mig)}")
    
#     # 创建完整日期范围
#     date_range = pd.date_range(start=start_date, end=end_date, freq='D')
#     df_full = pd.DataFrame({'date': date_range})
    
#     # 合并
#     df_merged = df_full.merge(df_mig, on='date', how='left')
    
#     # 列名映射
#     col_mapping = {
#         "BCH": "in_from_BCH",
#         "BSV": "in_from_BSV",
#         "ETH": "in_from_ETH",
#         "LTC": "in_from_LTC",
#         "Dogecoin": "in_from_DOGE"
#     }
    
#     # 构建迁移字典
#     migration_dict = {}
#     print(f"\n📈 迁移数据统计（{start_date} 至 {end_date}）:")
#     print("⚠️  方法2：迁移网络效应使用标准化数据")
    
#     for coin in COMPETITORS:
#         actual_col = col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             migration_dict[coin] = df_merged[actual_col].fillna(0).values
            
#             # 统计
#             total = migration_dict[coin].sum()
#             non_zero = (migration_dict[coin] > 0).sum()
#             if non_zero > 0:
#                 max_val = migration_dict[coin].max()
#                 mean_val = migration_dict[coin][migration_dict[coin] > 0].mean()
#                 std_val = migration_dict[coin].std()
#                 print(f"  {coin:10s}: 总数={total:6.0f}, 非零天数={non_zero:4d}, "
#                       f"均值={migration_dict[coin].mean():5.2f}, 标准差={std_val:5.2f}, "
#                       f"最大={max_val:5.0f}")
#             else:
#                 print(f"  {coin:10s}: 总数=     0, 非零天数=   0 (无数据)")
#         else:
#             print(f"  ⚠️  {coin:10s}: 列 '{actual_col}' 不存在，使用零值")
#             migration_dict[coin] = np.zeros(len(df_merged))
    
#     print(f"{'='*80}\n")
    
#     return migration_dict

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主数据
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     # 🔥 关键修改：在循环外部加载迁移数据一次
#     migration_dict_global = load_migration_data_once(
#         MIGRATION_PATH, 
#         START_DATE, 
#         END_DATE
#     )
    
#     if migration_dict_global is None:
#         print("⚠️ 无法加载迁移数据，退出")
#         sys.exit(1)
    
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
            
#             # 选择日期窗口
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & 
#                     (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1
#                 continue
            
#             # N_lag
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
#             # 🔥 关键修改：对齐全局迁移数据到当前df
#             # 因为df可能有不同的日期索引（由于fillna等操作）
#             df_dates = pd.DatetimeIndex(df[DATE_COL].values)
#             global_dates = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
            
#             migration_dict_aligned = {}
#             for coin in COMPETITORS:
#                 # 创建临时DataFrame用于对齐
#                 temp_df = pd.DataFrame({
#                     'date': global_dates,
#                     'migration': migration_dict_global[coin]
#                 }).set_index('date')
                
#                 # 对齐到当前df的日期
#                 aligned = temp_df.reindex(df_dates)['migration'].fillna(0).values
#                 migration_dict_aligned[coin] = aligned
            
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
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict_aligned)
                            
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛")
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             # 计算RMSE/SSE
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, migration_dict_aligned)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 参数名称
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
#                                              "gamma_std_BCH", "gamma_std_BSV", "gamma_std_ETH", 
#                                              "gamma_std_LTC", "gamma_std_Dogecoin", "m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
#                                              "gamma_std_BCH", "gamma_std_BSV", "gamma_std_ETH", 
#                                              "gamma_std_LTC", "gamma_std_Dogecoin", "m"]
                            
#                             # 保存结果
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