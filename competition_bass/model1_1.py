# 单独写的代码 也是离散bass model 验证了结果和下面的代码一样
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt
# import os

# # ====================================================================
# # ======================== 核心参数配置 ===============================
# # ====================================================================
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_features.csv"
# OUTPUT_DIR = "."  # 输出目录

# # ❗ 核心配置：请选择一个价格特征列作为外部驱动因子 X
# # 示例：'btc_log_price_t1', 'btc_return_7d', 'btc_vol_30d' 等
# EXOGENOUS_VAR = "eth_ma_14d" 

# # btc_price_lag1	
# # ln_btc_price_lag1
# # btc_return_1d

# # btc_return_7d	
# # btc_vol_7d	
# # btc_ma_7d	
# # btc_trend_7d	

# # btc_return_14d
# # btc_vol_14d	
# # btc_ma_14d	
# # btc_trend_14d	

# # btc_return_21	
# # btc_vol_21d	
# # btc_ma_21d	
# # btc_trend_21d	

# # btc_return_30d
# # btc_vol_30d	
# # btc_ma_30d	
# # btc_trend_30d

# # 模型和数据列定义
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_CSV = f"eth_gbm_pt_comparison_{EXOGENOUS_VAR}_2017_2019.csv"
# # ====================================================================

# # --- 辅助函数 ---

# def normalize(x):
#     """Z-Score 标准化函数 (μ=0, σ=1)"""
#     x = np.array(x)
#     return (x - np.mean(x)) / (np.std(x) + 1e-8)

# def is_scaled_variable(var_name):
#     """判断变量是否属于天然缩放变量 (return, vol)，不需要 Z-score 标准化"""
#     name = var_name.lower()
#     return 'return' in name or 'trend' in name

# def dN_bass_core(N, p_t, q, m):
#     """Bass 模型的核心增长率计算 dN/dt = (p_t + q * N/m) * (m - N)"""
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market

# # --- P(t) 函数定义 (X 是经过标准化/清洗后的预测因子) ---

# def pt_linear(params, X):
#     """p(t) = p0 + α * X"""
#     p0, alpha = params[0], params[1]
#     # np.maximum 确保 p(t) > 0，避免模型崩溃
#     return np.maximum(p0 + alpha * X, 1e-8) 

# def pt_log_linear(params, X):
#     """p(t) = p0 + α * ln(X)"""
#     p0, alpha = params[0], params[1]
#     # 假设 X 已经是 ln 变换后的价格滞后（如 btc_log_price_t1）
#     # 在这里 p(t) 的函数形式是 p(t) = p0 + α * X
#     return np.maximum(p0 + alpha * X, 1e-8) 

# def pt_exponential(params, X):
#     """p(t) = p0 + e^(α * X)"""
#     p0, alpha = params[0], params[1]
#     return np.maximum(p0 + np.exp(alpha * X), 1e-8)

# # --------- 数据准备 (整合 load_data 和 select_date 的核心逻辑) ----------
# def prepare_data():
#     """加载、筛选、清理数据，并准备外部预测因子 X"""
    
#     # 1. 加载数据
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL], low_memory=False)
#     df = df.sort_values(DATE_COL).reset_index(drop=True)

#     # 2. 筛选时间范围
#     mask = (df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))
#     df = df.loc[mask].copy()

#     # 3. 检查关键列是否存在
#     required_cols = [DATE_COL, NEW_COL, CUM_COL, EXOGENOUS_VAR]
#     for col in required_cols:
#         if col not in df.columns:
#             raise ValueError(f"CSV文件中缺少所需的列: {col}")

#     # 4. 填充并确保数值型
#     df = df.fillna(0)
#     df[CUM_COL] = pd.to_numeric(df[CUM_COL], errors='coerce').fillna(0)
#     df[NEW_COL] = pd.to_numeric(df[NEW_COL], errors='coerce').fillna(0)
#     df[EXOGENOUS_VAR] = pd.to_numeric(df[EXOGENOUS_VAR], errors='coerce').fillna(0)
    
#     # 5. 准备外部预测因子 X (标准化/非标准化)
#     is_return_or_vol = is_scaled_variable(EXOGENOUS_VAR)
    
#     if not is_return_or_vol:
#         X_pred = normalize(df[EXOGENOUS_VAR].values)
#         print(f"✅ 预测因子 '{EXOGENOUS_VAR}' 已进行 Z-Score 标准化。")
#     else:
#         X_pred = df[EXOGENOUS_VAR].values
#         print(f"✅ 预测因子 '{EXOGENOUS_VAR}' (Return/Vol) 未进行 Z-Score 标准化。")
    
