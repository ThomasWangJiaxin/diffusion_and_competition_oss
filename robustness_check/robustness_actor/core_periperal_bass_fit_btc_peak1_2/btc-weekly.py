# 分开做btc peak1 core developers fit weekly/monthly/quarterly和peripheral developers fit weekly/monthly/quarterly：
# /home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_weekly_new_core_peripheral.csv
# period_start	Core Developers	Peripheral Developers	total_new_classified	cum_Core	cum_Peripheral	cum_total
# 2012-03-12	8	4	12	8	4	12
# 2012-03-19	4	18	22	12	22	34

# 联立/home/lab0/survival_diffusion_github/competition_bass/BTCdev_weekly_timeline_event_all_with_price_event_features.csv有price和event特征
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_2","btc_p_event_sum_4","btc_p_event_sum_6","btc_p_event_sum_8","btc_p_event_sum_10"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_2","btc_q_event_sum_4","btc_q_event_sum_6","btc_q_event_sum_8","btc_q_event_sum_10"
# ]
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_2p","btc_ma_4p","btc_ma_6p","btc_ma_8p","btc_ma_10p"
# ]

# migration core daily：/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_daily_migration_core_peripheral_wide.csv
# 属性：date	Core_total_inflow	Core_total_outflow	Peripheral_total_inflow	Peripheral_total_outflow	total_inflow	total_outflow	Core_inflow_BCOIN	Core_inflow_BNB	Core_inflow_BTCD	Core_inflow_Bitcoincash	Core_inflow_Bitcoingpu	Core_inflow_Bitcoinsv	Core_inflow_Dogecoin	Core_inflow_ETH	Core_inflow_LBTC	Core_inflow_Lightningnetwork	Core_inflow_Litecoin	Core_inflow_Monero	Core_inflow_Parity	Core_inflow_Rootstock	Core_inflow_Solana	Core_inflow_Stacks	Core_inflow_TRON	Core_inflow_ZCASH	Core_outflow_BCOIN	Core_outflow_BNB	Core_outflow_BOB	Core_outflow_BTCD	Core_outflow_Bitcoincash	Core_outflow_Bitcoincashnode	Core_outflow_Bitcoingpu	Core_outflow_Bitcoinsv	Core_outflow_Dogecoin	Core_outflow_ETH	Core_outflow_LBTC	Core_outflow_Lightningnetwork	Core_outflow_Litecoin	Core_outflow_Monero	Core_outflow_Parity	Core_outflow_Rootstock	Core_outflow_Solana	Core_outflow_Stacks	Core_outflow_TRON	Core_outflow_ZCASH	Peripheral_inflow_BCOIN	Peripheral_inflow_BNB	Peripheral_inflow_BOB	Peripheral_inflow_BTCD	Peripheral_inflow_Bitcoincash	Peripheral_inflow_Bitcoincashnode	Peripheral_inflow_Bitcoingpu	Peripheral_inflow_Bitcoinsv	Peripheral_inflow_Dogecoin	Peripheral_inflow_ETH	Peripheral_inflow_LBTC	Peripheral_inflow_Lightningnetwork	Peripheral_inflow_Litecoin	Peripheral_inflow_Monero	Peripheral_inflow_Parity	Peripheral_inflow_Rootstock	Peripheral_inflow_Solana	Peripheral_inflow_Stacks	Peripheral_inflow_TRON	Peripheral_inflow_ZCASH	Peripheral_outflow_BCOIN	Peripheral_outflow_BNB	Peripheral_outflow_BOB	Peripheral_outflow_BTCD	Peripheral_outflow_Bitcoincash	Peripheral_outflow_Bitcoincashnode	Peripheral_outflow_Bitcoingpu	Peripheral_outflow_Bitcoinsv	Peripheral_outflow_Dogecoin	Peripheral_outflow_ETH	Peripheral_outflow_LBTC	Peripheral_outflow_Lightningnetwork	Peripheral_outflow_Litecoin	Peripheral_outflow_Monero	Peripheral_outflow_Parity	Peripheral_outflow_Rootstock	Peripheral_outflow_Solana	Peripheral_outflow_Stacks	Peripheral_outflow_TRON	Peripheral_outflow_ZCASH
# 还要转成migration core weekly

# 下面是我们weekly的大概模型 没有分core和边缘的代码：
# """
# BTC 稳健性检验 —— 周/月/季度 频率版本
# 使用方法: 修改下方 ===== 频率配置 ===== 区块中的变量即可切换频率

# """
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import matplotlib as mpl

# mpl.rcParams['font.family']     = 'serif'
# mpl.rcParams['font.serif']      = ['Times New Roman']
# mpl.rcParams['axes.titlesize']  = 14
# mpl.rcParams['axes.labelsize']  = 13
# mpl.rcParams['xtick.labelsize'] = 12
# mpl.rcParams['ytick.labelsize'] = 12
# mpl.rcParams['legend.fontsize'] = 12

# # ===================================================================
# # ===== 频率配置：修改这里切换 weekly / monthly / quarterly =====
# # ===================================================================
# FREQ = "monthly"   # 可选: "weekly" | "monthly" | "quarterly"

# # --- BTC Peak1 示例 ---
# if FREQ == "weekly":
#     CSV_PATH       = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/BTCdev_weekly_timeline_event_all_with_price_event_features.csv"
#     MIGRATION_PATH = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/btc_global_migration_enhanced_weekly_strict_rules.csv"
#     START_DATE     = "2017-01-02"   # 含 2017-01-01 的那周的周一
#     END_DATE       = "2018-12-31"   # 含 2019-01-01 前的最后一个完整周
#     DATE_FREQ      = "W-MON"        # 用于 resample / 对齐

# elif FREQ == "monthly":
#     CSV_PATH       = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/BTCdev_monthly_timeline_event_all_with_price_event_features.csv"
#     MIGRATION_PATH = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/btc_global_migration_enhanced_monthly_strict_rules.csv"
#     START_DATE     = "2017-01-01"
#     END_DATE       = "2019-01-01"   # 最后完整月
#     DATE_FREQ      = "MS"

