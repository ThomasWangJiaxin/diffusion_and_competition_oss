# /home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv中有date，btc_new_developers和btc_cum_users列，请进行python Gompertz模型的拟合，最后分别输出总的时间段、2017.1.1-2019.1.1和2020.10.1-2022.10.1三个时间段的MAD、SSE、MSE、RMSE、R2、adjusted R2、MAPE、WAPE评价指标 最后保存png 并说明参数

# 用累计拟合连续型
# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
# from sklearn.metrics import r2_score
# import matplotlib.pyplot as plt

# # ===============================
# # 1. 读取数据
# # ===============================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# df = pd.read_csv(file_path)

# # 转换日期
# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# # 使用累计开发者作为拟合对象
# df['t'] = (df['date'] - df['date'].min()).dt.days
# y = df['btc_cum_users'].values
# t = df['t'].values


# # ===============================
# # 2. Gompertz 模型
# # ===============================
# def gompertz(t, K, b, t0):
#     return K * np.exp(-np.exp(-b * (t - t0)))


# # ===============================
# # 3. 拟合函数
# # ===============================
# def fit_gompertz(t, y):
#     # 初始值设置
#     K0 = max(y) * 1.2 # 同bass中m的设置 最终饱和规模
#     b0 = 0.01  # 增长速度
#     t0_0 = np.median(t) # 拐点

#     popt, _ = curve_fit(gompertz, t, y, p0=[K0, b0, t0_0], maxfev=10000)
#     y_pred = gompertz(t, *popt)
#     return popt, y_pred


# # ===============================
# # 4. 评价指标函数
# # ===============================
# def compute_metrics(y_true, y_pred, k_params):
#     T = len(y_true)

#     error = y_true - y_pred

#     MAD = np.mean(np.abs(error))
#     SSE = np.sum(error**2)
#     MSE = SSE / T
#     RMSE = np.sqrt(MSE)

#     # R2
#     R2 = r2_score(y_true, y_pred)

#     # Adjusted R2
#     adj_R2 = 1 - (1 - R2) * (T - 1) / (T - k_params - 1)

#     # MAPE
#     MAPE = np.mean(np.abs(error / y_true)) * 100

#     # WAPE
#     WAPE = np.sum(np.abs(error)) / np.sum(y_true) * 100

#     return {
#         "MAD": MAD,
#         "SSE": SSE,
#         "MSE": MSE,
#         "RMSE": RMSE,
#         "R2": R2,
#         "Adj_R2": adj_R2,
#         "MAPE": MAPE,
#         "WAPE": WAPE
#     }


# # ===============================
# # 5. 不同时间窗口划分
# # ===============================
# def get_period(df, start, end):
#     mask = (df['date'] >= start) & (df['date'] <= end)
#     sub = df.loc[mask].copy()
#     sub['t_sub'] = (sub['date'] - sub['date'].min()).dt.days
#     return sub


# periods = {
#     "Overall": df,
#     "Peak1": get_period(df, "2017-01-01", "2019-01-01"),
#     "Peak2": get_period(df, "2020-10-01", "2022-10-01")
# }


# # ===============================
# # 6. 逐个时间段拟合并输出指标
# # ===============================
# results = {}

# for name, data in periods.items():

#     t_sub = data['t_sub'].values if name != "Overall" else data['t'].values
#     y_sub = data['btc_cum_users'].values

#     # 拟合
#     popt, y_pred = fit_gompertz(t_sub, y_sub)

#     # 指标
#     metrics = compute_metrics(y_sub, y_pred, k_params=3)

#     results[name] = metrics


# # ===============================
# # 7. 输出结果
# # ===============================
# results_df = pd.DataFrame(results).T
# print("\nGompertz Model Evaluation Results:\n")
# print(results_df.T.round(4))


# # ===============================
# # 8. 绘图函数
# # ===============================
# def plot_fit(ax, t, y_true, y_pred, title):
#     ax.plot(t, y_true, label="Actual", linewidth=2)
#     ax.plot(t, y_pred, linestyle="--", label="Gompertz Fit", linewidth=2)
#     ax.set_title(title)
#     ax.set_xlabel("Time (days)")
#     ax.set_ylabel("Cumulative Developers")
#     ax.legend()
#     ax.grid(True)


# # ===============================
# # 9. 重新拟合并绘图
# # ===============================
# fig, axes = plt.subplots(3, 1, figsize=(10, 15))

