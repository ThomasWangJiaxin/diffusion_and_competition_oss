import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt

# ===============================
# Peak1 竞争者：Cosmos, Bitcoin, TRON, Solana
# 时间窗口：2017-01-01 ~ 2019-01-01
# cum_user 改为窗口内累积（从窗口起点重置为0开始累加）
# ===============================

# 1. 定义文件路径
target_path = "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv"

competitors = {
    'Cosmos':  "/home/lab0/survival_diffusion_github/Ethereum/cosmos_first_actor_count_2025_12_31.csv",
    'Bitcoin': "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv",
    'TRON':    "/home/lab0/survival_diffusion_github/Ethereum/tron_first_actor_count_2025_12_31.csv",
    'SOLANA':  "/home/lab0/survival_diffusion_github/Ethereum/solana_first_actor_count_2025_12_31.csv",
}

# 2. 读取数据
df_target = pd.read_csv(target_path)[['date', 'new_developers', 'cum_users']]
df_target['date'] = pd.to_datetime(df_target['date'])
df_target = df_target.rename(columns={'cum_users': 'cum_target_global'})

df_comp = {}
for name, path in competitors.items():
    tmp = pd.read_csv(path)[['date', 'new_developers', 'cum_users']]
    tmp['date'] = pd.to_datetime(tmp['date'])
    tmp = tmp.rename(columns={
        'new_developers': f'new_{name}',
        'cum_users': f'cum_{name}_global'
    })
    df_comp[name] = tmp

# 合并所有数据
df = df_target.copy()
for name, df_c in df_comp.items():
    df = pd.merge(df, df_c[['date', f'new_{name}', f'cum_{name}_global']], on='date', how='inner')
df = df.sort_values('date').reset_index(drop=True)

dt = 1.0

# ===============================
# 辅助：将全局 cum 重置为窗口内累积
# ===============================
def window_cum(global_cum_series):
    """
    将全局累积序列重置为窗口内累积：
    窗口第一个值设为0，后续值 = global[t] - global[0]
    """
    arr = np.array(global_cum_series, dtype=float)
    return arr - arr[0]

# ===============================
# 3. MSB 残差函数（多竞争对手版，使用窗口内累积）
# ===============================
def msb_residuals(params, y_obs, X_target_cum, comp_cum_list, dt, m_comp_list, n_obs):
    p1, q1, m1 = params[:3]
    gamma_list = params[3:]

    residuals = []
    X1 = 0.0

    for t in range(n_obs):
        self_term = (p1 + q1 * X1 / m1) * (m1 - X1) * dt

        comp_term = 0.0
        for j, gamma_j in enumerate(gamma_list):
            comp_term += gamma_j * X1 * (m_comp_list[j] - comp_cum_list[j][t]) * dt

        dX1 = self_term + comp_term
        dX1 = max(dX1, 0)

        residuals.append(y_obs[t] - dX1)
        X1 += dX1

    return np.array(residuals)

# ===============================
# 4. 计算参数统计量
# ===============================
def compute_param_stats(result, y_obs, param_names, n_params):
    n = len(y_obs)
    k = n_params
    jac = result.jac
    try:
        JtJ_inv = np.linalg.inv(jac.T @ jac)
        MSE = result.cost / (n - k)
        pcov = JtJ_inv * MSE
    except np.linalg.LinAlgError:
        return None

    param_se = np.sqrt(np.diag(pcov))
    t_stats = result.x / param_se
    df_val = n - k
    p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df_val))

    param_stats = {}
    for i, name in enumerate(param_names):
        param_stats[name] = {
            'Estimate':  result.x[i],
            'Std.Error': param_se[i],
            't_value':   t_stats[i],
            'p_value':   p_values[i]
        }
    return param_stats

# ===============================
# 5. 拟合和报告函数
# ===============================
def fit_and_report(period_name, y_obs, X_target_cum, comp_cum_list, n_obs, m_comp_est):
    n_comp = len(competitors)
    initial_params = [0.0005, 0.08, X_target_cum.max() * 1.2] + [0.00005] * n_comp
    bounds_lower   = [1e-6, 1e-3, X_target_cum.max() * 1.05] + [-0.001] * n_comp
    bounds_upper   = [0.05, 0.5,  X_target_cum.max() * 10]   + [ 0.001] * n_comp
    bounds = (bounds_lower, bounds_upper)

    result = least_squares(
        msb_residuals,
        initial_params,
        args=(y_obs, X_target_cum, comp_cum_list, dt, m_comp_est, n_obs),
        bounds=bounds,
        method='trf',
        ftol=1e-8, xtol=1e-8,
        verbose=0
    )

    p1, q1, m1 = result.x[:3]
    gamma_list = result.x[3:]

    print("\n" + "=" * 80)
    print(f"{period_name} Fitting  [cum_user = 窗口内累积]")
    print("=" * 80)
    print(f"\n拟合参数：")
    print(f"p1 (创新系数): {p1:.6f}")
    print(f"q1 (模仿系数): {q1:.6f}")
    print(f"m1 (ETH 市场潜力): {m1:,.0f}")
    for i, name in enumerate(competitors):
        print(f"γ_{name} (竞争强度): {gamma_list[i]:.6f}")
    print(f"优化状态: {result.message}, cost: {result.cost:.4f}")

    param_names = ['p1', 'q1', 'm1'] + [f'gamma_{name}' for name in competitors]
    param_stats = compute_param_stats(result, y_obs, param_names, len(param_names))

    print("\n" + "=" * 80)
    print(f"Parameter Estimates and Significance Tests ({period_name}):")
    print("=" * 80)
    if param_stats:
        param_df = pd.DataFrame(param_stats).T
        param_df.columns = ['Estimate', 'Std.Error', 't_value', 'p_value']
        print(param_df.to_string())

    # 生成拟合值
    fitted = np.zeros(n_obs)
    X1 = 0.0
    for t in range(n_obs):
        self_term = (p1 + q1 * X1 / m1) * (m1 - X1) * dt
        comp_term = sum(gamma_list[j] * X1 * (m_comp_est[j] - comp_cum_list[j][t]) * dt
                        for j in range(n_comp))
        dX1 = max(self_term + comp_term, 0)
        fitted[t] = dX1
        X1 += dX1

    return result, fitted, param_stats

