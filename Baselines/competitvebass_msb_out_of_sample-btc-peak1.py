# ============================================================
# BTC Peak 1 — Competitive Bass (MSB) Rolling Window OOS Forecast
# 3 Rolling Periods, Full Window: 2017-01-01 ~ 2019-01-01
# ============================================================
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
from scipy.optimize import least_squares
from scipy.stats import t as t_dist
import math

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 路径配置 =============
OUTPUT_PNG = "btc_peak1_msb_rolling.png"

FULL_START = "2017-01-01"
FULL_END   = "2019-01-01"

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

# BTC Peak 1: 3 Rolling Periods
ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2017-06-30", "forecast_start": "2017-07-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2017-12-31", "forecast_start": "2018-01-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2018-06-30", "forecast_start": "2018-07-01"},
]

dt = 1.0

# ============= 读取 & 合并数据 =============
def load_data():
    df_target = pd.read_csv(target_path)[['date', 'new_developers', 'cum_users']]
    df_target['date'] = pd.to_datetime(df_target['date'])
    df_target = df_target.rename(columns={'cum_users': 'cum_target'})

    df = df_target.copy()
    for name, path in competitors.items():
        df_c = pd.read_csv(path)[['date', 'cum_users']]
        df_c['date'] = pd.to_datetime(df_c['date'])
        df_c = df_c.rename(columns={'cum_users': f'cum_{name}'})
        # ← left join，竞争对手数据不足时填 0
        df = pd.merge(df, df_c, on='date', how='left')
        df[f'cum_{name}'] = df[f'cum_{name}'].fillna(0)

    df = df.sort_values('date').reset_index(drop=True)
    mask = (df['date'] >= pd.to_datetime(FULL_START)) & \
           (df['date'] <= pd.to_datetime(FULL_END))
    df_full = df[mask].reset_index(drop=True)
    print(f"df_full after window filter: {len(df_full)} rows, "
          f"{df_full['date'].min()} ~ {df_full['date'].max()}")

    df_full['cum_target'] = df_full['new_developers'].cumsum()
    for name in competitors:
        df_full[f'cum_{name}'] = (df_full[f'cum_{name}']
                                   - df_full[f'cum_{name}'].iloc[0])
    return df_full

# ============= MSB 残差函数（拟合期用）=============
def msb_residuals(params, y_obs, comp_cum_list, m_comp_list, n_obs):
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

# ============= 拟合函数 =============
def fit_msb(y_calib, comp_cum_calib, cum_max_calib):
    """
    在 calibration 窗口上拟合 MSB 模型。
    comp_cum_calib: list of arrays，每个竞争对手在 calib 期的 cum
    cum_max_calib:  target 在 calib 期末的累积值，用于约束 m1 下界
    """
    n_comp     = len(competitors)
    n_obs      = len(y_calib)
    m_comp_est = [c[-1] * 1.2 for c in comp_cum_calib]
    m_guess    = cum_max_calib * 1.2

    init = [0.0005, 0.08, m_guess] + [0.00005] * n_comp
    lo   = [1e-6,   1e-3, cum_max_calib * 1.05] + [-0.001] * n_comp
    hi   = [0.05,   0.5,  cum_max_calib * 10]    + [ 0.001] * n_comp

    try:
        result = least_squares(
            msb_residuals, init,
            args=(y_calib, comp_cum_calib, m_comp_est, n_obs),
            bounds=(lo, hi), method='trf', ftol=1e-8, xtol=1e-8, verbose=0
        )
        if not result.success and result.cost > 1e10:
            return None, None
        return result, m_comp_est
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None, None