# for i, (name, data) in enumerate(periods.items()):

#     t_sub = data['t_sub'].values if name != "Overall" else data['t'].values
#     y_sub = data['btc_cum_users'].values

#     popt, y_pred = fit_gompertz(t_sub, y_sub)

#     plot_fit(axes[i], t_sub, y_sub, y_pred, name)

# plt.tight_layout()

# # ===============================
# # 10. 保存为 PNG
# # ===============================
# output_path = "/home/lab0/survival_diffusion_github/Baselines/btc_gompertz_fit.png"
# plt.savefig(output_path, dpi=300)

# print(f"\nFigure saved to: {output_path}")


# 用每天新增拟合连续型 全样本拟合一次、peak1独立拟合、peak2独立拟合
# 参数,含义（在此模型中）,代码中初始值 p0,代码中 bounds,推荐 bounds,推荐初始值建议
# K,缩放/峰值高度因子,cum_users.max() × 1.2,"(-∞, +∞)","(0, +∞) 或 (小正数, cum_max×5)",cum_users.max() × 1.1 ~ 1.5
# b,增长/衰减速率,0.01,"(-∞, +∞)","(1e-5, 0.5 ~ 1.0)",0.005 ~ 0.05（视数据跨度）
# t0,峰值/拐点时间位置,中位数时间（np.median(t)）,"(-∞, +∞)","(-∞, +∞) 或 数据范围 ±2年",中位数 或 视觉估计的峰值位置
# cum_users是用窗口最后一天减去第一天
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
df['y_daily'] = df['new_developers']

# ===============================
# 2. Gompertz 累计 + 导数模型
# ===============================
def gompertz(t, K, b, t0):
    return K * np.exp(-np.exp(-b * (t - t0)))

def gompertz_pdf(t, K, b, t0):
    return K * b * np.exp(-b * (t - t0)) * np.exp(-np.exp(-b * (t - t0)))

# ===============================
# 3. 拟合函数（加入统计显著性）
# ===============================
def fit_gompertz_daily(t, y, cum_window):
    """
    cum_window: 该窗口内新增的累积用户数（窗口最后一天 - 窗口第一天）
    K 的下界设为 cum_window * 1.01，确保市场容量始终大于窗口内新增用户数。
    K 的上界设为 cum_window * 10.0，给优化器足够搜索空间。
    """
    K0   = cum_window * 1.2       # 初始猜测：窗口新增用户数的 1.2 倍
    b0   = 0.01
    t0_0 = np.median(t)
    popt, pcov = curve_fit(
        gompertz_pdf,
        t,
        y,
        p0=[K0, b0, t0_0],
        bounds=(
            [cum_window * 1.05, 0.001, t.min() - 365 * 2],  # K 下界 ≥ 窗口内新增累积用户数
            [cum_window * 10.0, 1.0,   t.max() + 365 * 2]   # K 上界 = 10 倍窗口新增用户数
        ),
        maxfev=20000
    )
    y_pred = gompertz_pdf(t, *popt)
    
    # 统计推断
    se       = np.sqrt(np.diag(pcov))
    t_stats  = popt / se
    dfree    = len(t) - len(popt)
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=dfree))
    param_table = pd.DataFrame({
        "param":     ["K", "b", "t0"],
        "estimate":  popt,
        "std_error": se,
        "t_value":   t_stats,
        "p_value":   p_values
    })
    
    return popt, y_pred, param_table

# ===============================
# 4. 评价指标函数
# ===============================
def compute_metrics(y_true, y_pred, k_params):
    T     = len(y_true)
    error = y_true - y_pred
    MAD    = np.mean(np.abs(error))
    SSE    = np.sum(error ** 2)
    MSE    = SSE / T
    RMSE   = np.sqrt(MSE)
    R2     = r2_score(y_true, y_pred)
    adj_R2 = 1 - (1 - R2) * (T - 1) / (T - k_params - 1)
    MAPE   = np.mean(np.abs(error / (y_true + 1e-8))) * 100
    WAPE   = np.sum(np.abs(error)) / (np.sum(y_true) + 1e-8) * 100
    return {"MAD": MAD, "SSE": SSE, "MSE": MSE, "RMSE": RMSE,
            "R2": R2, "Adj_R2": adj_R2, "MAPE": MAPE, "WAPE": WAPE}

