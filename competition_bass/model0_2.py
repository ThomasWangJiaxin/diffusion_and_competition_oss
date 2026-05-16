# # 用curve_fit拟合Bass模型的闭式解（新增量 dN/dt 解析解），支持 周/月/季度 数据
# 和下面代码不同gpt生成 但结果一样，只适用monthly和quarterly
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# import scipy.stats as stats
# import matplotlib.pyplot as plt

# # ============= 参数配置区（只需改这几行即可切换文件和时间范围）=============
# # 选择要处理的文件：weekly / monthly / quarterly
# TIME_GRAN = "weekly"   # 可选: "weekly", "monthly", "quarterly"

# CSV_PATH = f"/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev_{TIME_GRAN}_timeline_event_all.csv"

# # 列名保持一致（三个文件里都应该有这些列）
# DATE_COL = "date"
# NEW_COL  = "btc_new_developers"   # 新增开发者
# CUM_COL  = "btc_cum_users"        # 累计开发者

# # 拟合时间范围（根据数据实际情况调整）
# START_DATE = "2017-01-01"    # 月/季度用 "YYYY-MM" 或 "YYYY-Q1"，周用 "YYYY-MM-DD"
# END_DATE   = "2019-01-01"    # 

# # 对周的处理
# # 用周一（或周起始日）作为该周的时间戳
# # 用 >= start 和 <= end 做闭区间筛选
# # 自动把“跨边界的周”归属到它开始的那一侧

# # 输出文件（自动加上粒度标识）
# OUTPUT_PNG_NEW = f"btc_bass_new_dev_dNfit_{TIME_GRAN}.png"
# OUTPUT_PNG_CUM = f"btc_bass_cum_dev_dNfit_{TIME_GRAN}.png"
# OUTPUT_CSV     = f"btc_bass_results_dNfit_{TIME_GRAN}.csv"
# # ===========================================================================

# def load_and_parse_date(df):
#     """专为你的季度格式 '2012-Q1' 优化，简洁高效"""
#     date_str = df[DATE_COL].astype(str).str.strip()
    
#     if TIME_GRAN == "weekly":
#         # 周：2012-03-05-2012-03-11 → 取第一天
#         df[DATE_COL] = pd.to_datetime(date_str.str.split('-').str[0])
        
#     elif TIME_GRAN == "monthly":
#         # 月：2021-03 或 2021-3 → 2021-03-01
#         df[DATE_COL] = pd.to_datetime(date_str + '-01', format='%Y-%m-%d', errors='coerce')
        
#     elif TIME_GRAN == "quarterly":
#         # 季度：精确匹配你现在的 "2012-Q1" 格式
#         def qstr_to_date(q):
#             year, q_part = q.split('-Q')        # 直接拆 "2012-Q1" → "2012", "1"
#             month = {1: '01-01', 2: '04-01', 3: '07-01', 4: '10-01'}[int(q_part)]
#             return f"{year}-{month}"
        
#         df[DATE_COL] = pd.to_datetime(date_str.apply(qstr_to_date))
    
#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     return df

# def select_date(df, start, end):
#     start_dt = pd.to_datetime(start)
#     end_dt   = pd.to_datetime(end)
#     if TIME_GRAN == "quarterly":
#         # 季度结束日期要包含整个季度最后一天
#         end_dt = end_dt + pd.tseries.offsets.QuarterEnd(0)
#     mask = (df[DATE_COL] >= start_dt) & (df[DATE_COL] <= end_dt)
#     return df.loc[mask].copy()

# # --------- Bass模型定义 ----------
# def bass_model_N(t, p, q, m):
#     """累计采用量 N(t)"""
#     exp_term = np.exp(-(p + q) * t)
#     denom = 1 + (q / p) * exp_term
#     return m * (1 - exp_term) / denom