# elif FREQ == "quarterly":
#     CSV_PATH       = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/BTCdev_quarterly_timeline_event_all_with_price_event_features.csv"
#     MIGRATION_PATH = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/btc_global_migration_enhanced_quarterly_strict_rules.csv"
#     START_DATE     = "2017-01-01"
#     END_DATE       = "2019-01-01"   # 最后完整季度
#     DATE_FREQ      = "QS"

# OUTPUT_PNG = f"/home/lab0/survival_diffusion_github/robustness_check/robustness_window/btc_peak1_{FREQ}_best_fit_plot.png"
# OUTPUT_CSV = f"/home/lab0/survival_diffusion_github/robustness_check/robustness_window/btc_peak1_{FREQ}_grid_search_results.csv"
# # ===================================================================

# DATE_COL = "date"
# NEW_COL  = "btc_new_developers"
# CUM_COL  = "btc_cum_users"

# # ── 注意：week/month/quarter 的事件列名需与对应 CSV 一致 ──────────────
# # 如果 CSV 里列名仍是 btc_p_event_lag1 等，直接使用；
# # 如果已聚合为 btc_p_event_sum_1w 等，请相应修改。
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_2","btc_p_event_sum_4","btc_p_event_sum_6","btc_p_event_sum_8","btc_p_event_sum_10"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_2","btc_q_event_sum_4","btc_q_event_sum_6","btc_q_event_sum_8","btc_q_event_sum_10"
# ]
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_2p","btc_ma_4p","btc_ma_6p","btc_ma_8p","btc_ma_10p"
# ]

# TARGET_PRICE_TF = "log"
# TARGET_P_MODEL  = "additive"
# TARGET_Q_FORM   = "linear"

# COMPETITORS = [
#     "ETH","Dogecoin","Lightning Network","Monero","Litecoin",
#     "BTCD","Zcash","BCOIN","TRON","Stacks",
#     "BitcoinCash","LBTC","BitcoinGpu","Parity","Rootstock"
# ]

# # ----------------- 评估指标 -----------------
# def compute_metrics(y_true, y_pred, k):
#     y_true = np.array(y_true, dtype=float)
#     y_pred = np.array(y_pred, dtype=float)
#     n      = len(y_true)
#     resid  = y_true - y_pred
#     sse    = np.sum(resid ** 2)
#     mse    = sse / n
#     rmse   = math.sqrt(mse)
#     mad    = np.mean(np.abs(resid))
#     ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
#     r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
#     adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
#               if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
#     mask  = y_true != 0
#     mape  = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
#     denom = np.sum(np.abs(y_true))
#     wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
#     return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
#             "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x   = np.array(x, dtype=float)
#     std = np.std(x)
#     if std <= 0:
#         return x - np.mean(x)
#     return (x - np.mean(x)) / (std + 1e-12)

# def compute_q_t_from_array(event_arr, q_params, q_form):
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         return np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         return q0 * np.exp(beta * ev)
#     raise ValueError(f"未知 q_form: {q_form}")

# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
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
#         raise ValueError(f"未知 p_model: {p_model}")
#     return np.maximum(p_t, 0)

# def get_param_indices(p_model):
#     n_comp        = len(COMPETITORS)
#     p_param_count = 3 if p_model in ["additive", "nonlinear_event"] else 4
#     q_start       = p_param_count
#     gamma_start   = q_start + 2
#     delta_start   = gamma_start + n_comp
#     m_idx         = delta_start + n_comp
#     return p_param_count, q_start, gamma_start, delta_start, m_idx, m_idx + 1

# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m,
#                       inflow_dict, outflow_dict,
#                       gamma_in_params, delta_out_params):
#     remaining = np.maximum(m - N_lag, 0)
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)
#     inflow_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in inflow_dict:
#             M_in_lag = np.concatenate([[0], inflow_dict[coin][:-1]])
#             inflow_network_rate += gamma_in_params[i] * normalize(M_in_lag)
#     outflow_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in outflow_dict:
#             M_out_lag = np.concatenate([[0], outflow_dict[coin][:-1]])
#             outflow_network_rate += delta_out_params[i] * normalize(M_out_lag)
#     constrained_growth = np.maximum(
#         (base_rate + inflow_network_rate - outflow_network_rate) * remaining, 0)
#     direct_migration = np.zeros_like(N_lag)
#     for coin in COMPETITORS:
#         if coin in inflow_dict:
#             direct_migration += inflow_dict[coin]
#     return constrained_growth + direct_migration