#     return df, X_pred

# # --- GBM 预测和残差计算 ---

# def compute_prediction(df, params, pt_func, X_pred):
#     """
#     计算预测的新增量 dN 和时变 p_t。
#     核心修正：N 使用真实的 N(t-1) 来预测 dN(t)。
#     """
#     p0, alpha, q, m = params
    
#     # 1. 计算时变 p(t)
#     p_t = pt_func([p0, alpha], X_pred)
    
#     # 2. 获取 N(t-1)
#     # N_t_minus_1: 将 df[CUM_COL] 滞后一位 (shift(1))
#     # 并用 df[CUM_COL].iloc[0] (即 N(0)) 填充第一天的 NaN 值。
#     N_t_minus_1 = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
    
#     # 3. 计算预测 dN
#     # 使用 N(t-1) 进行计算
#     dN_predicted = dN_bass_core(N_t_minus_1, p_t, q, m)
    
#     return dN_predicted, p_t

# def residuals(params, df, pt_func, X_pred):
#     """计算残差：dN_true - dN_predicted"""
#     p0, alpha, q, m = params
    
#     # 严格的边界检查 (m 必须大于历史最大累计量，防止优化器探索无效区域)
#     if m <= df[CUM_COL].max() * 0.9 or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e9
        
#     dN_predicted, _ = compute_prediction(df, params, pt_func, X_pred)
#     dN_true = df[NEW_COL].values
    
#     return dN_true - dN_predicted

# # --------- 参数显著性检验 ----------

# def significance(df, params, pt_func, X_pred):
#     """使用数值方法计算雅可比矩阵，进而计算 SE, t, p 值"""
#     eps = 1e-8
#     k = len(params)
#     n = len(df)
    
#     # 计算基线预测值
#     y_pred_base, _ = compute_prediction(df, params, pt_func, X_pred)
    
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
        
#         y_eps, _ = compute_prediction(df, params_eps, pt_func, X_pred)
#         J.append((y_eps - y_pred_base) / eps)
        
#     J = np.array(J).T
#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred_base
    
#     try:
#         # 标准误差计算
#         sigma2 = np.sum(residuals_vec**2) / (n - k)
#         cov = sigma2 * np.linalg.inv(J.T @ J)
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)
        
#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     return se, tvals, pvals

# def print_parameter_table(model_name, params, se, tvals, pvals, param_names):
#     """打印格式化的参数估计值、SE、t值和p值"""
#     print(f"\n--- {model_name} 参数显著性 ---")
#     print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
#     print("---------------------------------------------------")
#     for name, val, s, tval, pval in zip(param_names, params, se, tvals, pvals):
#         print(f"{name:<10}{val:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}")
#     print("---------------------------------------------------\n")

# # --------- 主程序 ----------
# def main():
#     try:
#         # 1. 数据准备
#         df, X_pred = prepare_data()
        
#         # 2. 确定初始值和 N0
#         N_start = df[CUM_COL].iloc[0]
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         # 3. 模型迭代与拟合配置
#         MODEL_NAME_EXP = "Exponential(p0+e^(aX))" # 定义指数模型的名称，用于排除绘图
        
#         model_configs = {
#             "Linear(p0+aX)": (pt_linear, [1e-4, 0.01, 0.01, m_guess], ["p0", "alpha", "q", "m"]),
#             "LogLinear(p0+a_lnX)": (pt_log_linear, [1e-4, 0.01, 0.01, m_guess], ["p0", "alpha", "q", "m"]),
#             MODEL_NAME_EXP: (pt_exponential, [1e-4, 0.01, 0.01, m_guess], ["p0", "alpha", "q", "m"])
#         }
        
#         results = []
#         valid_models = [] # 记录成功拟合的模型名称
        
#         for name, (pt_func, x0, param_names) in model_configs.items():
            
#             print(f"\n=======================================================")
#             print(f"拟合模型：{name}，预测因子：{EXOGENOUS_VAR}")
#             print(f"=======================================================")
            
#             # 边界设置
#             bounds = ([1e-7, -10, 0, df[CUM_COL].max() * 0.5],
#                       [1, 10, 1, df[CUM_COL].max() * 20])
            
#             try:
#                 # 使用 least_squares 进行非线性最小二乘拟合
#                 res = least_squares(residuals, x0=x0, bounds=bounds,
#                                     args=(df, pt_func, X_pred), method="trf")
                
#                 if not res.success: 
#                     print("⚠️ Least Squares failed to converge. 跳过该模型。")
#                     continue
                
#                 params = res.x
#                 p0, alpha, q, m_relative = params
                
