import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt

# ============= 参数配置 =============
# Peak1: 2017-01-01 to 2019-01-01
# Internal: LBTC, BTG, BTCD, BCOIN, Parity, Lightning Network, Stacks, Rootstock
# External: Ethereum, Litecoin, Monero, Zcash, Dogecoin, TRON

START_DATE = '2017-01-01'
END_DATE   = '2019-01-01'
OUTPUT_FIG = 'msb_btc_peak1_fit.png'

target_path = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv"

competitors = {
    'ETH':       "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv",
    'LTC':       "/home/lab0/survival_diffusion_github/Bitcoin/litecoin_first_actor_count_timeline_event_2025_12_31.csv",
    'MONERO':    "/home/lab0/survival_diffusion_github/Bitcoin/monero_first_actor_count_timeline_event_2025_12_31.csv",
    'ZCASH':     "/home/lab0/survival_diffusion_github/Bitcoin/zcash_first_actor_count_2025_12_31.csv",
    'DOGE':      "/home/lab0/survival_diffusion_github/Bitcoin/dogecoin_first_actor_count_timeline_event_2025_12_31.csv",
    'TRON':      "/home/lab0/survival_diffusion_github/Bitcoin/tron_first_actor_count_2025_12_31.csv",
    'lbtc':      "/home/lab0/survival_diffusion_github/Bitcoin/lbtc_first_actor_count_timeline_event_2025_12_31.csv",
    'BTG':       "/home/lab0/survival_diffusion_github/Bitcoin/bitcoingpu_first_actor_count_2025_12_31.csv",
    'BTCD':      "/home/lab0/survival_diffusion_github/Bitcoin/btcd_first_actor_count_timeline_event_2025_12_31.csv",
    'bcoin':     "/home/lab0/survival_diffusion_github/Bitcoin/bcoin_first_actor_count_timeline_event_2025_12_31.csv",
    'parity':    "/home/lab0/survival_diffusion_github/Bitcoin/parity_first_actor_count_2025_12_31.csv",
    'LN':        "/home/lab0/survival_diffusion_github/Bitcoin/lightningnetwork_first_actor_count_2025_12_31.csv",
    'stack':     "/home/lab0/survival_diffusion_github/Bitcoin/stacks_first_actor_count_2025_12_31.csv",
    'rootstock': "/home/lab0/survival_diffusion_github/Bitcoin/rootstock_first_actor_count_2025_12_31.csv",
    'BCH':       "/home/lab0/survival_diffusion_github/Bitcoin/bitcoincash_first_actor_count_2025_12_31.csv"
}

# ============= 读取数据 =============
df_target = pd.read_csv(target_path)[['date', 'new_developers', 'cum_users']]
df_target['date'] = pd.to_datetime(df_target['date'])
df_target = df_target.rename(columns={'cum_users': 'cum_target'})

df_comp = {}
for name, path in competitors.items():
    df_comp[name] = pd.read_csv(path)[['date', 'new_developers', 'cum_users']]
    df_comp[name]['date'] = pd.to_datetime(df_comp[name]['date'])
    df_comp[name] = df_comp[name].rename(columns={'cum_users': f'cum_{name}'})

df = df_target.copy()
for name, df_c in df_comp.items():
    df = pd.merge(df, df_c[['date', f'cum_{name}']], on='date', how='inner')
df = df.sort_values('date').reset_index(drop=True)

# ============= 截取峰期窗口 =============
mask = (df['date'] >= START_DATE) & (df['date'] <= END_DATE)
df_peak = df[mask].reset_index(drop=True)

# ← 关键修改：窗口内累积归零
df_peak['cum_target'] = df_peak['new_developers'].cumsum()
for name in competitors:
    df_peak[f'cum_{name}'] = df_peak[f'cum_{name}'] - df_peak[f'cum_{name}'].iloc[0]

y        = df_peak['new_developers'].values.astype(float)
X_cum    = df_peak['cum_target'].values.astype(float)
comp_cum_list = [df_peak[f'cum_{name}'].values.astype(float) for name in competitors]
n_days   = len(y)
dt       = 1.0

# ============= MSB 残差函数 =============
def msb_residuals(params, y_obs, X_target_cum, comp_cum_list, dt, m_comp_list, n_obs):
    p1, q1, m1 = params[:3]
    gamma_list  = params[3:]
    residuals   = []
    X1 = 0.0
    for t in range(n_obs):
        self_term = (p1 + q1 * X1 / m1) * (m1 - X1) * dt
        comp_term = sum(gamma_list[j] * X1 * (m_comp_list[j] - comp_cum_list[j][t]) * dt
                        for j in range(len(gamma_list)))
        dX1 = max(self_term + comp_term, 0)
        residuals.append(y_obs[t] - dX1)
        X1 += dX1
    return np.array(residuals)