# ===============================
# 5. 划分时间段
# ===============================
def get_period(df, start, end):
    mask = (df['date'] >= start) & (df['date'] <= end)
    sub  = df.loc[mask].copy()
    sub['t_sub'] = (sub['date'] - sub['date'].min()).dt.days
    return sub

periods = {
    "Overall": df,
    "Peak1":   get_period(df, "2017-01-01", "2019-01-01"),
    "Peak2":   get_period(df, "2020-10-01", "2023-01-01")
}

# ===============================
# 6. 拟合 + 评价
# ===============================
results       = {}
predictions   = {}
param_results = {}

for name, data in periods.items():
    t_sub   = data['t'].values if name == "Overall" else data['t_sub'].values
    y_sub   = data['y_daily'].values
    
    # 计算该窗口内新增的累积用户数（最后一天 - 第一天）
    cum_start = data['cum_users'].iloc[0]
    cum_end   = data['cum_users'].iloc[-1]
    cum_window = cum_end - cum_start
    
    print(f"\n{name} 窗口分析:")
    print(f"  窗口第一天累积值: {cum_start}")
    print(f"  窗口最后一天累积值: {cum_end}")
    print(f"  窗口内新增累积用户数: {cum_window}")
    
    popt, y_pred, param_table = fit_gompertz_daily(t_sub, y_sub, cum_window)
    metrics = compute_metrics(y_sub, y_pred, k_params=3)
    
    results[name]       = metrics
    predictions[name]   = (t_sub, y_sub, y_pred)
    param_results[name] = param_table

# ===============================
# 7. 输出评价指标
# ===============================
results_df = pd.DataFrame(results)
print("\n\nGompertz Daily Inflow Model Results:\n")
print(results_df.round(4))

# ===============================
# 8. 输出参数估计 + 显著性
# ===============================
for name, table in param_results.items():
    print(f"\n===== Parameter Estimates ({name}) =====")
    print(table.round(6))

