# ============================================================
# ETH Peak 2 — LSTM Rolling Window Out-of-Sample Forecast
# 4 Rolling Periods, Full Window: 2020-10-01 ~ 2023-01-01
# ============================================================
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
from sklearn.preprocessing import MinMaxScaler
import math

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
OUTPUT_PNG = "eth_peak2_lstm_rolling.png"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"

FULL_START = "2020-10-01"
FULL_END   = "2023-01-01"
SEQ_LEN    = 30  # seq len ∈ {7, 14, 21, 30}
EPOCHS     = 20

ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2021-03-31", "forecast_start": "2021-04-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2021-09-30", "forecast_start": "2021-10-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2022-03-31", "forecast_start": "2022-04-01"},
    {"label": "4th Rolling Period",
     "calib_end": "2022-09-30", "forecast_start": "2022-10-01"},
]

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc   = nn.Linear(hidden_size, 1)
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

def create_sequences(data, seq_len):
    xs, ys = [], []
    for i in range(len(data) - seq_len):
        xs.append(data[i:i+seq_len])
        ys.append(data[i+seq_len])
    return np.array(xs), np.array(ys)

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

def train_lstm(calib_values, seq_len, epochs):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(calib_values.reshape(-1, 1))
    X, y   = create_sequences(scaled, seq_len)
    X_t    = torch.tensor(X, dtype=torch.float32)
    y_t    = torch.tensor(y, dtype=torch.float32)
    model     = LSTMModel()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(X_t), y_t)
        loss.backward()
        optimizer.step()
    return model, scaler

def forecast_open(model, scaler, calib_values, forecast_len, seq_len):
    scaled_calib = scaler.transform(calib_values.reshape(-1, 1)).flatten()
    window = list(scaled_calib[-seq_len:])
    preds  = []
    model.eval()
    with torch.no_grad():
        for _ in range(forecast_len):
            x_in = torch.tensor(
                np.array(window[-seq_len:]).reshape(1, seq_len, 1),
                dtype=torch.float32)
            pred = model(x_in).item()
            preds.append(pred)
            window.append(pred)
    return scaler.inverse_transform(
        np.array(preds).reshape(-1, 1)).flatten()

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

def main():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = df[[DATE_COL, NEW_COL]].ffill().fillna(0)
    df = df[
        (df[DATE_COL] >= pd.to_datetime(FULL_START)) &
        (df[DATE_COL] <= pd.to_datetime(FULL_END))
    ].copy().reset_index(drop=True)

    dates_full = pd.to_datetime(df[DATE_COL].values)
    actual_dN  = df[NEW_COL].values.astype(float)

    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 1, figsize=(12, 4 * n_rows))
    fig.suptitle('ETH Peak 2 — LSTM Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)

    all_metrics = []

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.to_datetime(period["calib_end"])
        forecast_start = pd.to_datetime(period["forecast_start"])
        label          = period["label"]

        mask_calib   = dates_full <= calib_end
        calib_vals   = actual_dN[mask_calib]
        mask_fc      = dates_full >= forecast_start
        fc_actual    = actual_dN[mask_fc]
        forecast_len = int(mask_fc.sum())

        print(f"\n→ 训练 {label}  (calib: {FULL_START} ~ {period['calib_end']})")
        model, scaler = train_lstm(calib_vals, SEQ_LEN, EPOCHS)
        fc_pred = forecast_open(model, scaler, calib_vals, forecast_len, SEQ_LEN)

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