# ============= 参数统计函数 =============
def compute_param_stats(result, y_obs, param_names):
    n, k = len(y_obs), len(param_names)
    jac  = result.jac
    try:
        JtJ_inv = np.linalg.inv(jac.T @ jac)
        MSE     = result.cost / (n - k)
        pcov    = JtJ_inv * MSE
    except np.linalg.LinAlgError:
        return None
    se      = np.sqrt(np.diag(pcov))
    t_stats = result.x / se
    p_vals  = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=n - k))
    return {name: {'Estimate': result.x[i], 'Std.Error': se[i],
                   't_value': t_stats[i], 'p_value': p_vals[i]}
            for i, name in enumerate(param_names)}

# ============= 拟合函数 =============
def fit_and_report(y_obs, X_cum_obs, comp_cum_obs, n_obs):
    n_comp  = len(competitors)
    m_guess = X_cum_obs.max() * 1.2
    m_comp_est = [c.max() * 1.2 for c in comp_cum_obs]

    init   = [0.0005, 0.08, m_guess] + [0.00005] * n_comp
    lo     = [1e-6,   1e-3, X_cum_obs.max() * 1.05] + [-0.001] * n_comp
    hi     = [0.05,   0.5,  X_cum_obs.max() * 10]    + [ 0.001] * n_comp

    result = least_squares(
        msb_residuals, init,
        args=(y_obs, X_cum_obs, comp_cum_obs, dt, m_comp_est, n_obs),
        bounds=(lo, hi), method='trf', ftol=1e-8, xtol=1e-8, verbose=0)

    p1, q1, m1 = result.x[:3]
    gamma_list  = result.x[3:]

    print("\n" + "="*80)
    print("BTC Peak1 Fitting")
    print("="*80)
    print(f"p1={p1:.6f}, q1={q1:.6f}, m1={m1:,.0f}")
    for i, name in enumerate(competitors):
        print(f"γ_{name}: {gamma_list[i]:.6f}")

    param_names  = ['p1', 'q1', 'm1'] + [f'gamma_{n}' for n in competitors]
    param_stats  = compute_param_stats(result, y_obs, param_names)
    if param_stats:
        print("\nParameter Estimates:")
        print(pd.DataFrame(param_stats).T.to_string())

    # 生成拟合值
    fitted = np.zeros(n_obs)
    X1 = 0.0
    for t in range(n_obs):
        self_term = (p1 + q1 * X1 / m1) * (m1 - X1) * dt
        comp_term = sum(gamma_list[j] * X1 * (m_comp_est[j] - comp_cum_obs[j][t]) * dt
                        for j in range(n_comp))
        dX1 = max(self_term + comp_term, 0)
        fitted[t] = dX1
        X1 += dX1

    return result, fitted, param_stats

# ============= 指标函数 =============
def compute_metrics(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    error  = y_true - y_pred
    SSE    = np.sum(error**2)
    MSE    = SSE / len(y_true)
    RMSE   = np.sqrt(MSE)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    R2     = 1 - SSE / ss_tot if ss_tot != 0 else np.nan
    n, p   = len(y_true), 3 + len(competitors)
    Adj_R2 = 1 - (1 - R2) * (n - 1) / (n - p - 1) if n > p + 1 else np.nan
    y_safe = np.where(y_true == 0, 1e-10, y_true)
    WAPE   = np.sum(np.abs(error)) / np.sum(y_safe) * 100
    MAPE   = np.mean(np.abs(error / y_safe)) * 100
    return {"MAD": np.mean(np.abs(error)), "SSE": SSE, "MSE": MSE,
            "RMSE": RMSE, "R2": R2, "Adj_R2": Adj_R2, "MAPE": MAPE, "WAPE": WAPE}

# ============= 主程序 =============
if len(df_peak) > 3 + len(competitors):
    result_peak1, fitted_peak1, param_stats_peak1 = fit_and_report(
        y, X_cum, comp_cum_list, n_days)
    print("\nBTC Peak1 指标:")
    for k, v in compute_metrics(y, fitted_peak1).items():
        print(f"  {k}: {v:.4f}")
else:
    print("样本量不足，跳过拟合")
    fitted_peak1 = None

# ============= 绘图 =============
plt.figure(figsize=(12, 6))
plt.plot(df_peak['date'], y, label='Actual', color='blue', alpha=0.7)
if fitted_peak1 is not None:
    plt.plot(df_peak['date'], fitted_peak1, label='MSB Fitted (Peak1)',
             color='green', linewidth=2)
plt.xlabel('Date')
plt.ylabel('Daily New Developers')
plt.title('MSB Model Fit vs Actual (BTC Peak1)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_FIG, dpi=300)
plt.show()