# def bass_model_dN(t, p, q, m):
#     """新增采用量 dN/dt"""
#     exp_term = np.exp(-(p + q) * t)
#     numerator = m * (p + q)**2 * exp_term / p
#     denominator = (1 + (q / p) * exp_term)**2
#     return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator != 0)

# # --------- 参数拟合 ----------
# def fit_bass(df):
#     # 以第一个观测点作为 t=0
#     t_start = df[DATE_COL].iloc[0]
#     df['t_year'] = (df[DATE_COL] - t_start).dt.days / 365.25   # 所有粒度都用这个！
#     t = df['t_year'].values
    
#     if TIME_GRAN == "weekly":
#         df['t'] = (df[DATE_COL] - t_start).dt.days / 7.0   # 每周为单位，浮点数
#     elif TIME_GRAN == "monthly":
#         df['t'] = ((df[DATE_COL].dt.year - t_start.year)*12 + 
#                    (df[DATE_COL].dt.month - t_start.month)).astype(float)
#     elif TIME_GRAN == "quarterly":
#         df['t'] = ((df[DATE_COL].dt.year - t_start.year)*4 + 
#                    ((df[DATE_COL].dt.month - 1)//3 - (t_start.month - 1)//3)).astype(float)
    
#     t = df['t'].values
#     y_dN = df[NEW_COL].values.astype(float)
#     y_cum = df[CUM_COL].values.astype(float)   # ← 这里是 ndarray
    
#     N0 = y_cum[0]  # 正确：用普通索引
    
#     max_cum = y_cum.max()
#     m_guess = max_cum * 1.2
#     bounds_lower = [1e-6, 0,      max_cum * 0.5]
#     bounds_upper = [0.99, 1.0,   max_cum * 20]
#     # =====================================
    
#     p0 = [0.01, 0.3, m_guess]
    
#     try:
#         popt, pcov = curve_fit(
#             bass_model_dN, t, y_dN,
#             p0=p0,
#             bounds=(bounds_lower, bounds_upper),
#             maxfev=10000,
#             ftol=1e-8,
#             xtol=1e-8
#         )
#         p, q, m = popt
#     except Exception as e:
#         print(f"拟合失败: {e}")
#         return None, None
    
#     dN_pred = bass_model_dN(t, *popt)
#     # 累计预测 = 真实起点 N0 + 从 t=0 开始的 Bass 累计增量
#     N_pred = N0 + np.cumsum(dN_pred) * (1 if TIME_GRAN == "weekly" else 
#                                        1 if TIME_GRAN == "monthly" else 
#                                        1)  # 这里时间单位已经是“期”，无需再乘周期长度
    
#     rmse_dN = np.sqrt(np.mean((y_dN - dN_pred) ** 2))
#     se = np.sqrt(np.diag(pcov))
#     n, k = len(df), 3
#     residuals = y_dN - dN_pred
#     sigma2 = np.sum(residuals**2) / (n - k) if n > k else np.nan
#     tvals = popt / se
#     pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), df=n - k)) if n > k else np.full(k, np.nan)
    
#     return popt, {
#         'se': se, 'tvals': tvals, 'pvals': pvals,
#         'rmse_dN': rmse_dN,
#         'N_pred': N_pred, 'dN_pred': dN_pred, 'N0': N0
#     }

# # --------- 主程序 ----------
# def main():
#     print(f"\n正在处理 {TIME_GRAN.upper()} 数据：{CSV_PATH}")
#     df = pd.read_csv(CSV_PATH)
#     df = load_and_parse_date(df)
#     df = df[[DATE_COL, NEW_COL, CUM_COL]].copy()
#     df = select_date(df, START_DATE, END_DATE)
    
#     if len(df) < 10:
#         print("⚠️ 数据点太少，跳过拟合")
#         return
    
#     print(f"拟合区间：{df[DATE_COL].iloc[0]} ~ {df[DATE_COL].iloc[-1]}  (共 {len(df)} 期)")
    
#     popt, info = fit_bass(df)
#     if popt is None:
#         return
    
