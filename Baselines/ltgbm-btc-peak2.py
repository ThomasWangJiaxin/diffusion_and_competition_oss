import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
OUTPUT_PNG = "btc_peak2_lightgbm_rolling.png"
DATE_COL   = "date"
NEW_COL    = "btc_new_developers"
EXOG_COLS  = ["btc_price_lag1", "btc_p_event_sum_7", "btc_q_event_sum_30"]

FULL_START = "2020-10-01"
FULL_END   = "2022-10-01"
SEQ_LEN    = 30
N_FEATURES = 1 + len(EXOG_COLS)  # target + exog

ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2021-03-31", "forecast_start": "2021-04-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2021-09-30", "forecast_start": "2021-10-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2022-03-31", "forecast_start": "2022-04-01"},
]

# ============= 序列构造 =============
def create_sequences(data, seq_len):
    xs, ys = [], []
    for i in range(len(data) - seq_len):
        xs.append(data[i:i+seq_len].flatten())
        ys.append(data[i+seq_len, 0])
    return np.array(xs), np.array(ys)

# ============= 评估指标 =============
def compute_metrics(y_true, y_pred, k=SEQ_LEN):
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

# ============= 训练函数 =============
def train_model(calib_data, seq_len):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(calib_data)
    X, y   = create_sequences(scaled, seq_len)
    split  = int(len(X) * 0.8)
    params = {
        'objective':       'regression',
        'metric':          'rmse',
        'learning_rate':   0.05,
        'num_leaves':      31,
        'max_depth':       4,
        'subsample':       0.8,
        'colsample_bytree':0.8,
        'n_estimators':    500,
        'verbose':         -1,
        'random_state':    42,
    }
    model = lgb.LGBMRegressor(**params)
    model.fit(
        X[:split], y[:split],
        eval_set=[(X[split:], y[split:])],
        callbacks=[lgb.early_stopping(20, verbose=False),
                   lgb.log_evaluation(period=-1)]
    )
    return model, scaler

# ============= Open-loop 预测 =============
def forecast_open(model, scaler, calib_data, fc_exog, seq_len):
    scaled_calib = scaler.transform(calib_data)
    window       = list(scaled_calib[-seq_len:])
    dummy        = np.zeros((len(fc_exog), calib_data.shape[1]))
    dummy[:, 1:] = fc_exog
    scaled_exog  = scaler.transform(dummy)[:, 1:]
    preds = []
    for i in range(len(fc_exog)):
        x_in = np.array(window[-seq_len:]).flatten().reshape(1, -1)
        pred = model.predict(x_in)[0]
        preds.append(pred)
        window.append(np.concatenate([[pred], scaled_exog[i]]))
    dummy_pred       = np.zeros((len(preds), calib_data.shape[1]))
    dummy_pred[:, 0] = preds
    return scaler.inverse_transform(dummy_pred)[:, 0]

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
        ax.legend(fontsize=8.5, loc='upper left',
                  framealpha=0.85, edgecolor='gray')

# ============= 主程序 =============
def main():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = df[[DATE_COL, NEW_COL] + EXOG_COLS].ffill().fillna(0)
    df = df[
        (df[DATE_COL] >= pd.to_datetime(FULL_START)) &
        (df[DATE_COL] <= pd.to_datetime(FULL_END))
    ].copy().reset_index(drop=True)

    dates_full = pd.to_datetime(df[DATE_COL].values)
    actual_dN  = df[NEW_COL].values.astype(float)
    all_data   = df[[NEW_COL] + EXOG_COLS].values.astype(float)

    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 1, figsize=(12, 4 * n_rows))
    fig.suptitle('BTC Peak 2 — LightGBM Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.to_datetime(period["calib_end"])
        forecast_start = pd.to_datetime(period["forecast_start"])
        label          = period["label"]

        mask_calib = dates_full <= calib_end
        mask_fc    = dates_full >= forecast_start
        calib_data = all_data[mask_calib]
        fc_exog    = all_data[mask_fc][:, 1:]
        fc_actual  = actual_dN[mask_fc]

        print(f"\n→ 训练 {label}  (calib: {FULL_START} ~ {period['calib_end']})")
        model, scaler = train_model(calib_data, SEQ_LEN)
        fc_pred = forecast_open(model, scaler, calib_data, fc_exog, SEQ_LEN)

        metrics = compute_metrics(fc_actual, fc_pred)
        print(f"  RMSE={metrics['RMSE']:.2f}  WAPE={metrics['WAPE']:.2f}%  Adj.R²={metrics['Adj_R2']:.4f}")
        all_metrics.append({"Period": label, **metrics})

        ax = axes[row_idx]
        mask_fit = ~mask_fc
        ax.plot(dates_full, actual_dN,
                color=colors['actual'], linewidth=1.2, label='Actual')
        ax.plot(dates_full[mask_fit], actual_dN[mask_fit],
                color=colors['calib'], linewidth=1.3, linestyle='-', label='Calibration')
        ax.plot(dates_full[mask_fc], fc_pred,
                color=colors['forecast'], linewidth=1.3, linestyle='--', label='Forecast')
        ax.set_ylabel(f'{label}\nDaily New Developers', fontsize=10)
        format_ax(ax, dates_full, forecast_start, colors, show_legend=True)
        add_metrics_box(ax, metrics)

    axes[-1].set_xlabel('Date', fontsize=10)
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches='tight')
    print(f"\n✅ 图已保存: {OUTPUT_PNG}")
    print("\n===== 汇总指标 =====")
    print(pd.DataFrame(all_metrics).round(4).to_string(index=False))
    plt.close()

if __name__ == "__main__":
    main()