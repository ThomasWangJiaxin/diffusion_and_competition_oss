# logistic模型参数和gompertz一样 都是三个  K：最终饱和规模（market potential），r：增长速度（diffusion speed），t0：拐点时间（inflection point）

# 每天新增的连续型拟合
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
# from sklearn.metrics import r2_score

# # ==============================
# # 1. 读取数据
# # ==============================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# df = pd.read_csv(file_path)

# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# # 时间索引（从0开始）
# df['t'] = (df['date'] - df['date'].min()).dt.days

# t = df['t'].values
# y = df['btc_new_developers'].values

# # ==============================
# # 2. Logistic daily inflow函数
# # ==============================
# def logistic_daily(t, K, r, t0):
#     exp_term = np.exp(-r * (t - t0))
#     return (r * K * exp_term) / ((1 + exp_term) ** 2)

# # ==============================
# # 3. 参数拟合
# # ==============================
# K_init = df['btc_cum_users'].max() * 1.2
# r_init = 0.01
# t0_init = np.median(t)

# p0 = [K_init, r_init, t0_init]

# params, _ = curve_fit(logistic_daily, t, y, p0=p0, maxfev=200000)
# K_hat, r_hat, t0_hat = params

# print("Estimated parameters:")
# print(f"K={K_hat:.4f}, r={r_hat:.6f}, t0={t0_hat:.2f}")

# # 预测
# df['pred'] = logistic_daily(t, K_hat, r_hat, t0_hat)

# # ==============================
# # 4. 评价指标函数
# # ==============================
# def compute_metrics(y_true, y_pred, k_params=3):
#     y_true = np.array(y_true)
#     y_pred = np.array(y_pred)
    
#     n = len(y_true)
    
#     MAD = np.mean(np.abs(y_true - y_pred))
#     SSE = np.sum((y_true - y_pred) ** 2)
#     MSE = SSE / n
#     RMSE = np.sqrt(MSE)
    
#     R2 = r2_score(y_true, y_pred)
#     Adj_R2 = 1 - (1 - R2) * (n - 1) / (n - k_params - 1)
    
#     # 避免除0
#     nonzero = y_true != 0
#     MAPE = np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
#     WAPE = np.sum(np.abs(y_true - y_pred)) / np.sum(y_true) * 100
    
#     return {
#         "MAD": MAD,
#         "SSE": SSE,
#         "MSE": MSE,
#         "RMSE": RMSE,
#         "R2": R2,
#         "Adj_R2": Adj_R2,
#         "MAPE": MAPE,
#         "WAPE": WAPE
#     }

# # ==============================
# # 5. 三个时间区间
# # ==============================
# periods = {
#     "Overall": df,
#     "Peak1": df[(df['date'] >= "2017-01-01") & (df['date'] <= "2019-01-01")],
#     "Peak2": df[(df['date'] >= "2020-10-01") & (df['date'] <= "2022-10-01")]
# }

# results = {}

# for name, sub in periods.items():
#     metrics = compute_metrics(sub['btc_new_developers'], sub['pred'])
#     results[name] = metrics

# results_df = pd.DataFrame(results)
# print("\nEvaluation Results:")
# print(results_df)

# # ==============================
# # 6. 画图并保存PNG
# # ==============================
# plt.figure(figsize=(12,6))

# plt.plot(df['date'], df['btc_new_developers'], label='Actual Daily New Developers', alpha=0.7)
# plt.plot(df['date'], df['pred'], label='Logistic Fitted Daily Inflow', linewidth=2)

# plt.axvspan(pd.to_datetime("2017-01-01"), pd.to_datetime("2019-01-01"), alpha=0.15)
# plt.axvspan(pd.to_datetime("2020-10-01"), pd.to_datetime("2022-10-01"), alpha=0.15)

# plt.title("BTC Developer Adoption - Logistic Daily Inflow Fit")
# plt.xlabel("Date")
# plt.ylabel("Daily New Developers")
# plt.legend()
# plt.grid(alpha=0.3)

# output_path = "/home/lab0/survival_diffusion_github/Baselines/btc_logistic_daily_fit.png"
# plt.savefig(output_path, dpi=300, bbox_inches='tight')

# print(f"\nPNG saved to: {output_path}")


# 每天新增的离散拟合 Peak1和2分开拟合（各自独立拟合）
# cum_users用的是窗口内最后一天减去第一天
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from scipy import stats

# ===============================
# 1. 读取数据
# ===============================
file_path = "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv"
df = pd.read_csv(file_path)

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

df['t'] = (df['date'] - df['date'].min()).dt.days

y_all = df['new_developers'].values
t_all = df['t'].values

# ===============================
# 2. Logistic 累计函数
# ===============================
def logistic_cum(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))