#     p, q, m = popt
#     rmse = info['rmse_dN']
#     sse = np.sum((df[NEW_COL].values - info['dN_pred']) ** 2)
    
#     print(f"✅ 拟合成功！")
#     print(f"   p = {p:.6f}   q = {q:.6f}   m = {m:.1f}   RMSE_dN = {rmse:.3f}")
#     print(f"   初始累计 N0 = {info['N0']:.1f}")
    
#     df["pred_new"] = info['dN_pred']
#     df["pred_cum"] = info['N_pred']
    
#     # 保存结果
#     results = [{
#         "granularity": TIME_GRAN,
#         "model": "bass_dN_fit_with_N0",
#         "p": p, "q": q, "m": m,
#         "N0": info['N0'],
#         "SSE_dN": sse, "RMSE_dN": rmse,
#         "t_p": info['tvals'][0], "p_p": info['pvals'][0],
#         "t_q": info['tvals'][1], "p_q": info['pvals'][1],
#         "t_m": info['tvals'][2], "p_m": info['pvals'][2],
#     }]
#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")
    
#     # 参数显著性
#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(["p", "q", "m"], popt, info['se'], info['tvals'], info['pvals']):
#         print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p-value={p_i:.2e}")
    
#     # 绘图
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], 'o-', label="真实累计 N(t)", color="black")
#     plt.plot(df[DATE_COL], df["pred_cum"], '--', label="Bass拟合累计（已对齐N0）", color="red")
#     plt.title(f"BTC Developers Cumulative - Bass Fit ({TIME_GRAN})")
#     plt.legend(); plt.grid(True, alpha=0.3)
#     plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()
    
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], 'o-', label="真实新增", color="black")
#     plt.plot(df[DATE_COL], df["pred_new"], '--', label="Bass拟合新增 dN/dt", color="red")
#     plt.title(f"BTC New Developers per {TIME_GRAN.capitalize()} - Bass Fit")
#     plt.legend(); plt.grid(True, alpha=0.3)
#     plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()


# ===================
# 和上面代码不同gpt生成 但结果一样，同样只适用monthly和quarterly
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# import scipy.stats as stats
# import matplotlib.pyplot as plt

# # ================= 参数配置 =================
# TIME_GRAN = "quarterly"   # 可选: "monthly", "quarterly"
# CSV_PATH = f"/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_{TIME_GRAN}_timeline_event_all.csv"

# DATE_COL = "date"
# NEW_COL  = "eth_new_developers"
# CUM_COL  = "eth_cum_users"

# START_DATE = "2017-01-01"
# END_DATE   = "2019-01-01"

# OUTPUT_PNG_NEW = f"eth_bass_new_dev_dNfit_{TIME_GRAN}.png"
# OUTPUT_PNG_CUM = f"eth_bass_cum_dev_dNfit_{TIME_GRAN}.png"
# OUTPUT_CSV     = f"eth_bass_results_dNfit_{TIME_GRAN}.csv"
# # ===========================================