# def compute_prediction_pair(df, params, price_array,
#                              p_event_col, q_event_col,
#                              p_model, q_form,
#                              inflow_dict, outflow_dict):
#     p_param_count, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
#     p_params         = params[:p_param_count]
#     q0, beta_q       = params[q_start], params[q_start + 1]
#     gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
#     delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
#     m                = params[m_idx]
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     dN  = dN_pred_from_Nlag(df["N_lag"].values, p_t, q_t, m,
#                              inflow_dict, outflow_dict,
#                              gamma_in_params, delta_out_params)
#     return dN, p_t, q_t

# def residuals_pair(params, df, price_array,
#                    p_event_col, q_event_col,
#                    p_model, q_form,
#                    inflow_dict, outflow_dict):
#     _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
#     if params[m_idx] <= df[CUM_COL].max() or params[q_start] < 0:
#         return np.ones(len(df)) * 1e6
#     dN_pred, _, _ = compute_prediction_pair(
#         df, params, price_array, p_event_col, q_event_col,
#         p_model, q_form, inflow_dict, outflow_dict)
#     if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0) or np.any(dN_pred < 0):
#         return np.ones(len(df)) * 1e6
#     return df[NEW_COL].values - dN_pred

# def fit_bass_pair(df, price_array,
#                   p_event_col, q_event_col,
#                   p_model, q_form,
#                   inflow_dict, outflow_dict):
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
#         n_comp  = len(COMPETITORS)
#         if p_model in ["additive", "nonlinear_event"]:
#             p_init = [0.001, 0.01, 0.01]; p_lo = [0,-10,-10]; p_hi = [1,10,10]
#         else:
#             p_init = [0.001,0.01,0.01,0.01]; p_lo=[0,-10,-10,-10]; p_hi=[1,10,10,10]
#         q_init     = [0.01, 0.01];      q_lo = [0,-10];          q_hi = [1,10]
#         gamma_init = [0.0001]*n_comp;   gamma_lo=[-0.01]*n_comp;  gamma_hi=[0.01]*n_comp
#         delta_init = [0.0001]*n_comp;   delta_lo=[-0.01]*n_comp;  delta_hi=[0.01]*n_comp
#         init = p_init + q_init + gamma_init + delta_init + [m_guess]
#         lo   = p_lo   + q_lo   + gamma_lo   + delta_lo   + [0.875*m_guess]
#         hi   = p_hi   + q_hi   + gamma_hi   + delta_hi   + [10*m_guess]
#         res = least_squares(residuals_pair, init, bounds=(lo, hi), method="trf",
#                             args=(df, price_array, p_event_col, q_event_col,
#                                   p_model, q_form, inflow_dict, outflow_dict))
#         if res.status <= 0:
#             return None
#         params = res.x
#         n, k   = len(df), len(params)
#         y_pred, _, _ = compute_prediction_pair(
#             df, params, price_array, p_event_col, q_event_col,
#             p_model, q_form, inflow_dict, outflow_dict)
#         eps = 1e-6
#         J   = []
#         for i in range(k):
#             p_eps = params.copy(); p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(
#                 df, p_eps, price_array, p_event_col, q_event_col,
#                 p_model, q_form, inflow_dict, outflow_dict)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T
#         try:    cond = np.linalg.cond(J.T @ J)
#         except: cond = np.nan
#         sigma2 = np.sum((df[NEW_COL].values - y_pred)**2) / max(n - k, 1)
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se  = np.sqrt(np.diag(cov))
#         except:
#             se = np.full(k, np.nan)
#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=max(n - k, 1)))
#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#         return res
#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # --------- 加载迁移数据（适配各频率）----------
# def load_migration_data(migration_path, main_df):
#     """
#     迁移数据已按对应频率聚合，date 列为各周期起始日。
#     用 merge 对齐 main_df 的日期，缺失填 0。
#     """
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}"); return None, None

#     # 直接用 main_df 的日期做左连接，无需重建 date_range
#     main_dates_df = pd.DataFrame({'date': pd.to_datetime(main_df[DATE_COL].values)})
#     df_merged = main_dates_df.merge(df_mig, on='date', how='left').fillna(0)

#     inflow_col_mapping = {
#         "BCOIN": "in_from_BCOIN",
#         "BTCD": "in_from_BTCD",
#         "BitcoinCash": "in_from_BitcoinCash",
#         "BitcoinGpu": "in_from_BitcoinGpu",
#         "Dogecoin": "in_from_Dogecoin",
#         "ETH": "in_from_ETH",
#         "LBTC": "in_from_LBTC",
#         "Lightning Network": "in_from_Lightning Network",
#         "Litecoin": "in_from_Litecoin",
#         "Monero": "in_from_Monero",
#         "Parity": "in_from_Parity",
#         "Rootstock": "in_from_Rootstock",
#         "Stacks": "in_from_Stacks",
#         "TRON": "in_from_TRON",
#         "Zcash": "in_from_Zcash"
#     }
#     outflow_col_mapping = {
#         "BCOIN": "out_to_BCOIN",
#         "BTCD": "out_to_BTCD",
#         "BitcoinCash": "out_to_BitcoinCash",
#         "BitcoinGpu": "out_to_BitcoinGpu",
#         "Dogecoin": "out_to_Dogecoin",
#         "ETH": "out_to_ETH",
#         "LBTC": "out_to_LBTC",
#         "Lightning Network": "out_to_Lightning Network",
#         "Litecoin": "out_to_Litecoin",
#         "Monero": "out_to_Monero",
#         "Parity": "out_to_Parity",
#         "Rootstock": "out_to_Rootstock",
#         "Stacks": "out_to_Stacks",
#         "TRON": "out_to_TRON",
#         "Zcash": "out_to_Zcash"
#     }

#     inflow_dict, outflow_dict = {}, {}
#     for coin in COMPETITORS:
#         col = inflow_col_mapping.get(coin)
#         inflow_dict[coin] = (
#             df_merged[col].values if col and col in df_merged.columns
#             else np.zeros(len(main_df)))
#         col = outflow_col_mapping.get(coin)
#         outflow_dict[coin] = (
#             df_merged[col].values if col and col in df_merged.columns
#             else np.zeros(len(main_df)))

#     loaded = sum(1 for c in COMPETITORS if inflow_col_mapping.get(c) in df_merged.columns)
#     print(f"✅ 迁移数据加载完成，{loaded}/{len(COMPETITORS)} 个竞争者有数据")
#     return inflow_dict, outflow_dict

# # --------- 绘图函数 ----------
# def plot_fit(dates, y_true, y_pred, metrics, combo_tag, save_path):
#     fig, ax = plt.subplots(figsize=(8, 4))
#     ax.plot(dates, y_true, color='#2166ac', linewidth=2.0, label='Actual new developers')
#     ax.plot(dates, y_pred, color='#d6604d', linewidth=2.0, linestyle='--', label='Fitted new developers')
#     ax.set_xlabel('Date', fontsize=13)
#     ax.set_ylabel(f'New Developers ({FREQ.capitalize()})', fontsize=13)
#     textstr = (f"Adj. $R^2$ = {metrics['Adj_R2']:.3f}\n"
#                f"RMSE = {metrics['RMSE']:.2f}\n"
#                f"WAPE = {metrics['WAPE']:.2f}%")
#     ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=12,
#             verticalalignment='top', fontfamily='serif',
#             bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray'))
#     ax.set_title(f"Best Model ({FREQ}): {combo_tag}", fontsize=10)
#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
#     # 根据频率调整 x 轴刻度间隔
#     interval = {"weekly": 3, "monthly": 3, "quarterly": 1}.get(FREQ, 3)
#     ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
#     plt.xticks(rotation=30, ha='right', fontsize=12)
#     plt.yticks(fontsize=12)
#     ax.legend(fontsize=12)
#     ax.grid(axis='y', linestyle=':', alpha=0.5)
#     plt.tight_layout()
#     plt.savefig(save_path, dpi=200, bbox_inches='tight')
#     print(f"✅ 图已保存: {save_path}")
#     plt.close()