#                 # 计算预测值和显著性
#                 dN_pred, p_t = compute_prediction(df, params, pt_func, X_pred)
#                 cum_pred = N_start + np.cumsum(dN_pred)
#                 rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                
#                 se, tvals, pvals = significance(df, params, pt_func, X_pred)
                
#                 print_parameter_table(name, params, se, tvals, pvals, param_names)

#                 # 📌 打印 RMSE
#                 print(f"✅ 模型拟合 RMSE (新增量残差): {rmse:.4f}")
#                 print(f"   拟合评估 (p0={p0:.6f}, q={q:.6f}, m={m_relative:.1f})")
                
#                 results.append({
#                     "model": name, "Exog_Var": EXOGENOUS_VAR,
#                     "p0": p0, "alpha": alpha, "q": q, "m": m_relative,
#                     "RMSE": rmse,
#                     "t_p0": tvals[0], "p_p0": pvals[0],
#                     "t_alpha": tvals[1], "p_alpha": pvals[1],
#                     "t_q": tvals[2], "p_q": pvals[2],
#                     "t_m": tvals[3], "p_m": pvals[3],
#                 })
                
#                 # 添加预测结果到 df 中，用于绘图
#                 df[f"pred_new_{name}"] = dN_pred
#                 df[f"pred_cum_{name}"] = cum_pred
#                 valid_models.append(name) # 标记为成功拟合
                
#             except Exception as e:
#                 print(f"❌ 拟合 {name} 失败: {e}")
                
#         # 4. 保存最终结果
#         if results:
#             pd.DataFrame(results).to_csv(os.path.join(OUTPUT_DIR, OUTPUT_CSV), index=False)
#             print(f"\n🎉 所有拟合结果已保存至 {os.path.join(OUTPUT_DIR, OUTPUT_CSV)}")
        
#         # 5. 【新增绘图逻辑】
#         if valid_models:
#             # --- 图 1: 新增量 dN/dt 对比 ---
#             plt.figure(figsize=(12, 6))
#             plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
#             for name in valid_models:
#                 # 关键修正：排除 Exponential 模型绘图
#                 if name == MODEL_NAME_EXP:
#                     continue
#                 plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"Fit: {name}")
#             plt.xlabel("日期"); plt.ylabel("新增开发者 dN/dt")
#             plt.title(f"新增量拟合对比 ({EXOGENOUS_VAR})")
#             plt.legend(); plt.tight_layout()
#             plt.savefig(os.path.join(OUTPUT_DIR, f"new_dev_fit_compare_{EXOGENOUS_VAR}.png"), dpi=300)
#             plt.show()

#             # --- 图 2: 累计量 N(t) 对比 ---
#             plt.figure(figsize=(12, 6))
#             plt.plot(df[DATE_COL], df[CUM_COL], label="真实累计 N(t)", color="black", linewidth=2)
#             for name in valid_models:
#                  # 关键修正：排除 Exponential 模型绘图
#                 if name == MODEL_NAME_EXP:
#                     continue
#                 plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"Fit: {name}")
#             plt.xlabel("日期"); plt.ylabel("累积开发者 N(t)")
#             plt.title(f"累计曲线拟合对比 (N0={N_start:.0f}) ({EXOGENOUS_VAR})")
#             plt.legend(); plt.tight_layout()
#             plt.savefig(os.path.join(OUTPUT_DIR, f"cum_dev_fit_compare_{EXOGENOUS_VAR}.png"), dpi=300)
#             plt.show()
        
#     except ValueError as ve:
#         print(f"❌ 数据错误: {ve}")
#     except Exception as e:
#         print(f"❌ 运行过程中发生错误: {e}")

# if __name__ == "__main__":
#     main()


# =========
# 下面这段代码是根据model1.py修改的 离散bass拟合 和上面代码结果一样
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL   = "date"
NEW_COL    = "btc_new_developers"
CUM_COL    = "btc_cum_users"
PRICE_COL  = "btc_vol_30d"   # <-- 已经是滞后的价格列

# btc_price_lag1	
# ln_btc_price_lag1
# btc_return_1d

# btc_return_7d	
# btc_vol_7d	
# btc_ma_7d	
# btc_trend_7d	

# btc_return_14	
# btc_vol_14d	
# btc_ma_14d	
# btc_trend_14d	

# btc_return_21	
# btc_vol_21d	
# btc_ma_21d	
# btc_trend_21d	

# btc_return_30	
# btc_vol_30d	
# btc_ma_30d	
# btc_trend_30d


START_DATE = "2017-07-01"
END_DATE   = "2018-10-01"