# # --------- 数据读取与时间处理 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH)
#     df = df[[DATE_COL, NEW_COL, CUM_COL]].copy()
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def parse_dates(df):
#     # 将不同粒度的时间转换为 datetime，并排序
#     if TIME_GRAN == "daily":
#         df[DATE_COL] = pd.to_datetime(df[DATE_COL])
#     elif TIME_GRAN == "weekly":
#         # 取每周第一天作为日期
#         df[DATE_COL] = pd.to_datetime(df[DATE_COL].str.split('-').str[0])
#     elif TIME_GRAN == "monthly":
#         df[DATE_COL] = pd.to_datetime(df[DATE_COL].astype(str) + "-01", format='%Y-%m-%d', errors='coerce')
#     elif TIME_GRAN == "quarterly":
#         def qstr_to_date(q):
#             year, qn = q.split('-Q')
#             month = {'1':'01','2':'04','3':'07','4':'10'}[qn]
#             return f"{year}-{month}-01"
#         df[DATE_COL] = pd.to_datetime(df[DATE_COL].apply(qstr_to_date))
#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# def make_continuous_t(df):
#     # 将不同粒度的日期转换为连续时间 t
#     start_date = df[DATE_COL].iloc[0]
#     if TIME_GRAN == "daily":
#         df['t'] = (df[DATE_COL] - start_date).dt.days.astype(float)
#     elif TIME_GRAN == "weekly":
#         df['t'] = (df[DATE_COL] - start_date).dt.days / 7.0
#     elif TIME_GRAN == "monthly":
#         df['t'] = (df[DATE_COL].dt.year - start_date.year)*12 + (df[DATE_COL].dt.month - start_date.month)
#         df['t'] = df['t'].astype(float)
#     elif TIME_GRAN == "quarterly":
#         df['t'] = (df[DATE_COL].dt.year - start_date.year)*4 + ((df[DATE_COL].dt.month-1)//3 - (start_date.month-1)//3)
#         df['t'] = df['t'].astype(float)
#     return df

# # --------- Bass 模型 ----------
# def bass_model_N(t, p, q, m):
#     if p == 0:
#         return m*(1 - np.exp(-q*t))
#     exp_term = np.exp(-(p+q)*t)
#     return m*(1 - exp_term) / (1 + (q/p)*exp_term)

# def bass_model_dN(t, p, q, m):
#     if p == 0:
#         return m*q*np.exp(-q*t)
#     exp_term = np.exp(-(p+q)*t)
#     numerator = m*(p+q)**2*exp_term / p
#     denominator = (1 + (q/p)*exp_term)**2
#     return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator!=0)

# # --------- 拟合函数 ----------
# def fit_bass(df):
#     df = make_continuous_t(df)
#     t = df['t'].values
#     y_dN = df[NEW_COL].values
#     y_cum = df[CUM_COL].values
#     N0 = y_cum[0]

#     m_guess = y_cum.max() * 1.2
#     p0 = [0.01, 0.3, m_guess]
#     bounds_lower = [1e-6, 0, y_cum.max()*0.5]
#     bounds_upper = [0.99, 1.0, y_cum.max()*20]

#     try:
#         popt, pcov = curve_fit(bass_model_dN, t, y_dN, p0=p0, bounds=(bounds_lower,bounds_upper), maxfev=10000)
#     except Exception as e:
#         print(f"拟合失败: {e}")
#         return None, None

#     dN_pred = bass_model_dN(t, *popt)
#     N_pred = N0 + bass_model_N(t, *popt)

#     se = np.sqrt(np.diag(pcov))
#     n, k = len(df), 3
#     residuals = y_dN - dN_pred
#     sigma2 = np.sum(residuals**2)/(n-k) if n>k else np.nan
#     tvals = popt / se if n>k else np.full(k, np.nan)
#     pvals = 2*(1 - stats.t.cdf(np.abs(tvals), df=n-k)) if n>k else np.full(k, np.nan)
#     rmse_dN = np.sqrt(np.mean(residuals**2))

#     return popt, {'dN_pred':dN_pred, 'N_pred':N_pred, 'N0':N0, 'se':se, 'tvals':tvals, 'pvals':pvals, 'rmse_dN':rmse_dN}

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = parse_dates(df)
#     df = select_date(df, START_DATE, END_DATE)

#     popt, info = fit_bass(df)
#     if popt is None:
#         return
#     p, q, m = popt
#     print(f"拟合成功: p={p:.6f}, q={q:.6f}, m={m:.1f}, RMSE_dN={info['rmse_dN']:.3f}")
#     print(f"N0 = {info['N0']:.1f}")

#     df['pred_new'] = info['dN_pred']
#     df['pred_cum'] = info['N_pred']

#     # 保存 CSV
#     df.to_csv(OUTPUT_CSV, index=False)
#     print(f"结果保存到 {OUTPUT_CSV}")