# ===============================
# 9. 绘图函数
# ===============================
def plot_fit(ax, t, y_true, y_pred, title):
    ax.plot(t, y_true, label="Actual Daily New Developers", linewidth=2)
    ax.plot(t, y_pred, linestyle="--", label="Gompertz Predicted Daily", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("New Developers per Day")
    ax.legend()
    ax.grid(True)

# ===============================
# 10. 画三张图
# ===============================
fig, axes = plt.subplots(3, 1, figsize=(10, 14))
plot_fit(axes[0], *predictions["Overall"], "Overall Period (Daily Inflow)")
plot_fit(axes[1], *predictions["Peak1"],   "Peak1: 2017-01-01 to 2019-01-01")
plot_fit(axes[2], *predictions["Peak2"],   "Peak2: 2020-10-01 to 2023-01-01")
plt.tight_layout()

# ===============================
# 11. 保存 PNG
# ===============================
output_path = "/home/lab0/survival_diffusion_github/Baselines/eth_gompertz_daily_fit.png"
plt.savefig(output_path, dpi=300)
print(f"\nPNG saved to: {output_path}")
plt.show()

# 用每天新增拟合离散型 结果和上面还是差不多
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import minimize
# from sklearn.metrics import r2_score

# # ===============================
# # 1. 读取数据
# # ===============================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# df = pd.read_csv(file_path)

# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# df['t'] = (df['date'] - df['date'].min()).dt.days
# df['y_daily'] = df['btc_new_developers']

# # ===============================
# # 2. 离散 Gompertz 函数
# # ===============================
# def gompertz_discrete(N_t, K, b):
#     """
#     离散 Gompertz 增长公式
#     N_{t+1} = N_t * exp(b * (1 - ln(N_t/K)))
#     """
#     return N_t * np.exp(b * (1 - np.log(N_t / K)))

# def simulate_discrete_gompertz(N0, K, b, T):
#     """
#     用离散 Gompertz 模拟整个时间序列
#     返回每日新增 n_t = N_{t+1} - N_t
#     """
#     N_pred = np.zeros(T)
#     N_pred[0] = N0
#     for t in range(T - 1):
#         N_pred[t+1] = gompertz_discrete(N_pred[t], K, b)
#     # 每日新增
#     n_pred = np.diff(N_pred, prepend=N0)
#     return n_pred

# # ===============================
# # 3. 拟合函数
# # ===============================
# def fit_discrete_gompertz_daily(y_true):
#     N0 = y_true[0]
#     T = len(y_true)

#     # 初始猜测
#     K0 = max(y_true) * 10  # 离散版本可能需要放大初值
#     b0 = 0.01
#     x0 = [K0, b0]

#     # 损失函数 SSE
#     def sse(params):
#         K, b = params
#         y_pred = simulate_discrete_gompertz(N0, K, b, T)
#         return np.sum((y_true - y_pred) ** 2)

#     res = minimize(sse, x0, bounds=[(1.0, None), (0.0001, 1.0)], method='L-BFGS-B')

#     K_fit, b_fit = res.x
#     y_pred = simulate_discrete_gompertz(N0, K_fit, b_fit, T)
#     return K_fit, b_fit, y_pred

# # ===============================
# # 4. 指标计算
# # ===============================
# def compute_metrics(y_true, y_pred, k_params=2):
#     T = len(y_true)
#     error = y_true - y_pred

#     MAD = np.mean(np.abs(error))
#     SSE = np.sum(error**2)
#     MSE = SSE / T
#     RMSE = np.sqrt(MSE)

#     R2 = r2_score(y_true, y_pred)
#     adj_R2 = 1 - (1 - R2) * (T - 1) / (T - k_params - 1)

#     MAPE = np.mean(np.abs(error / (y_true + 1e-8))) * 100
#     WAPE = np.sum(np.abs(error)) / (np.sum(y_true) + 1e-8) * 100

#     return {
#         "MAD": MAD,
#         "SSE": SSE,
#         "MSE": MSE,
#         "RMSE": RMSE,
#         "R2": R2,
#         "Adj_R2": adj_R2,
#         "MAPE": MAPE,
#         "WAPE": WAPE
#     }

# # ===============================
# # 5. 时间段划分
# # ===============================
# def get_period(df, start, end):
#     mask = (df['date'] >= start) & (df['date'] <= end)
#     sub = df.loc[mask].copy()
#     sub['t_sub'] = (sub['date'] - sub['date'].min()).dt.days
#     return sub

# periods = {
#     "Overall": df,
#     "Peak1": get_period(df, "2017-01-01", "2019-01-01"),
#     "Peak2": get_period(df, "2020-10-01", "2022-10-01")
# }

# # ===============================
# # 6. 拟合 + 评价
# # ===============================
# results = {}
# predictions = {}

# for name, data in periods.items():
#     y_sub = data['y_daily'].values
#     K_fit, b_fit, y_pred = fit_discrete_gompertz_daily(y_sub)
#     metrics = compute_metrics(y_sub, y_pred, k_params=2)
#     results[name] = metrics
#     predictions[name] = (data['t'].values if name=="Overall" else data['t_sub'].values, y_sub, y_pred)

# # 输出表格
# results_df = pd.DataFrame(results).T
# print("\nDiscrete Gompertz Daily Inflow Model Results:\n")
# print(results_df.T.round(4))

# # ===============================
# # 7. 绘图函数
# # ===============================
# def plot_fit(ax, t, y_true, y_pred, title):
#     ax.plot(t, y_true, label="Actual Daily New Developers", linewidth=2)
#     ax.plot(t, y_pred, linestyle="--", label="Discrete Gompertz Predicted", linewidth=2)
#     ax.set_title(title)
#     ax.set_xlabel("Time (days)")
#     ax.set_ylabel("New Developers per Day")
#     ax.legend()
#     ax.grid(True)

# # ===============================
# # 8. 画三张图
# # ===============================
# fig, axes = plt.subplots(3, 1, figsize=(10, 14))

# plot_fit(axes[0], *predictions["Overall"], "Overall Period (Daily Inflow)")
# plot_fit(axes[1], *predictions["Peak1"], "Peak1: 2017-01-01 to 2019-01-01")
# plot_fit(axes[2], *predictions["Peak2"], "Peak2: 2020-10-01 to 2022-10-01")

# plt.tight_layout()

# # ===============================
# # 9. 保存 PNG
# # ===============================
# output_path = "/home/lab0/survival_diffusion_github/Baselines/btc_discrete_gompertz_daily_fit.png"
# plt.savefig(output_path, dpi=300)
# print(f"\nPNG saved to: {output_path}")

# plt.show()