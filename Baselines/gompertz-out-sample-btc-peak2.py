# ============================================================
# BTC Peak 2 — Gompertz Rolling Window Out-of-Sample Forecast
# 3 Rolling Periods, Full Window: 2020-10-01 ~ 2022-10-01
# ============================================================
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
from scipy.optimize import curve_fit
from scipy import stats
import math

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 路径配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv"
OUTPUT_PNG = "btc_peak2_gompertz_rolling.png"

DATE_COL = "date"
NEW_COL  = "new_developers"
CUM_COL  = "cum_users"

FULL_START = "2020-10-01"
FULL_END   = "2022-10-01"

ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2021-03-31", "forecast_start": "2021-04-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2021-09-30", "forecast_start": "2021-10-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2022-03-31", "forecast_start": "2022-04-01"},
]

# ============= Gompertz 模型 =============
def gompertz_pdf(t, K, b, t0):
    return K * b * np.exp(-b * (t - t0)) * np.exp(-np.exp(-b * (t - t0)))

def gompertz_cdf(t, K, b, t0):
    return K * np.exp(-np.exp(-b * (t - t0)))

# ============= 拟合函数 =============
def fit_gompertz(t_arr, y_arr, cum_window):
    K0   = cum_window * 1.2
    b0   = 0.01
    t0_0 = np.median(t_arr)
    try:
        popt, pcov = curve_fit(
            gompertz_pdf, t_arr, y_arr,
            p0=[K0, b0, t0_0],
            bounds=(
                [cum_window * 1.05, 0.001, t_arr.min() - 365 * 2],
                [cum_window * 10.0, 1.0,   t_arr.max() + 365 * 2]
            ),
            maxfev=20000
        )
        se      = np.sqrt(np.diag(pcov))
        t_stats = popt / (se + 1e-12)
        dfree   = len(t_arr) - len(popt)
        pvals   = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=dfree))
        param_table = pd.DataFrame({
            "param":     ["K", "b", "t0"],
            "estimate":  popt,
            "std_error": se,
            "t_value":   t_stats,
            "p_value":   pvals
        })
        return popt, param_table
    except Exception as e:
        print(f"  拟合失败: {e}")
        return None, None

# ============= 评估指标 =============
def compute_metrics(y_true, y_pred, k=3):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    n      = len(y_true)
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

# ============= Open-loop 预测 =============
def forecast_open(dates_full, t_full, popt, calib_end, N_lag_calib_end, actual_cum, actual_dN):
    n = len(t_full)
    dN_pred  = np.zeros(n)
    cum_pred = np.zeros(n)
    N_current = N_lag_calib_end

    for i in range(n):
        dN_i = max(gompertz_pdf(t_full[i], *popt), 0)
        dN_pred[i] = dN_i
        if dates_full[i] <= calib_end:
            cum_pred[i] = actual_cum[i]
        else:
            N_current  += dN_i
            cum_pred[i] = N_current

    return dN_pred, cum_pred

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
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    if show_legend:
        ax.legend(fontsize=8.5, loc=legend_loc, framealpha=0.85, edgecolor='gray')

# ============= 主程序 =============
def main():
    df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    df_full = df_raw[[DATE_COL, NEW_COL, CUM_COL]].copy()
    df_full = df_full.ffill().fillna(0)
    df_full = df_full[
        (df_full[DATE_COL] >= pd.to_datetime(FULL_START)) &
        (df_full[DATE_COL] <= pd.to_datetime(FULL_END))
    ].copy().reset_index(drop=True)

    cum_offset       = df_full[CUM_COL].iloc[0] - df_full[NEW_COL].iloc[0]
    df_full[CUM_COL] = df_full[CUM_COL] - cum_offset

    dates_full = pd.to_datetime(df_full[DATE_COL].values)
    actual_dN  = df_full[NEW_COL].values.astype(float)
    actual_cum = df_full[CUM_COL].values.astype(float)
    
    t_full = (dates_full - dates_full[0]).days.astype(float)

    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 2, figsize=(14, 4 * n_rows))
    fig.suptitle('BTC Peak 2 — Gompertz Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    col_titles = ['Daily New Developers (dN)', 'Cumulative Developers (Open-loop)']
    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=10, pad=8)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.to_datetime(period["calib_end"])
        forecast_start = pd.to_datetime(period["forecast_start"])
        label          = period["label"]

        mask_calib = dates_full <= calib_end
        t_calib    = t_full[mask_calib]
        y_calib    = actual_dN[mask_calib]
        cum_window = actual_cum[mask_calib][-1] - actual_cum[mask_calib][0]

        print(f"\n→ 拟合 {label}  (calib: {FULL_START} ~ {period['calib_end']})")
        print(f"  cum_window = {cum_window:.0f}")

        popt, param_table = fit_gompertz(t_calib, y_calib, cum_window)
        if popt is None:
            print(f"  ❌ 拟合失败，跳过"); continue

        print(param_table.round(6))

        N_lag_calib_end = actual_cum[mask_calib][-1]
        dN_pred, cum_pred = forecast_open(
            dates_full, t_full, popt, calib_end,
            N_lag_calib_end, actual_cum, actual_dN
        )

        mask_fc  = dates_full >= forecast_start
        mask_fit = ~mask_fc
        m_dN  = compute_metrics(actual_dN[mask_fc],  dN_pred[mask_fc])
        m_cum = compute_metrics(actual_cum[mask_fc], cum_pred[mask_fc])

        print(f"  dN   RMSE={m_dN['RMSE']:.2f}  WAPE={m_dN['WAPE']:.2f}%  Adj.R²={m_dN['Adj_R2']:.4f}")
        print(f"  cum  RMSE={m_cum['RMSE']:.2f}  WAPE={m_cum['WAPE']:.2f}%  Adj.R²={m_cum['Adj_R2']:.4f}")

        all_metrics.append({
            "Period": label,
            "dN_RMSE": m_dN['RMSE'], "dN_WAPE": m_dN['WAPE'], "dN_AdjR2": m_dN['Adj_R2'],
            "cum_RMSE": m_cum['RMSE'], "cum_WAPE": m_cum['WAPE'], "cum_AdjR2": m_cum['Adj_R2'],
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

    metrics_df = pd.DataFrame(all_metrics)
    print("\n===== 汇总指标 =====")
    print(metrics_df.round(4).to_string(index=False))
    plt.close()

if __name__ == "__main__":
    main()