#     # 绘图
#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[CUM_COL], 'o-', label='真实累计 N(t)')
#     plt.plot(df[DATE_COL], df['pred_cum'], '--', label='拟合累计 N(t)')
#     plt.legend(); plt.grid(True,alpha=0.3); plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM,dpi=300)
#     plt.show()

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], 'o-', label='真实新增 dN')
#     plt.plot(df[DATE_COL], df['pred_new'], '--', label='拟合新增 dN/dt')
#     plt.legend(); plt.grid(True,alpha=0.3); plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW,dpi=300)
#     plt.show()

# if __name__ == "__main__":
#     main()


# ===============
# 下面代码只适用weekly

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# import scipy.stats as stats
# import matplotlib.pyplot as plt

# # ================= 参数配置 =================
# TIME_GRAN = "weekly"   # <<<<<<<<<<<<<<<< 固定为 weekly
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev_weekly_timeline_event_all.csv"

# DATE_COL = "date"
# NEW_COL  = "btc_new_developers"
# CUM_COL  = "btc_cum_users"

# START_DATE = "2017-01-01"
# END_DATE   = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_new_dev_dNfit_weekly.png"
# OUTPUT_PNG_CUM = "btc_bass_cum_dev_dNfit_weekly.png"
# OUTPUT_CSV     = "btc_bass_results_dNfit_weekly.csv"
# # ===========================================


# # --------- 数据读取与时间处理 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH)
#     df = df[[DATE_COL, NEW_COL, CUM_COL]].copy()
#     df = df.fillna(method="ffill").fillna(0)
#     return df


# def parse_dates(df):
#     """
#     Weekly 专用解析：
#     输入格式类似：
#     "2012-03-05 - 2012-03-11（第1周）"
#     只取前面的开始日期 2012-03-05
#     """
#     df[DATE_COL] = df[DATE_COL].str.split(" ").str[0]  # 取 "2012-03-05"
#     df[DATE_COL] = pd.to_datetime(df[DATE_COL])

#     # 强制对齐到周一，以保持周一致性
#     df[DATE_COL] = df[DATE_COL] - pd.to_timedelta(df[DATE_COL].dt.weekday, unit='d')

#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# def make_continuous_t(df):
#     """
#     Weekly 专用：连续周数，用整数
#     t = 0,1,2,3...
#     """
#     start_date = df[DATE_COL].iloc[0]
#     df['t'] = ((df[DATE_COL] - start_date).dt.days // 7).astype(float)
#     return df


# # --------- Bass 模型 ----------
# def bass_model_N(t, p, q, m):
#     if p == 0:
#         return m*(1 - np.exp(-q*t))
#     exp_term = np.exp(-(p+q)*t)
#     return m*(1 - exp_term) / (1 + (q/p)*exp_term)


# def bass_model_dN(t, p, q, m):
#     if p == 0:
#         return m*q*np.exp(-q*t)
#     exp_term = np.exp(-(p+q)*t)
#     numerator = m*(p+q)**2*exp_term / p
#     denominator = (1 + (q/p)*exp_term)**2
#     return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator!=0)


# # --------- 拟合函数 ----------
# def fit_bass(df):
#     df = make_continuous_t(df)
#     t = df['t'].values
#     y_dN = df[NEW_COL].values
#     y_cum = df[CUM_COL].values
#     N0 = y_cum[0]

#     m_guess = y_cum.max() * 1.2
#     p0 = [0.01, 0.3, m_guess]
#     bounds_lower = [1e-6, 0, y_cum.max()*0.5]
#     bounds_upper = [0.99, 1.0, y_cum.max()*20]

#     try:
#         popt, pcov = curve_fit(bass_model_dN, t, y_dN, p0=p0,
#                                bounds=(bounds_lower,bounds_upper), maxfev=10000)
#     except Exception as e:
#         print(f"拟合失败: {e}")
#         return None, None