# # =================== 主程序 ===================
# def main():
#     print(f"\n🔧 频率模式: {FREQ.upper()}")
#     print(f"   窗口: {START_DATE} ~ {END_DATE}")

#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}"); sys.exit(1)

#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

#     all_event_cols = list(set(P_EVENT_LIST + Q_EVENT_LIST + PRICE_LAG_COLS))
#     required = [DATE_COL, NEW_COL, CUM_COL] + all_event_cols
#     missing  = [c for c in required if c not in df_raw.columns]
#     if missing:
#         print(f"❌ 缺少列: {missing}"); sys.exit(1)

#     df_base = df_raw[[DATE_COL, NEW_COL, CUM_COL] + all_event_cols].copy()
#     df_base = df_base.ffill().fillna(0)
#     df_base = df_base[(df_base[DATE_COL] >= pd.to_datetime(START_DATE)) &
#                       (df_base[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
#     if df_base.empty:
#         print("❌ 过滤后数据为空，请检查 START_DATE/END_DATE 与 CSV 日期格式是否匹配")
#         sys.exit(1)

#     print(f"✅ 数据窗口: {df_base[DATE_COL].min().date()} ~ {df_base[DATE_COL].max().date()}, {len(df_base)} 个周期")

#     # 窗口内累积归零
#     cum_offset       = df_base[CUM_COL].iloc[0] - df_base[NEW_COL].iloc[0]
#     df_base[CUM_COL] = df_base[CUM_COL] - cum_offset
#     df_base["N_lag"] = df_base[CUM_COL].shift(1).fillna(0).values

#     inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df_base)
#     if inflow_dict is None:
#         print("❌ 迁移数据加载失败"); sys.exit(1)

#     param_names = ["p0", "alpha", "beta_p", "q0", "beta_q"]
#     for coin in COMPETITORS: param_names.append(f"gamma_in_{coin}")
#     for coin in COMPETITORS: param_names.append(f"delta_out_{coin}")
#     param_names.append("m")

#     total_combos = len(P_EVENT_LIST) * len(Q_EVENT_LIST) * len(PRICE_LAG_COLS)
#     print(f"\n📊 共 {total_combos} 个组合，开始遍历...\n")

#     all_results = []
#     done, skip  = 0, 0

#     for p_col in P_EVENT_LIST:
#         for q_col in Q_EVENT_LIST:
#             for price_col in PRICE_LAG_COLS:
#                 combo_tag = f"P={p_col} | Q={q_col} | price={price_col}({TARGET_PRICE_TF})"
#                 print(f"→ [{done+skip+1}/{total_combos}] {combo_tag}")

#                 raw_price = df_base[price_col].values.astype(float)
#                 if TARGET_PRICE_TF == "log":
#                     price_arr = normalize(np.log(np.maximum(raw_price, 1e-8)))
#                 else:
#                     price_arr = normalize(raw_price)

#                 res = fit_bass_pair(df_base, price_arr, p_col, q_col,
#                                     TARGET_P_MODEL, TARGET_Q_FORM,
#                                     inflow_dict, outflow_dict)
#                 if res is None:
#                     print("  ✖ 拟合失败，跳过")
#                     skip += 1
#                     continue

#                 params = res.x
#                 k      = len(params)
#                 y_pred, _, _ = compute_prediction_pair(
#                     df_base, params, price_arr, p_col, q_col,
#                     TARGET_P_MODEL, TARGET_Q_FORM, inflow_dict, outflow_dict)
#                 metrics = compute_metrics(df_base[NEW_COL].values, y_pred, k)
#                 done += 1

#                 row = {
#                     "freq": FREQ,
#                     "p_event_col": p_col, "q_event_col": q_col,
#                     "price_col": price_col, "price_tf": TARGET_PRICE_TF,
#                     "p_model": TARGET_P_MODEL, "q_form": TARGET_Q_FORM,
#                     **metrics,
#                     "cond": float(res.cond) if not np.isnan(res.cond) else np.nan,
#                 }
#                 for i, name in enumerate(param_names):
#                     if i < len(params):
#                         pv  = res.pvals[i] if hasattr(res, 'pvals') else np.nan
#                         sig = ("***" if pv < 0.001 else "**" if pv < 0.01
#                                else "*" if pv < 0.05 else "†" if pv < 0.1 else "")
#                         row[name]          = float(params[i])
#                         row[f"se_{name}"]  = float(res.se[i])
#                         row[f"t_{name}"]   = float(res.tvals[i])
#                         row[f"p_{name}"]   = float(pv)
#                         row[f"sig_{name}"] = sig
#                 all_results.append(row)

#     df_results = pd.DataFrame(all_results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 结果已保存: {OUTPUT_CSV}  (成功 {done} 次，跳过 {skip} 次)")

#     if df_results.empty:
#         print("❌ 无有效结果"); sys.exit(1)

#     best_idx = df_results["RMSE"].idxmin()
#     best_row = df_results.loc[best_idx]
#     best_tag = (f"P={best_row['p_event_col']} | Q={best_row['q_event_col']} | "
#                 f"price={best_row['price_col']}({best_row['price_tf']})")

