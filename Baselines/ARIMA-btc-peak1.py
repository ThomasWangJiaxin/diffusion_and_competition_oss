# BTC Peak1 — Auto ARIMA Rolling Window Out-of-Sample Forecast
# 3 Rolling Periods, Full Window: 2017-01-01 ~ 2019-01-01
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
from pmdarima import auto_arima
import math

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 路径配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv"
OUTPUT_PNG = "btc_peak1_arima_rolling.png"
OUTPUT_CSV = "btc_peak1_arima_metrics.csv"
DATE_COL   = "date"
NEW_COL    = "new_developers"

FULL_START = "2017-01-01"
FULL_END   = "2019-01-01"

ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_start": "2017-01-01", "calib_end": "2017-06-30",
     "forecast_start": "2017-07-01", "forecast_end": "2019-01-01"},
    {"label": "2nd Rolling Period",
     "calib_start": "2017-01-01", "calib_end": "2017-12-31",
     "forecast_start": "2018-01-01", "forecast_end": "2019-01-01"},
    {"label": "3rd Rolling Period",
     "calib_start": "2017-01-01", "calib_end": "2018-06-30",
     "forecast_start": "2018-07-01", "forecast_end": "2019-01-01"},
]

# ============= 指标函数 =============
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
    wape   = (np.sum(np.abs(resid)) / np.sum(np.abs(y_true)) * 100
              if np.sum(np.abs(y_true)) > 0 else np.nan)
    return {"RMSE": rmse, "Adj_R2": adj_r2, "WAPE": wape}

# ============= 图表辅助 =============
def add_metrics_box(ax, metrics):
    txt = (f"RMSE = {metrics['RMSE']:.2f}\n"
           f"WAPE = {metrics['WAPE']:.2f}%")
    ax.text(0.98, 0.97, txt, transform=ax.transAxes,
            fontsize=8.5, va='top', ha='right', fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.3',
                      facecolor='white', alpha=0.85, edgecolor='gray'))

def format_ax(ax, dates_full, forecast_start, colors, show_legend=False):
    ax.axvline(x=forecast_start, color=colors['vline'], linewidth=0.9)
    ax.axvspan(dates_full[0],  forecast_start, alpha=0.05, color=colors['shade_c'])
    ax.axvspan(forecast_start, dates_full[-1],  alpha=0.05, color=colors['shade_f'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    if show_legend:
        ax.legend(fontsize=8.5, loc='upper left', framealpha=0.85, edgecolor='gray')

# ============= 主程序 =============
def main():
    df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    df_full = df_raw[[DATE_COL, NEW_COL]].copy().ffill().fillna(0)
    df_full = df_full[
        (df_full[DATE_COL] >= pd.to_datetime(FULL_START)) &
        (df_full[DATE_COL] <= pd.to_datetime(FULL_END))
    ].copy().reset_index(drop=True)

    dates_full = pd.to_datetime(df_full[DATE_COL].values)
    actual_dN  = df_full[NEW_COL].values.astype(float)

    colors = {
        'actual': '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':  '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 1, figsize=(12, 4 * n_rows))
    if n_rows == 1:
        axes = [axes]
    fig.suptitle('BTC Peak 1 — Auto ARIMA Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.to_datetime(period["calib_end"])
        forecast_start = pd.to_datetime(period["forecast_start"])
        label          = period["label"]

        mask_calib = dates_full <= calib_end
        mask_fc    = dates_full >= forecast_start
        mask_fit   = ~mask_fc

        y_calib = actual_dN[mask_calib]
        y_fc    = actual_dN[mask_fc]
        steps   = int(mask_fc.sum())

        print(f"\n→ 拟合 {label}  (calib: {period['calib_start']} ~ {period['calib_end']})")
        print(f"  校准样本量={len(y_calib)}, 预测步数={steps}")

        model = auto_arima(
            y_calib,
            start_p=0, max_p=5,
            start_q=0, max_q=5,
            d=None, seasonal=False,
            information_criterion='aic',
            stepwise=True,
            suppress_warnings=True,
            error_action='ignore'
        )
        order   = model.order
        y_pred  = model.predict(n_periods=steps)
        k_params = sum(order)

        metrics = compute_metrics(y_fc, y_pred, k=k_params)
        print(f"  ARIMA{order}  RMSE={metrics['RMSE']:.2f}  WAPE={metrics['WAPE']:.2f}%  Adj.R²={metrics['Adj_R2']:.4f}")

        all_metrics.append({
            "Period": label, "ARIMA_order": str(order),
            "RMSE": metrics['RMSE'], "WAPE": metrics['WAPE'], "Adj_R2": metrics['Adj_R2']
        })

        # 构造全窗口预测数组（校准期用实际值，预测期用预测值）
        dN_plot = np.full(len(dates_full), np.nan)
        dN_plot[mask_fc] = y_pred

        ax = axes[row_idx]
        ax.plot(dates_full, actual_dN,
                color=colors['actual'], linewidth=1.2, label='Actual')
        ax.plot(dates_full[mask_fc], y_pred,
                color=colors['forecast'], linewidth=1.3, linestyle='--', label='Forecast')
        ax.set_ylabel(f'{label}\nDaily New Developers', fontsize=10)
        format_ax(ax, dates_full, forecast_start, colors, show_legend=True)
        add_metrics_box(ax, metrics)

    axes[-1].set_xlabel('Date', fontsize=10)
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches='tight')
    print(f"\n✅ 图已保存: {OUTPUT_PNG}")

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(OUTPUT_CSV, index=False)
    print("\n===== 汇总指标 =====")
    print(metrics_df.round(4).to_string(index=False))
    plt.close()

if __name__ == "__main__":
    main()