# ===============================
# 6. 计算指标
# ===============================
def compute_metrics(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    error  = y_true - y_pred
    MAD  = np.mean(np.abs(error))
    SSE  = np.sum(error ** 2)
    MSE  = SSE / len(y_true)
    RMSE = np.sqrt(MSE)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    R2   = 1 - SSE / ss_tot if ss_tot != 0 else np.nan
    n, p = len(y_true), 3 + len(competitors)
    Adj_R2 = 1 - (1 - R2) * (n - 1) / (n - p - 1) if n > p + 1 else np.nan
    y_safe = np.where(y_true == 0, 1e-10, y_true)
    MAPE = np.mean(np.abs(error / y_safe)) * 100
    WAPE = np.sum(np.abs(error)) / np.sum(y_safe) * 100
    return {"MAD": MAD, "SSE": SSE, "MSE": MSE, "RMSE": RMSE,
            "R2": R2, "Adj_R2": Adj_R2, "MAPE": MAPE, "WAPE": WAPE}

# ===============================
# 7. 全样本拟合（全局 cum 保持不变，作为基准参考）
# ===============================
y_full = df['new_developers'].values.astype(float)
# 全样本使用全局累积
X_target_cum_full  = df['cum_target_global'].values.astype(float)
comp_cum_list_full = [df[f'cum_{name}_global'].values.astype(float) for name in competitors]
n_days_full        = len(y_full)
m_comp_est_full    = [cum.max() * 1.2 for cum in comp_cum_list_full]

result_full, fitted_full, _ = fit_and_report(
    "Full Sample", y_full, X_target_cum_full, comp_cum_list_full, n_days_full, m_comp_est_full
)
print("\n全样本 in-sample 指标：")
for k, v in compute_metrics(y_full, fitted_full).items():
    print(f"{k}: {v:.4f}")

# ===============================
# 8. Peak1 独立拟合（窗口内累积）
# ===============================
peak1_mask = (df['date'] >= '2017-01-01') & (df['date'] <= '2019-01-01')
df_peak1   = df[peak1_mask].reset_index(drop=True)

if len(df_peak1) > 3 + len(competitors):
    y_peak1 = df_peak1['new_developers'].values.astype(float)

    # ★ 窗口内累积：从窗口起点重置为 0
    X_target_cum_peak1  = window_cum(df_peak1['cum_target_global'].values)
    comp_cum_list_peak1 = [window_cum(df_peak1[f'cum_{name}_global'].values)
                           for name in competitors]
    n_days_peak1  = len(y_peak1)
    m_comp_est_peak1 = [cum.max() * 1.2 for cum in comp_cum_list_peak1]

    result_peak1, fitted_peak1, _ = fit_and_report(
        "Peak1 (2017-01-01 to 2019-01-01)",
        y_peak1, X_target_cum_peak1,
        comp_cum_list_peak1, n_days_peak1, m_comp_est_peak1
    )
    print("\nPeak 1 指标：")
    for k, v in compute_metrics(y_peak1, fitted_peak1).items():
        print(f"{k}: {v:.4f}")
else:
    print("\nPeak1 样本量不足，跳过拟合")
    fitted_peak1 = None

# ===============================
# 9. 绘图保存
# ===============================
plt.figure(figsize=(14, 7))
plt.plot(df['date'], y_full, label='Actual New Developers (ETH)', color='blue', alpha=0.7)
plt.plot(df['date'], fitted_full, label='MSB Fitted (Full Sample)', color='red', linewidth=2)
if fitted_peak1 is not None:
    plt.plot(df_peak1['date'], fitted_peak1, label='MSB Fitted (Peak1)', color='green', linewidth=2)
plt.axvspan(pd.to_datetime('2017-01-01'), pd.to_datetime('2019-01-01'),
            color='gray', alpha=0.15, label='Peak 1 Period')
plt.xlabel('Date')
plt.ylabel('Daily New Developers')
plt.title('MSB Model – Peak1 (ETH vs Cosmos/Bitcoin/TRON/Solana)\n[cum_user = window-cumulative]')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('msb_eth_peak1_fit.png', dpi=300)
plt.show()