#     print("\n" + "="*80)
#     print(f"🏆 最低 RMSE 模型 [{FREQ}]: {best_tag}")
#     print("="*80)
#     print(f"  RMSE   = {best_row['RMSE']:.4f}")
#     print(f"  WAPE   = {best_row['WAPE']:.4f}%")
#     print(f"  Adj_R2 = {best_row['Adj_R2']:.4f}")
#     print(f"\n  {'参数':<28} {'估计值':>14} {'SE':>12} {'t':>10} {'p':>10} {'显著性':>6}")
#     print("  " + "-"*82)
#     for name in param_names:
#         if name in best_row:
#             print(f"  {name:<28} {best_row[name]:>14.6e} "
#                   f"{best_row.get(f'se_{name}', np.nan):>12.4e} "
#                   f"{best_row.get(f't_{name}', np.nan):>10.3f} "
#                   f"{best_row.get(f'p_{name}', np.nan):>10.4f} "
#                   f"{best_row.get(f'sig_{name}', ''):>6}")

#     # 重新拟合最优并绘图
#     raw_price_best = df_base[best_row['price_col']].values.astype(float)
#     price_arr_best = normalize(np.log(np.maximum(raw_price_best, 1e-8)))
#     res_best = fit_bass_pair(df_base, price_arr_best,
#                              best_row['p_event_col'], best_row['q_event_col'],
#                              TARGET_P_MODEL, TARGET_Q_FORM, inflow_dict, outflow_dict)
#     if res_best is not None:
#         y_pred_best, _, _ = compute_prediction_pair(
#             df_base, res_best.x, price_arr_best,
#             best_row['p_event_col'], best_row['q_event_col'],
#             TARGET_P_MODEL, TARGET_Q_FORM, inflow_dict, outflow_dict)
#         metrics_best = compute_metrics(df_base[NEW_COL].values, y_pred_best, len(res_best.x))
#         plot_fit(pd.to_datetime(df_base[DATE_COL].values),
#                  df_base[NEW_COL].values, y_pred_best,
#                  metrics_best, best_tag, OUTPUT_PNG)

# if __name__ == "__main__":
#     main()