# ============= Open-loop 全窗口预测 =============
def forecast_open(result, m_comp_est, comp_cum_full, n_full,
                  calib_mask, actual_cum):
    """
    用 calib 期估计的参数，在整个全窗口上做 open-loop 递推：
    - 拟合期：照常递推，但 cum 展示用真实值（与 Gompertz/Logistic 版一致）
    - 预测期：继续递推，X1 从 calib 末端真实 cum 开始
    注意：MSB 的 dN 依赖 X1（上一步累积），因此拟合期也是递推的。
          为保持与其他模型图表的一致性，拟合期 cum 展示真实值，
          但预测期 cum 完全开环。
    """
    p1, q1, m1 = result.x[:3]
    gamma_list  = result.x[3:]
    n_comp      = len(competitors)

    dN_pred  = np.zeros(n_full)
    cum_pred = np.zeros(n_full)

    # 预测期起点：calib 末端的真实 cum 值
    X1 = float(actual_cum[calib_mask][-1])

    # calib 末端的 index（用于切换 open-loop 起点）
    calib_end_idx = int(np.sum(calib_mask)) - 1

    for i in range(n_full):
        comp_cum_i = [comp_cum_full[j][i] for j in range(n_comp)]
        self_term  = (p1 + q1 * X1 / m1) * (m1 - X1) * dt
        comp_term  = sum(gamma_list[j] * X1 * (m_comp_est[j] - comp_cum_i[j]) * dt
                         for j in range(n_comp))
        dX1 = max(self_term + comp_term, 0)
        dN_pred[i] = dX1

        if i <= calib_end_idx:
            # 拟合期：cum 展示真实值，X1 用真实 cum 更新（闭环展示）
            cum_pred[i] = actual_cum[i]
            X1 = float(actual_cum[i])
        else:
            # 预测期：开环累积
            X1 += dX1
            cum_pred[i] = X1

    return dN_pred, cum_pred

# ============= 评估指标 =============
def compute_metrics(y_true, y_pred, k=None):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    n      = len(y_true)
    if k is None:
        k = 3 + len(competitors)
    resid  = y_true - y_pred
    sse    = np.sum(resid ** 2)
    rmse   = math.sqrt(sse / n)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
              if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
    wape   = np.sum(np.abs(resid)) / np.sum(np.abs(y_true)) * 100 \
             if np.sum(np.abs(y_true)) > 0 else np.nan
    return {"RMSE": rmse, "Adj_R2": adj_r2, "WAPE": wape}

# ============= 图表辅助 =============
def add_metrics_box(ax, metrics, loc='upper right'):
    txt = (f"RMSE = {metrics['RMSE']:.2f}\n"
           f"WAPE = {metrics['WAPE']:.2f}%")
    x  = 0.98 if 'right' in loc else 0.02
    ha = 'right' if 'right' in loc else 'left'
    ax.text(x, 0.97, txt, transform=ax.transAxes,
            fontsize=8.5, va='top', ha=ha, fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.3',
                      facecolor='white', alpha=0.85, edgecolor='gray'))

