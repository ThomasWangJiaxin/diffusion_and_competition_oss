import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import math
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pmdarima as pm

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 路径配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
OUTPUT_PNG = "eth_peak1_arimax_rolling.png"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
EXOG_COLS  = ["eth_price_lag1", "eth_p_event_sum_30", "eth_q_event_sum_7"]
FULL_START = "2017-01-01"
FULL_END   = "2019-01-01"
ROLLING_PERIODS = [
    {"label": "1st Rolling Period", "calib_end": "2017-06-30", "forecast_start": "2017-07-01"},
    {"label": "2nd Rolling Period", "calib_end": "2017-12-31", "forecast_start": "2018-01-01"},
    {"label": "3rd Rolling Period", "calib_end": "2018-06-30", "forecast_start": "2018-07-01"},
]

# ============= auto_arima 搜索范围 =============
P_MAX = 5
D_MAX = 2   # 差分阶数一般不超过 2
Q_MAX = 5

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
    # ── 读取数据 ──
    df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    cols_needed = [DATE_COL, NEW_COL, CUM_COL] + EXOG_COLS
    df_full = df_raw[cols_needed].copy()
    df_full = df_full.ffill().fillna(0)
    df_full = df_full[
        (df_full[DATE_COL] >= pd.to_datetime(FULL_START)) &
        (df_full[DATE_COL] <= pd.to_datetime(FULL_END))
    ].copy().reset_index(drop=True)

    # cum 归零（与其他模型一致）
    cum_offset       = df_full[CUM_COL].iloc[0] - df_full[NEW_COL].iloc[0]
    df_full[CUM_COL] = df_full[CUM_COL] - cum_offset

    dates_full = pd.to_datetime(df_full[DATE_COL].values)
    actual_dN  = df_full[NEW_COL].values.astype(float)
    actual_cum = df_full[CUM_COL].values.astype(float)
    exog_all   = df_full[EXOG_COLS].values.astype(float)  # (T, n_exog)
    n_full     = len(df_full)

    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 2, figsize=(14, 4 * n_rows))
    fig.suptitle('BTC Peak 1 — ARIMAX Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    col_titles = ['Daily New Developers (dN)', 'Cumulative Developers (Open-loop)']
    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=10, pad=8)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.Timestamp(period["calib_end"])
        forecast_start = pd.Timestamp(period["forecast_start"])
        label          = period["label"]

        mask_calib    = dates_full <= calib_end
        calib_end_idx = int(np.sum(mask_calib)) - 1
        mask_fc       = dates_full >= forecast_start
        mask_fit      = ~mask_fc
        n_forecast    = int(np.sum(mask_fc))

        if calib_end_idx < 10:
            print(f"  ❌ calib 期太短，跳过 {label}"); continue

        y_calib    = actual_dN[mask_calib]
        exog_calib = exog_all[mask_calib]
        exog_fc    = exog_all[mask_fc]   # 外生变量在预测期用真实值（外生，可观测）

        print(f"\n→ 拟合 {label}  (calib: {FULL_START} ~ {period['calib_end']},"
              f" n_calib={calib_end_idx+1}, n_forecast={n_forecast})")

        # ── auto_arima 自动搜索最优 (p,d,q) ──
        print(f"  auto_arima 搜索 p∈[0,{P_MAX}] d∈[0,{D_MAX}] q∈[0,{Q_MAX}] ...")
        try:
            auto_res = pm.auto_arima(
                y_calib,
                exogenous=exog_calib,
                start_p=0, max_p=P_MAX,
                d=None, max_d=D_MAX,      # d 自动用 ADF/KPSS 检验
                start_q=0, max_q=Q_MAX,
                seasonal=False,
                information_criterion='aic',
                stepwise=True,            # stepwise 加速搜索
                error_action='ignore',
                suppress_warnings=True,
            )
            order = auto_res.order
        except Exception as e:
            print(f"  ❌ auto_arima 失败: {e}"); continue

        print(f"  最优 ARIMA order: {order}")

        # ── 用选出的阶数重新用 SARIMAX 拟合（便于后续 get_forecast）──
        try:
            model = SARIMAX(
                endog=y_calib,
                exog=exog_calib,
                order=order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            result = model.fit(disp=False, maxiter=200)
        except Exception as e:
            print(f"  ❌ 拟合失败: {e}"); continue

        print(f"  AIC={result.aic:.2f}  BIC={result.bic:.2f}")

        # ── 拟合期：in-sample fitted values ──
        fitted_calib = np.asarray(result.fittedvalues)
        fitted_calib = np.maximum(fitted_calib, 0)

        # ── 预测期：多步外推（使用真实外生变量）──
        # SARIMAX.forecast() 做真正的 open-loop 多步预测
        try:
            fc_result = result.get_forecast(steps=n_forecast, exog=exog_fc)
            dN_fc     = np.maximum(np.asarray(fc_result.predicted_mean), 0)
        except Exception as e:
            print(f"  ❌ 预测失败: {e}"); continue

        # ── 拼接全窗口 dN_pred ──
        dN_pred = np.zeros(n_full)
        dN_pred[mask_calib] = fitted_calib
        dN_pred[mask_fc]    = dN_fc

        # ── 构建 cum_pred（拟合期展示真实值，预测期开环累积）──
        cum_pred = np.zeros(n_full)
        cum_pred[mask_calib] = actual_cum[mask_calib]   # 拟合期：真实 cum

        N_current = actual_cum[calib_end_idx]            # 从 calib 末端真实 cum 开始
        fc_indices = np.where(mask_fc)[0]
        for i in fc_indices:
            N_current += dN_pred[i]
            cum_pred[i] = N_current

        # ── 指标（仅 forecast 期）──
        m_dN  = compute_metrics(actual_dN[mask_fc],  dN_pred[mask_fc])
        m_cum = compute_metrics(actual_cum[mask_fc], cum_pred[mask_fc])

        print(f"  dN   RMSE={m_dN['RMSE']:.2f}  WAPE={m_dN['WAPE']:.2f}%  Adj.R²={m_dN['Adj_R2']:.4f}")
        print(f"  cum  RMSE={m_cum['RMSE']:.2f}  WAPE={m_cum['WAPE']:.2f}%  Adj.R²={m_cum['Adj_R2']:.4f}")

        all_metrics.append({
            "Period":   label,
            "dN_RMSE":  m_dN['RMSE'],  "dN_WAPE":  m_dN['WAPE'],  "dN_AdjR2":  m_dN['Adj_R2'],
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

    if all_metrics:
        metrics_df = pd.DataFrame(all_metrics)
        print("\n===== 汇总指标 =====")
        print(metrics_df.round(4).to_string(index=False))

    plt.close()

if __name__ == "__main__":
    main()