#     dN_pred = bass_model_dN(t, *popt)
#     N_pred = N0 + bass_model_N(t, *popt)

#     se = np.sqrt(np.diag(pcov))
#     n, k = len(df), 3
#     residuals = y_dN - dN_pred
#     sigma2 = np.sum(residuals**2)/(n-k) if n>k else np.nan
#     tvals = popt / se if n>k else np.full(k, np.nan)
#     pvals = 2*(1 - stats.t.cdf(np.abs(tvals), df=n-k)) if n>k else np.full(k, np.nan)
#     rmse_dN = np.sqrt(np.mean(residuals**2))

#     return popt, {
#         'dN_pred': dN_pred,
#         'N_pred': N_pred,
#         'N0': N0,
#         'se': se,
#         'tvals': tvals,
#         'pvals': pvals,
#         'rmse_dN': rmse_dN
#     }


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = parse_dates(df)
#     df = select_date(df, START_DATE, END_DATE)

#     popt, info = fit_bass(df)
#     if popt is None:
#         return
#     p, q, m = popt
#     print(f"拟合成功: p={p:.6f}, q={q:.6f}, m={m:.1f}, RMSE_dN={info['rmse_dN']:.3f}")
#     print(f"N0 = {info['N0']:.1f}")

#     df['pred_new'] = info['dN_pred']
#     df['pred_cum'] = info['N_pred']

#     df.to_csv(OUTPUT_CSV, index=False)
#     print(f"结果保存到 {OUTPUT_CSV}")

#     # 绘图
#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[CUM_COL], 'o-', label='真实累计 N(t)')
#     plt.plot(df[DATE_COL], df['pred_cum'], '--', label='拟合累计 N(t)')
#     plt.legend(); plt.grid(True,alpha=0.3); plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     plt.show()

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], 'o-', label='真实新增 dN')
#     plt.plot(df[DATE_COL], df['pred_new'], '--', label='拟合新增 dN/dt')
#     plt.legend(); plt.grid(True,alpha=0.3); plt.xticks(rotation=45); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     plt.show()


# if __name__ == "__main__":
#     main()

# =======
# 简单版：索引,适用"weekly", "monthly", "quarterly"
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import scipy.stats as stats
import matplotlib.pyplot as plt

# ================= 参数配置 =================
TIME_GRAN = "weekly"   # "weekly", "monthly", "quarterly"
CSV_PATH = f"/home/lab0/survival_diffusion_github/competition_bass/ETHdev_{TIME_GRAN}_timeline_event_all.csv"

DATE_COL = "date"

# 人工选择
NEW_COL  = "eth_new_developers"
CUM_COL  = "eth_cum_users"

# 你设置 index 选择区间（例如 weekly）
# BTC weekly: 253-357; ETH weekly: 159-263
# BTC monthly: 59-83; ETH monthly:38-62
# BTC quarterly: 21-29; ETH quarterly:14-22
IDX_START = 159
IDX_END   = 263

OUTPUT_PNG_NEW = f"eth_bass_new_dev_dNfit_{TIME_GRAN}.png"
OUTPUT_PNG_CUM = f"eth_bass_cum_dev_dNfit_{TIME_GRAN}.png"
OUTPUT_CSV     = f"eth_bass_results_dNfit_{TIME_GRAN}.csv"
# ===========================================


# =============== 数据读取 =====================
def load_data():
    df = pd.read_csv(CSV_PATH)
    df = df[["index", DATE_COL, NEW_COL, CUM_COL]].copy()
    df["index"] = df["index"].astype(int)
    df = df.sort_values("index").reset_index(drop=True)
    return df


# =============== 用 index 选区间 =====================
def select_by_index(df, idx_start, idx_end):
    return df[(df["index"] >= idx_start) & (df["index"] <= idx_end)].reset_index(drop=True)


# =============== 构造 t 序列 ==========================
def make_continuous_t(df):
    df["t"] = np.arange(len(df), dtype=float)
    return df