# ===============================
# 3. 离散 daily inflow
# ===============================
def logistic_daily(t, K, r, t0):
    t = np.array(t)
    cum_t       = logistic_cum(t,     K, r, t0)
    cum_t_minus = logistic_cum(t - 1, K, r, t0)
    return cum_t - cum_t_minus

# ===============================
# 4. 拟合函数（加入统计推断）
# ===============================
def fit_logistic_discrete(t, y, cum_max):
    """
    cum_max: 该窗口内 cum_users 的最大值
    """
    K0  = cum_max * 1.2        # 初始猜测：已观测最大值的 1.2 倍
    r0  = 0.01
    t00 = np.median(t)

    popt, pcov = curve_fit(
        logistic_daily,
        t,
        y,
        p0=[K0, r0, t00],
        bounds=(
            [cum_max * 1.05, 0.001, t.min() - 365 * 2],  # K 下界 ≥ 已观测最大累计值
            [cum_max * 10.0, 1.0,   t.max() + 365 * 2]   # K 上界 = 10 倍已观测最大值
        ),
        maxfev=20000
    )

    y_pred = logistic_daily(t, *popt)

    # 统计推断
    se      = np.sqrt(np.diag(pcov))
    t_stats = popt / se
    dfree   = len(t) - len(popt)
    p_values= 2 * (1 - stats.t.cdf(np.abs(t_stats), df=dfree))

    param_table = pd.DataFrame({
        "param":     ["K", "r", "t0"],
        "estimate":  popt,
        "std_error": se,
        "t_value":   t_stats,
        "p_value":   p_values
    })

    return popt, y_pred, param_table

# ===============================
# 5. 评价指标
# ===============================
def compute_metrics(y_true, y_pred, k_params):
    T     = len(y_true)
    error = y_true - y_pred

    MAD   = np.mean(np.abs(error))
    SSE   = np.sum(error ** 2)
    MSE   = SSE / T
    RMSE  = np.sqrt(MSE)
    R2    = r2_score(y_true, y_pred)
    adj_R2= 1 - (1 - R2) * (T - 1) / (T - k_params - 1)

    y_safe= np.where(y_true == 0, 1e-8, y_true)
    MAPE  = np.mean(np.abs(error / y_safe)) * 100
    WAPE  = np.sum(np.abs(error)) / np.sum(y_safe) * 100

    return {"MAD": MAD, "SSE": SSE, "MSE": MSE, "RMSE": RMSE,
            "R2": R2, "Adj_R2": adj_R2, "MAPE": MAPE, "WAPE": WAPE}

# ===============================
# 6. 时间窗口划分 + 窗口内局部累计
# ===============================
def get_period(df, start, end):
    sub = df[(df['date'] >= start) & (df['date'] <= end)].copy()
    sub['t_sub'] = (sub['date'] - sub['date'].min()).dt.days
    # 窗口内累计
    sub['cum_users_sub'] = sub['new_developers'].cumsum()
    return sub

periods = {
    "Overall": df.assign(cum_users_sub=df['new_developers'].cumsum()),  # 整体累积
    "Peak1":   get_period(df, "2017-01-01", "2019-01-01"),
    "Peak2":   get_period(df, "2020-10-01", "2023-01-01")
}

# ===============================
# 7. 拟合 + 记录结果
# ===============================
results       = {}
fit_curves    = {}
param_results = {}

for name, data in periods.items():

    t = data['t'].values if name == "Overall" else data['t_sub'].values
    y = data['new_developers'].values

    cum_max = data['cum_users_sub'].max()  # 使用窗口内累计最大值

    popt, y_pred, param_table = fit_logistic_discrete(t, y, cum_max)

    metrics = compute_metrics(y, y_pred, k_params=3)

    results[name]       = metrics
    fit_curves[name]    = (data['date'], y, y_pred)
    param_results[name] = param_table

# ===============================
# 8. 输出评价指标
# ===============================
results_df = pd.DataFrame(results).T
print("\n===== Discrete Logistic Fit Metrics =====\n")
print(results_df.T.round(4))

# ===============================
# 9. 输出参数显著性
# ===============================
for name, table in param_results.items():
    print(f"\n===== Parameter Estimates ({name}) =====")
    print(table.round(6))

# ===============================
# 10. 画图
# ===============================
fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=False)
titles = ["Overall Period", "Peak 1 (2017–2019)", "Peak 2 (2020–2023)"]

for ax, (name, (dates, y_true, y_pred)), title in zip(axes, fit_curves.items(), titles):
    ax.plot(dates, y_true, label="Observed Daily Developers")
    ax.plot(dates, y_pred, linestyle='--', label="Fitted Logistic (Discrete)")
    ax.set_title(title)
    ax.set_ylabel("Daily New Developers")
    ax.legend()

axes[-1].set_xlabel("Date")

plt.tight_layout()
plt.savefig("/home/lab0/survival_diffusion_github/Baselines/eth_logistic_discrete_daily_fit_windowed.png", dpi=300)
plt.show()