def format_ax(ax, dates_full, forecast_start, colors,
              show_legend=False, legend_loc='upper left'):
    ax.axvline(x=forecast_start, color=colors['vline'], linewidth=0.9)
    ax.axvspan(dates_full[0],  forecast_start, alpha=0.05, color=colors['shade_c'])
    ax.axvspan(forecast_start, dates_full[-1],  alpha=0.05, color=colors['shade_f'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    if show_legend:
        ax.legend(fontsize=8.5, loc=legend_loc, framealpha=0.85, edgecolor='gray')

# ============= 主程序 =============
def main():
    print("读取数据...")
    df_full = load_data()

    dates_full = pd.to_datetime(df_full['date'].values)
    actual_dN  = df_full['new_developers'].values.astype(float)
    actual_cum = df_full['cum_target'].values.astype(float)
    
    dates_full = pd.to_datetime(df_full['date'].values)
    actual_dN  = df_full['new_developers'].values.astype(float)
    actual_cum = df_full['cum_target'].values.astype(float)

    # ← 加这一行，去除时区信息
    dates_full = dates_full.tz_localize(None) if dates_full.tz is not None else dates_full

    # 全窗口各竞争对手 cum（list of arrays）
    comp_cum_full = [df_full[f'cum_{name}'].values.astype(float)
                     for name in competitors]

    n_full = len(df_full)
    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 2, figsize=(14, 4 * n_rows))
    fig.suptitle('BTC Peak 1 — Competitive Bass (MSB) Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    col_titles = ['Daily New Developers (dN)', 'Cumulative Developers (Open-loop)']
    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=10, pad=8)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.Timestamp(period["calib_end"])
        forecast_start = pd.Timestamp(period["forecast_start"])
        label          = period["label"]

        mask_calib = dates_full <= calib_end

        y_calib         = actual_dN[mask_calib]
        comp_cum_calib  = [c[mask_calib] for c in comp_cum_full]
        cum_max_calib   = actual_cum[mask_calib][-1]

        print(f"\n→ 拟合 {label}  (calib: {FULL_START} ~ {period['calib_end']})")
        print(f"  cum_max_calib = {cum_max_calib:.0f},  n_calib = {int(np.sum(mask_calib))}")

        result, m_comp_est = fit_msb(y_calib, comp_cum_calib, cum_max_calib)
        if result is None:
            print(f"  ❌ 拟合失败，跳过"); continue

        p1, q1, m1 = result.x[:3]
        print(f"  p1={p1:.6f}  q1={q1:.6f}  m1={m1:,.0f}")

        dN_pred, cum_pred = forecast_open(
            result, m_comp_est, comp_cum_full, n_full,
            mask_calib, actual_cum
        )

        mask_fc  = dates_full >= forecast_start
        mask_fit = ~mask_fc
        m_dN  = compute_metrics(actual_dN[mask_fc],  dN_pred[mask_fc])
        m_cum = compute_metrics(actual_cum[mask_fc], cum_pred[mask_fc])

        print(f"  dN   RMSE={m_dN['RMSE']:.2f}  WAPE={m_dN['WAPE']:.2f}%  Adj.R²={m_dN['Adj_R2']:.4f}")
        print(f"  cum  RMSE={m_cum['RMSE']:.2f}  WAPE={m_cum['WAPE']:.2f}%  Adj.R²={m_cum['Adj_R2']:.4f}")

        all_metrics.append({
            "Period":    label,
            "dN_RMSE":   m_dN['RMSE'],  "dN_WAPE":   m_dN['WAPE'],  "dN_AdjR2":   m_dN['Adj_R2'],
            "cum_RMSE":  m_cum['RMSE'], "cum_WAPE":  m_cum['WAPE'], "cum_AdjR2":  m_cum['Adj_R2'],
        })

        for col_idx, (actual_arr, pred_arr, metrics) in enumerate([
            (actual_dN,  dN_pred,  m_dN),
            (actual_cum, cum_pred, m_cum),
        ]):
            ax = axes[row_idx, col_idx]
            ax.plot(dates_full, actual_arr,
                    color=colors['actual'], linewidth=1.2, label='Actual')
            ax.plot(dates_full[mask_fit], pred_arr[mask_fit],
                    color=colors['calib'], linewidth=1.3, linestyle='-', label='Fitted')
            ax.plot(dates_full[mask_fc],  pred_arr[mask_fc],
                    color=colors['forecast'], linewidth=1.3, linestyle='--', label='Forecast')

            ylabel = 'Daily New Developers' if col_idx == 0 else 'Cumulative Developers'
            ax.set_ylabel(f'{label}\n{ylabel}', fontsize=10)
            format_ax(ax, dates_full, forecast_start, colors,
                      show_legend=True, legend_loc='upper left')
            if col_idx == 0:
                add_metrics_box(ax, metrics, loc='upper right')

    for col in range(2):
        axes[n_rows - 1, col].set_xlabel('Date', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches='tight')
    print(f"\n✅ 图已保存: {OUTPUT_PNG}")

    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        print("\n===== 汇总指标 =====")
        print(metrics_df.round(4).to_string(index=False))

    plt.close()

if __name__ == "__main__":
    main()