"""
BTC 稳健性检验 —— Core / Peripheral 开发者分类版本
==================================================
对 Core 和 Peripheral 开发者分别拟合完整 Bass 竞争扩散模型。

数据来源:
  - 开发者新增序列 : btc_weekly_new_core_peripheral.csv
  - 事件/价格特征  : BTCdev_weekly_timeline_event_all_with_price_event_features.csv
  - 迁移数据 (日度): btc_daily_migration_core_peripheral_wide.csv（在脚本内聚合为周度）

使用方法:
  ACTOR = "Core"        # 切换 "Core" | "Peripheral"
  PEAK  = "peak1"       # 切换 "peak1" | "peak2"
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl

mpl.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.titlesize': 14, 'axes.labelsize': 13,
    'xtick.labelsize': 12, 'ytick.labelsize': 12,
    'legend.fontsize': 12,
})

# ===================================================================
# ===== 配置区：修改此处切换 actor 类型 / peak 窗口 =====
# ===================================================================
ACTOR = "Peripheral"        # "Core" | "Peripheral"
PEAK  = "peak2"       # "peak1" | "peak2"

# 峰值窗口定义（weekly，同主模型）
PEAK_WINDOWS = {
    "peak1": ("2017-01-02", "2018-12-31"),
    "peak2": ("2020-09-28", "2022-10-03"),
}
START_DATE, END_DATE = PEAK_WINDOWS[PEAK]

# ── 路径 ──────────────────────────────────────────────────────────
BASE = "/home/lab0/survival_diffusion_github"

ACTOR_CSV_PATH  = f"{BASE}/robustness_check/robustness_actor/btc_weekly_new_core_peripheral.csv"
FEATURE_CSV     = f"{BASE}/competition_bass/BTCdev_weekly_timeline_event_all_with_price_event_features.csv"
DAILY_MIG_PATH  = f"{BASE}/robustness_check/robustness_actor/btc_daily_migration_core_peripheral_wide.csv"

OUTPUT_CSV = (f"{BASE}/robustness_check/robustness_actor/core_periperal_bass_fit_btc_peak1_2/"
              f"btc_{PEAK}_{ACTOR.lower()}_weekly_grid_results.csv")
OUTPUT_PNG = (f"{BASE}/robustness_check/robustness_actor/core_periperal_bass_fit_btc_peak1_2/"
              f"btc_{PEAK}_{ACTOR.lower()}_weekly_best_fit.png")
# ===================================================================

DATE_COL = "date"

# 根据 actor 选择列名
if ACTOR == "Core":
    NEW_COL = "Core"
    CUM_COL = "cum_Core"
    MIG_IN_PREFIX  = "Core_inflow_"
    MIG_OUT_PREFIX = "Core_outflow_"
else:
    NEW_COL = "Peripheral"
    CUM_COL = "cum_Peripheral"
    MIG_IN_PREFIX  = "Peripheral_inflow_"
    MIG_OUT_PREFIX = "Peripheral_outflow_"

# ── 事件 / 价格列表（与主模型一致）──────────────────────────────
P_EVENT_LIST = [
    "btc_p_event_lag1", "btc_p_event_sum_2", "btc_p_event_sum_4",
    "btc_p_event_sum_6", "btc_p_event_sum_8", "btc_p_event_sum_10",
]
Q_EVENT_LIST = [
    "btc_q_event_lag1", "btc_q_event_sum_2", "btc_q_event_sum_4",
    "btc_q_event_sum_6", "btc_q_event_sum_8", "btc_q_event_sum_10",
]
PRICE_LAG_COLS = [
    "btc_price_lag1", "btc_ma_2p", "btc_ma_4p",
    "btc_ma_6p", "btc_ma_8p", "btc_ma_10p",
]

TARGET_PRICE_TF = "log"
TARGET_P_MODEL  = "additive"
TARGET_Q_FORM   = "linear"

# ── 竞争项目列表（按 peak 区分）────────────────────────────────
COMPETITORS_PEAK = {
    "peak1": [
        "ETH", "Dogecoin", "Lightning Network", "Monero", "Litecoin",
        "BTCD", "Zcash", "BCOIN", "TRON", "Stacks",
        "BitcoinCash", "LBTC", "BitcoinGpu", "Parity", "Rootstock",
    ],
    "peak2": [
        "ETH", "Dogecoin", "Lightning Network", "Solana", "Monero",
        "Litecoin", "BTCD", "Zcash", "BCOIN", "TRON",
        "Stacks", "BitcoinCash", "BNBChain", "LBTC",
    ],
}
COMPETITORS = COMPETITORS_PEAK[PEAK]   # 由顶部 PEAK 变量决定

# 每个竞争项目在日度迁移 CSV 中的列名尾缀（去掉前缀后）
# 格式：COMPETITORS 名 → 迁移CSV列名后缀
COMP_COL_MAP = {
    "ETH":              "ETH",
    "Dogecoin":         "Dogecoin",
    "Lightning Network":"Lightningnetwork",
    "Monero":           "Monero",
    "Litecoin":         "Litecoin",
    "BTCD":             "BTCD",
    "Zcash":            "ZCASH",
    "BCOIN":            "BCOIN",
    "TRON":             "TRON",
    "Stacks":           "Stacks",
    "BitcoinCash":      "Bitcoincash",
    "LBTC":             "LBTC",
    "BitcoinGpu":       "Bitcoingpu",
    "Parity":           "Parity",
    "Rootstock":        "Rootstock",
    # peak2 专属
    "Solana":           "Solana",
    "BNBChain":         "BNB",
}


# ─────────────────────────────────────────────────────────────────
# 评估指标
# ─────────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, k):
    y_true, y_pred = np.array(y_true, float), np.array(y_pred, float)
    n     = len(y_true)
    resid = y_true - y_pred
    sse   = np.sum(resid ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
              if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
    mask  = y_true != 0
    mape  = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
    denom = np.sum(np.abs(y_true))
    wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
    return {
        "MAD": np.mean(np.abs(resid)),
        "SSE": sse, "MSE": sse / n,
        "RMSE": math.sqrt(sse / n),
        "R2": r2, "Adj_R2": adj_r2,
        "MAPE": mape, "WAPE": wape,
    }


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────
def normalize(x):
    x   = np.array(x, float)
    std = np.std(x)
    return (x - np.mean(x)) / (std + 1e-12) if std > 0 else x - np.mean(x)

def compute_p_t(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    p0, alpha, beta = params[:3]
    p_t = p0 + alpha * price_array + beta * ev   # additive
    return np.maximum(p_t, 0)

def compute_q_t(event_arr, q0, beta_q, q_form):
    ev = normalize(event_arr)
    q_t = q0 + beta_q * ev  # linear
    return np.maximum(q_t, 0)

def get_param_indices():
    """参数布局: [p0, alpha, beta_p, q0, beta_q, γ_in×J, δ_out×J, m]"""
    n = len(COMPETITORS)
    return dict(p_end=3, q_start=3, q_end=5,
                gi_start=5, gi_end=5+n,
                do_start=5+n, do_end=5+2*n,
                m_idx=5+2*n, total=5+2*n+1)

def dN_prediction(df, params, price_array, p_event_col, q_event_col,
                  inflow_dict, outflow_dict):
    idx = get_param_indices()
    p0, alpha, beta_p = params[0], params[1], params[2]
    q0, beta_q        = params[idx['q_start']], params[idx['q_start']+1]
    gamma_in  = params[idx['gi_start']:idx['gi_end']]
    delta_out = params[idx['do_start']:idx['do_end']]
    m         = params[idx['m_idx']]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)

    p_t = compute_p_t(df, [p0, alpha, beta_p], price_array, TARGET_P_MODEL, p_event_col)
    q_t = compute_q_t(df[q_event_col].values, q0, beta_q, TARGET_Q_FORM)

    base_rate = p_t + q_t * (N_lag / m)

    inflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            lag = np.concatenate([[0], inflow_dict[coin][:-1]])
            inflow_rate += gamma_in[i] * normalize(lag)

    outflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            lag = np.concatenate([[0], outflow_dict[coin][:-1]])
            outflow_rate += delta_out[i] * normalize(lag)

    growth = np.maximum((base_rate + inflow_rate - outflow_rate) * remaining, 0)

    direct = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct += inflow_dict[coin]

    return growth + direct

def residuals_fn(params, df, price_array, p_event_col, q_event_col,
                 inflow_dict, outflow_dict):
    idx = get_param_indices()
    if params[idx['m_idx']] <= df[CUM_COL].max() or params[idx['q_start']] < 0:
        return np.ones(len(df)) * 1e6
    pred = dN_prediction(df, params, price_array, p_event_col, q_event_col,
                         inflow_dict, outflow_dict)
    if np.any(np.isnan(pred)) or np.allclose(pred, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - pred

def fit_model(df, price_array, p_event_col, q_event_col,
              inflow_dict, outflow_dict):
    try:
        idx     = get_param_indices()
        n_comp  = len(COMPETITORS)
        m_guess = 1.2 * df[CUM_COL].max()

        init = ([0.001, 0.01, 0.01]            # p0, alpha, beta_p
                + [0.01, 0.01]                  # q0, beta_q
                + [0.0001] * n_comp             # gamma_in
                + [0.0001] * n_comp             # delta_out
                + [m_guess])
        lo   = ([0,   -10, -10] + [0,   -10]
                + [-0.01]*n_comp + [-0.01]*n_comp + [0.875*m_guess])
        hi   = ([1,    10,  10] + [1,    10]
                + [0.01]*n_comp  + [0.01]*n_comp  + [10*m_guess])

        res = least_squares(residuals_fn, init, bounds=(lo, hi), method="trf",
                            args=(df, price_array, p_event_col, q_event_col,
                                  inflow_dict, outflow_dict))
        if res.status < 0:
            return None

        params = res.x
        n, k   = len(df), len(params)
        y_pred = dN_prediction(df, params, price_array, p_event_col, q_event_col,
                               inflow_dict, outflow_dict)

        # 数值 Jacobian → 标准误
        eps, J = 1e-6, []
        for i in range(k):
            p_eps      = params.copy(); p_eps[i] += eps
            y_eps      = dN_prediction(df, p_eps, price_array, p_event_col, q_event_col,
                                       inflow_dict, outflow_dict)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T
        try:    cond = np.linalg.cond(J.T @ J)
        except: cond = np.nan

        sigma2 = np.sum((df[NEW_COL].values - y_pred)**2) / max(n - k, 1)
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se  = np.sqrt(np.diag(cov))
        except:
            se = np.full(k, np.nan)

        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=max(n - k, 1)))
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# 日度迁移 → 周度聚合（分 Core / Peripheral）
# ─────────────────────────────────────────────────────────────────
def build_weekly_migration(daily_mig_path, main_df):
    """
    读取日度迁移宽表，按 ISO 周（Week-Monday）加总，
    再对齐 main_df 的日期序列，返回 (inflow_dict, outflow_dict)。
    """
    try:
        df_d = pd.read_csv(daily_mig_path, parse_dates=['date'])
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None, None

    # 聚合到周（week starting Monday）
    df_d = df_d.set_index('date').sort_index()
    df_w = df_d.resample('W-MON', label='left', closed='left').sum().reset_index()
    df_w = df_w.rename(columns={'date': DATE_COL})

    # 对齐 main_df 日期
    main_dates = pd.DataFrame({DATE_COL: pd.to_datetime(main_df[DATE_COL].values)})
    df_merged  = main_dates.merge(df_w, on=DATE_COL, how='left').fillna(0)

    inflow_dict, outflow_dict = {}, {}
    n = len(main_df)

    for coin in COMPETITORS:
        suffix   = COMP_COL_MAP.get(coin, coin)
        in_col   = MIG_IN_PREFIX  + suffix
        out_col  = MIG_OUT_PREFIX + suffix

        inflow_dict[coin]  = (df_merged[in_col].values
                              if in_col  in df_merged.columns else np.zeros(n))
        outflow_dict[coin] = (df_merged[out_col].values
                              if out_col in df_merged.columns else np.zeros(n))

        in_ok  = in_col  in df_merged.columns
        out_ok = out_col in df_merged.columns
        status = "✅" if (in_ok and out_ok) else ("⚠️ in only" if in_ok else
                                                   "⚠️ out only" if out_ok else "❌")
        print(f"  {status}  {coin:20s}  in={in_col}  out={out_col}")

    return inflow_dict, outflow_dict


# ─────────────────────────────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────────────────────────────
def plot_fit(dates, y_true, y_pred, metrics, combo_tag, save_path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, y_true, color='#2166ac', lw=2.0, label=f'Actual ({ACTOR})')
    ax.plot(dates, y_pred, color='#d6604d', lw=2.0, ls='--', label='Fitted')
    textstr = (f"Adj. $R^2$ = {metrics['Adj_R2']:.3f}\n"
               f"RMSE = {metrics['RMSE']:.2f}\n"
               f"WAPE = {metrics['WAPE']:.2f}%")
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=12,
            va='top', fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.8, ec='gray'))
    ax.set_title(f"BTC {PEAK} – {ACTOR} Developers | {combo_tag}", fontsize=10)
    ax.set_xlabel('Date'); ax.set_ylabel(f'New {ACTOR} Developers (Weekly)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30, ha='right')
    ax.legend(); ax.grid(axis='y', ls=':', alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"✅ 图已保存: {save_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────
def main():
    print(f"\n🔧 Actor={ACTOR}  Peak={PEAK}  窗口={START_DATE}~{END_DATE}")

    # ── 1. 加载 Core/Peripheral 开发者序列 ────────────────────────
    try:
        df_actor = pd.read_csv(ACTOR_CSV_PATH)
        df_actor.columns = df_actor.columns.str.strip()
        print(f"   actor CSV 列名: {list(df_actor.columns)}")
        # 自动识别日期列（兼容 'date'/'period_start'/'week' 等命名）
        date_candidates = [c for c in df_actor.columns
                        if any(k in c.lower() for k in ('date', 'period', 'week', 'time'))]
        if DATE_COL in df_actor.columns:
            pass
        elif date_candidates:
            df_actor = df_actor.rename(columns={date_candidates[0]: DATE_COL})
            print(f"   日期列 '{date_candidates[0]}' → 重命名为 '{DATE_COL}'")
        else:
            print(f"❌ 找不到日期列，所有列: {list(df_actor.columns)}"); sys.exit(1)
        df_actor[DATE_COL] = pd.to_datetime(df_actor[DATE_COL], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"❌ 无法读取 actor CSV: {e}"); sys.exit(1)

    # ── 2. 加载事件/价格特征 ───────────────────────────────────────
    all_feat_cols = list(set(P_EVENT_LIST + Q_EVENT_LIST + PRICE_LAG_COLS))
    try:
        df_feat = pd.read_csv(FEATURE_CSV)
        df_feat.columns = df_feat.columns.str.strip()
        # 兼容 "2012-03-19 - 2012-03-25" 格式：取 ' - ' 前的部分
        if DATE_COL not in df_feat.columns:
            date_candidates = [c for c in df_feat.columns
                            if any(k in c.lower() for k in ('date', 'period', 'week', 'time'))]
            if date_candidates:
                df_feat = df_feat.rename(columns={date_candidates[0]: DATE_COL})
        df_feat[DATE_COL] = (df_feat[DATE_COL]
                            .astype(str)
                            .str.split(' - ')
                            .str[0]
                            .str.strip())
        df_feat[DATE_COL] = pd.to_datetime(df_feat[DATE_COL], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"❌ 无法读取特征 CSV: {e}"); sys.exit(1)

    missing_feat = [c for c in all_feat_cols if c not in df_feat.columns]
    if missing_feat:
        print(f"⚠️ 特征 CSV 缺少列: {missing_feat}")

    # ── 3. 合并 ────────────────────────────────────────────────────
    df = df_actor[[DATE_COL, NEW_COL, CUM_COL]].merge(
        df_feat[[DATE_COL] + [c for c in all_feat_cols if c in df_feat.columns]],
        on=DATE_COL, how='left')
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = df.ffill().fillna(0)

    # ── 4. 窗口过滤 ────────────────────────────────────────────────
    df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
            (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy().reset_index(drop=True)
    if df.empty:
        print("❌ 窗口内无数据"); sys.exit(1)
    print(f"✅ 数据: {df[DATE_COL].min().date()} ~ {df[DATE_COL].max().date()}, {len(df)} 周")

    # ── 5. 累积量归零（窗口内重新 cumsum）──────────────────────────
    df[CUM_COL] = df[NEW_COL].cumsum()
    df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

    # ── 6. 迁移数据（日度→周度）──────────────────────────────────
    print("\n📦 加载并聚合迁移数据...")
    inflow_dict, outflow_dict = build_weekly_migration(DAILY_MIG_PATH, df)
    if inflow_dict is None:
        print("❌ 迁移数据加载失败"); sys.exit(1)

    # ── 7. 参数名列表 ──────────────────────────────────────────────
    param_names = (["p0", "alpha", "beta_p", "q0", "beta_q"]
                   + [f"gamma_in_{c}"  for c in COMPETITORS]
                   + [f"delta_out_{c}" for c in COMPETITORS]
                   + ["m"])

    # ── 8. 网格搜索 ────────────────────────────────────────────────
    combos = [(p, q, pr)
              for p in P_EVENT_LIST
              for q in Q_EVENT_LIST
              for pr in PRICE_LAG_COLS]
    print(f"\n📊 共 {len(combos)} 个组合，开始拟合...\n")

    all_results, done, skip = [], 0, 0

    for p_col, q_col, price_col in combos:
        tag = f"P={p_col}|Q={q_col}|pr={price_col}"
        print(f"→ [{done+skip+1}/{len(combos)}] {tag}")

        raw = df[price_col].values.astype(float)
        price_arr = normalize(np.log(np.maximum(raw, 1e-8)))

        res = fit_model(df, price_arr, p_col, q_col, inflow_dict, outflow_dict)
        if res is None:
            print("  ✖ 拟合失败"); skip += 1; continue

        params = res.x
        y_pred = dN_prediction(df, params, price_arr, p_col, q_col,
                               inflow_dict, outflow_dict)
        metrics = compute_metrics(df[NEW_COL].values, y_pred, len(params))
        done += 1

        row = {
            "actor": ACTOR, "peak": PEAK, "freq": "weekly",
            "p_event_col": p_col, "q_event_col": q_col,
            "price_col": price_col, "price_tf": TARGET_PRICE_TF,
            **metrics,
            "cond": float(res.cond) if not np.isnan(res.cond) else np.nan,
        }
        for i, name in enumerate(param_names):
            if i < len(params):
                pv  = res.pvals[i]
                sig = ("***" if pv < 0.001 else "**" if pv < 0.01
                       else "*" if pv < 0.05 else "†" if pv < 0.1 else "")
                row[name]            = float(params[i])
                row[f"se_{name}"]    = float(res.se[i])
                row[f"t_{name}"]     = float(res.tvals[i])
                row[f"p_{name}"]     = float(pv)
                row[f"sig_{name}"]   = sig
        all_results.append(row)

    df_out = pd.DataFrame(all_results)
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 结果已保存: {OUTPUT_CSV}  (成功 {done}, 跳过 {skip})")

    if df_out.empty:
        print("❌ 无有效结果"); sys.exit(1)

    # ── 9. 最优模型汇报 ────────────────────────────────────────────
    best = df_out.loc[df_out["RMSE"].idxmin()]
    best_tag = f"P={best['p_event_col']}|Q={best['q_event_col']}|pr={best['price_col']}"
    print(f"\n{'='*80}")
    print(f"🏆 最低 RMSE [{ACTOR} / {PEAK}]: {best_tag}")
    print(f"{'='*80}")
    print(f"  RMSE   = {best['RMSE']:.4f}")
    print(f"  WAPE   = {best['WAPE']:.4f}%")
    print(f"  Adj_R2 = {best['Adj_R2']:.4f}")
    header = f"  {'参数':<30} {'估计值':>14} {'SE':>12} {'t':>10} {'p':>10} {'sig':>5}"
    print(f"\n{header}")
    print("  " + "-"*83)
    for name in param_names:
        if name in best:
            print(f"  {name:<30} {best[name]:>14.4e} "
                  f"{best.get(f'se_{name}', np.nan):>12.4e} "
                  f"{best.get(f't_{name}', np.nan):>10.3f} "
                  f"{best.get(f'p_{name}', np.nan):>10.4f} "
                  f"{best.get(f'sig_{name}', ''):>5}")

    # ── 10. 最优模型绘图 ───────────────────────────────────────────
    raw_best  = df[best['price_col']].values.astype(float)
    price_best = normalize(np.log(np.maximum(raw_best, 1e-8)))
    res_best = fit_model(df, price_best,
                         best['p_event_col'], best['q_event_col'],
                         inflow_dict, outflow_dict)
    if res_best is not None:
        y_pred_best = dN_prediction(df, res_best.x, price_best,
                                    best['p_event_col'], best['q_event_col'],
                                    inflow_dict, outflow_dict)
        m_best = compute_metrics(df[NEW_COL].values, y_pred_best, len(res_best.x))
        plot_fit(pd.to_datetime(df[DATE_COL].values),
                 df[NEW_COL].values, y_pred_best,
                 m_best, best_tag, OUTPUT_PNG)


if __name__ == "__main__":
    main()