# =============== Bass 模型 ===========================
def bass_model_N(t, p, q, m):
    if p == 0:
        return m * (1 - np.exp(-q*t))
    exp_term = np.exp(-(p+q)*t)
    return m*(1 - exp_term) / (1 + (q/p)*exp_term)

def bass_model_dN(t, p, q, m):
    if p == 0:
        return m*q*np.exp(-q*t)
    exp_term = np.exp(-(p+q)*t)
    numerator = m*(p+q)**2 * exp_term / p
    denominator = (1 + (q/p)*exp_term)**2
    return numerator / denominator


# =============== 拟合函数 ===========================
def fit_bass(df):
    df = make_continuous_t(df)

    t = df['t'].values
    y_dN = df[NEW_COL].values
    y_cum = df[CUM_COL].values
    N0 = y_cum[0]

    m_guess = y_cum.max() * 1.2
    p0 = [0.01, 0.3, m_guess]

    bounds_lower = [1e-6, 0, y_cum.max()*0.5]
    bounds_upper = [0.99, 1.0, y_cum.max()*20]

    popt, pcov = curve_fit(
        bass_model_dN, t, y_dN,
        p0=p0,
        bounds=(bounds_lower, bounds_upper),
        maxfev=20000
    )

    dN_pred = bass_model_dN(t, *popt)
    N_pred  = N0 + bass_model_N(t, *popt)

    # --- 统计量 ---
    se = np.sqrt(np.diag(pcov))
    residuals = y_dN - dN_pred
    rmse = np.sqrt(np.mean(residuals**2))

    n, k = len(df), 3
    tvals = popt / se
    pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), df=n-k))

    return popt, {
        "N_pred": N_pred,
        "dN_pred": dN_pred,
        "N0": N0,
        "se": se,
        "tvals": tvals,
        "pvals": pvals,
        "rmse_dN": rmse
    }


# ================= 主程序 ======================
def main():
    df = load_data()
    df = select_by_index(df, IDX_START, IDX_END)

    popt, info = fit_bass(df)

    p, q, m = popt
    se_p, se_q, se_m = info["se"]
    t_p, t_q, t_m = info["tvals"]
    pv_p, pv_q, pv_m = info["pvals"]

    print(f"\n===== Bass 拟合结果 =====")
    print(f"p = {p:.6f} (SE={se_p:.6f}, t={t_p:.3f}, p={pv_p:.3e})")
    print(f"q = {q:.6f} (SE={se_q:.6f}, t={t_q:.3f}, p={pv_q:.3e})")
    print(f"m = {m:.1f}    (SE={se_m:.1f},    t={t_m:.3f}, p={pv_m:.3e})")
    print(f"RMSE(dN) = {info['rmse_dN']:.4f}")
    print(f"N0       = {info['N0']:.1f}\n")

    # 保存统计结果 CSV
    stats_df = pd.DataFrame({
        "param": ["p", "q", "m"],
        "estimate": popt,
        "SE": info["se"],
        "t_value": info["tvals"],
        "p_value": info["pvals"],
        "rmse_dN": [info["rmse_dN"], "", ""]
    })

    stats_df.to_csv(OUTPUT_CSV, index=False)
    print(f"参数统计保存到: {OUTPUT_CSV}")

    # 保存预测
    df["pred_new"] = info["dN_pred"]
    df["pred_cum"] = info["N_pred"]

    # ---- 绘图 ----
    plt.figure(figsize=(12,6))
    plt.plot(df["index"], df[CUM_COL], 'o-', label="真实累计 N(t)")
    plt.plot(df["index"], df["pred_cum"], '--', label="拟合累计")
    plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()

    plt.figure(figsize=(12,6))
    plt.plot(df["index"], df[NEW_COL], 'o-', label="真实新增 dN")
    plt.plot(df["index"], df["pred_new"], '--', label="拟合 dN/dt")
    plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