OUTPUT_PNG_NEW = "btc_bass_pricefit_new.png"
OUTPUT_PNG_CUM = "btc_bass_pricefit_cum.png"
OUTPUT_CSV     = "btc_bass_pricefit_results.csv"
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

    # 用户输入的价格列直接使用
    df["price_input"] = df[PRICE_COL].values

    # ★ 使用 N(t-1) 预测 dN(t)
    df["N_lag"] = df[CUM_COL].shift(1)
    df["N_lag"] = df["N_lag"].fillna(df[CUM_COL].iloc[0])

    return df


# --------- Bass 离散模型（新版：使用 N_lag） ----------
def dN_pred(N_lag, p_t, q, m):
    remaining_market = np.maximum(m - N_lag, 0)
    return (p_t + q * (N_lag / m)) * remaining_market


# --------- 数据标准化 ----------
def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


# price 变换
def price_identity(price): 
    return normalize(price)

def price_log(price): 
    return normalize(np.log(np.maximum(price, 1e-8)))


# --------- baseline：constant p ----------
def compute_pred_constant_p(df, params):
    p0, q, m = params
    N_lag = df["N_lag"].values
    p_t = np.full(len(df), p0)
    return dN_pred(N_lag, p_t, q, m), p_t


def residuals_constant_p(params, df):
    p0, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_pred_constant_p(df, params)
    return df[NEW_COL].values - dN_predicted


# --------- price-driven model ----------
def compute_prediction(df, params, price_func):
    p0, alpha, q, m = params
    price = df["price_input"].values

    p_input = price_func(price)
    p_t = np.maximum(p0 + alpha * p_input, 0)

    N_lag = df["N_lag"].values
    return dN_pred(N_lag, p_t, q, m), p_t


def residuals(params, df, price_func):
    p0, alpha, q, m = params

    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6

    dN_predicted, _ = compute_prediction(df, params, price_func)
    return df[NEW_COL].values - dN_predicted


# --------- 参数显著性检验 ----------
def print_parameter_table(model_name, params, se, tvals, pvals, param_names):
    print(f"\n--- {model_name} 参数显著性 ---")
    print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
    print("---------------------------------------------------")

    for name, val, s, tval, pval in zip(param_names, params, se, tvals, pvals):
        print(f"{name:<10}{val:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}")

    print("---------------------------------------------------\n")


def significance(df, params, compute_pred_func, k):
    eps = 1e-8
    n = len(df)

    y_pred, _ = compute_pred_func(df, params)

    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
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


# --------- 主程序 ----------
def main():

    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    results = []
    valid_models = []

    # ================= baseline =====================
    print(f"\n=== 拟合模型：constant_p ===")
    m_guess = 1.2 * df[CUM_COL].max()

    res0 = least_squares(residuals_constant_p,
                         x0=[0.01, 0.3, m_guess],
                         bounds=([1e-6, 0, 0.5*m_guess],
                                 [1, 1.0, 20*m_guess]),
                         args=(df,), method="trf")

    if res0.success:
        params = res0.x
        p0, q, m = params

        dN_pred0, _ = compute_pred_constant_p(df, params)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_pred0)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred0)**2))

        print(f"✔ baseline：p0={p0:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")

        se, tvals, pvals = significance(df, params, compute_pred_constant_p, 3)
        print_parameter_table("constant_p", params, se, tvals, pvals, ["p0", "q", "m"])

        results.append({
            "model": "constant_p",
            "p0": p0, "alpha": 0,
            "q": q, "m": m,
            "RMSE": rmse
        })

        df["pred_new_constant_p"] = dN_pred0
        df["pred_cum_constant_p"] = cum_pred
        valid_models.append("constant_p")

    # ================= price-driven ==================
    models = {
        "linear_price": price_identity,
        "log_price": price_log
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

        se, tvals, pvals = significance(df, params,
                                        lambda df, p: compute_prediction(df, p, func),
                                        4)

        print(f"✔ {name}：p0={p0:.6f}, α={alpha:.6f}, q={q:.6f}, m={m:.1f}, RMSE={rmse:.3f}")
        print_parameter_table(name, params, se, tvals, pvals, ["p0", "alpha", "q", "m"])

        results.append({
            "model": name,
            "p0": p0, "alpha": alpha,
            "q": q, "m": m,
            "RMSE": rmse
        })

        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_pred
        valid_models.append(name)

    # 保存结果
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✔ 拟合结果已保存至：{OUTPUT_CSV}")


    # ---------- 绘图 ----------
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=name)
    plt.legend(); plt.title("每日新增")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_NEW, dpi=300)


    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=name)
    plt.legend(); plt.title("累积开发者")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_CUM, dpi=300)

    plt.show()


if __name__ == "__main__":
    main()