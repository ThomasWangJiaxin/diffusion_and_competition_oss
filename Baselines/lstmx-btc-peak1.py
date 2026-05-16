# ============================================================
# BTC Peak 1 — Multivariate LSTM Rolling Window OOS Forecast
# 3 Rolling Periods, Full Window: 2017-01-01 ~ 2019-01-01
# Features: btc_new_developers, btc_ma_21d,
#           btc_p_event_sum_21, btc_q_event_sum_7
# 评估框架与 Gompertz / Logistic / MSB 完全对齐
# ============================================================
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import math

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 路径配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
OUTPUT_PNG = "btc_peak1_lstm_rolling.png"

DATE_COL = "date"
NEW_COL  = "btc_new_developers"
CUM_COL  = "btc_cum_users"

# 外部特征列（与 NEW_COL 一起组成多变量输入）
FEATURE_COLS = [
    "btc_new_developers",    # 目标变量自身（index 0）
    "btc_ma_7d",             # 价格 MA
    "btc_p_event_sum_14",    # p 事件特征
    "btc_q_event_sum_7",     # q 事件特征
]
TARGET_IDX = 0               # FEATURE_COLS 中目标变量的位置

FULL_START = "2017-01-01"
FULL_END   = "2019-01-01"

ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2017-06-30", "forecast_start": "2017-07-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2017-12-31", "forecast_start": "2018-01-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2018-06-30", "forecast_start": "2018-07-01"},
]

# ============= LSTM 超参数 =============
LOOKBACK   = 30       # 用过去 30 天预测下一天
HIDDEN_DIM = 64    # {32,64,128}
NUM_LAYERS = 2     # {1,2,3}
DROPOUT    = 0.2
EPOCHS     = 200
BATCH_SIZE = 32
LR         = 1e-3
PATIENCE   = 20       # early stopping

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============= LSTM 模型定义 =============
class MultivariateLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze(-1)

# ============= 滑窗构建 =============
def build_sequences(data_scaled, lookback):
    """
    data_scaled: (T, n_features) numpy array，已归一化
    返回 X: (N, lookback, n_features), y: (N,)  目标为第 TARGET_IDX 列
    """
    X, y = [], []
    for i in range(lookback, len(data_scaled)):
        X.append(data_scaled[i - lookback: i, :])
        y.append(data_scaled[i, TARGET_IDX])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

# ============= 训练函数 =============
def train_lstm(X_train, y_train, input_dim):
    model = MultivariateLSTM(input_dim, HIDDEN_DIM, NUM_LAYERS, DROPOUT).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    # 90/10 train/val split for early stopping
    val_size  = max(1, int(len(X_train) * 0.1))
    X_val_t   = torch.tensor(X_train[-val_size:]).to(DEVICE)
    y_val_t   = torch.tensor(y_train[-val_size:]).to(DEVICE)
    X_tr_t    = torch.tensor(X_train[:-val_size]).to(DEVICE)
    y_tr_t    = torch.tensor(y_train[:-val_size]).to(DEVICE)

    dataset   = TensorDataset(X_tr_t, y_tr_t)
    loader    = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    best_val_loss = float('inf')
    best_state    = None
    patience_cnt  = 0

    for epoch in range(EPOCHS):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val_t), y_val_t).item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state    = {k: v.clone() for k, v in model.state_dict().items()}
            patience_cnt  = 0
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                break

    model.load_state_dict(best_state)
    return model

# ============= Open-loop 预测 =============
def forecast_open(model, scaler, data_scaled, calib_end_idx,
                  actual_cum, actual_dN, n_full):
    """
    拟合期（calib）：用真实滑窗做 one-step-ahead 预测（闭环展示）
    预测期（forecast）：用预测值替换滑窗中的目标列，开环递推

    scaler: 仅对 TARGET_IDX 列反归一化
    """
    model.eval()
    n_features = data_scaled.shape[1]

    dN_pred  = np.zeros(n_full)
    cum_pred = np.zeros(n_full)

    # 滑窗缓存（用真实数据初始化）
    window = data_scaled[:LOOKBACK].copy()   # (LOOKBACK, n_features)
    N_current = actual_cum[calib_end_idx]    # 预测期起点 cum

    for i in range(LOOKBACK, n_full):
        x_in = torch.tensor(window[np.newaxis], dtype=torch.float32).to(DEVICE)
        with torch.no_grad():
            pred_scaled = model(x_in).item()

        # 反归一化：只反变换目标列
        dummy = np.zeros((1, n_features))
        dummy[0, TARGET_IDX] = pred_scaled
        pred_dN = float(scaler.inverse_transform(dummy)[0, TARGET_IDX])
        pred_dN = max(pred_dN, 0)

        dN_pred[i] = pred_dN

        if i <= calib_end_idx:
            # 拟合期：cum 展示真实值
            cum_pred[i] = actual_cum[i]
            # 下一步滑窗用真实数据
            window = data_scaled[i - LOOKBACK + 1: i + 1].copy()
        else:
            # 预测期：开环累积 cum
            N_current += pred_dN
            cum_pred[i] = N_current
            # 下一步滑窗：目标列替换为预测值，其他特征用真实值
            new_row = data_scaled[i].copy()
            new_row[TARGET_IDX] = pred_scaled
            window = np.vstack([window[1:], new_row[np.newaxis]])

    # 前 LOOKBACK 天没有预测（补 0）
    for i in range(LOOKBACK):
        dN_pred[i]  = actual_dN[i]
        cum_pred[i] = actual_cum[i]

    return dN_pred, cum_pred

# ============= 评估指标 =============
def compute_metrics(y_true, y_pred, k=4):
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
    print(f"Using device: {DEVICE}")

    # ── 读取数据 ──
    df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    df_full = df_raw[[DATE_COL, NEW_COL, CUM_COL] +
                     [c for c in FEATURE_COLS if c != NEW_COL]].copy()
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
    n_full     = len(df_full)

    # 特征矩阵（全窗口，用于归一化和预测期滑窗）
    data_all = df_full[FEATURE_COLS].values.astype(float)  # (T, n_features)

    colors = {
        'actual':  '#2c2c2c', 'calib': '#2166ac', 'forecast': '#d6604d',
        'vline':   '#666666', 'shade_c': '#d6eaf8', 'shade_f': '#fde8e4'
    }

    n_rows = len(ROLLING_PERIODS)
    fig, axes = plt.subplots(n_rows, 2, figsize=(14, 4 * n_rows))
    fig.suptitle('BTC Peak 1 — Multivariate LSTM Out-of-Sample Forecasting (Rolling Windows)',
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

        if calib_end_idx < LOOKBACK:
            print(f"  ❌ calib 期太短（{calib_end_idx+1} 天 < LOOKBACK={LOOKBACK}），跳过 {label}")
            continue

        print(f"\n→ 训练 {label}  (calib: {FULL_START} ~ {period['calib_end']},"
              f" n={calib_end_idx+1})")

        # ── 仅用 calib 期数据拟合 scaler（防止信息泄露）──
        data_calib = data_all[: calib_end_idx + 1]          # (calib_len, n_features)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaler.fit(data_calib)

        # ── 归一化全窗口（用 calib 期的 scaler）──
        data_scaled = scaler.transform(data_all)             # (T, n_features)

        # ── 构建 calib 期训练序列 ──
        data_calib_scaled = data_scaled[: calib_end_idx + 1]
        X_train, y_train  = build_sequences(data_calib_scaled, LOOKBACK)

        if len(X_train) == 0:
            print(f"  ❌ 训练序列为空，跳过"); continue

        print(f"  训练样本数: {len(X_train)}")

        # ── 训练 LSTM ──
        input_dim = len(FEATURE_COLS)
        model = train_lstm(X_train, y_train, input_dim)
        print(f"  训练完成")

        # ── 全窗口 open-loop 预测 ──
        dN_pred, cum_pred = forecast_open(
            model, scaler, data_scaled,
            calib_end_idx, actual_cum, actual_dN, n_full
        )

        mask_fc  = dates_full >= forecast_start
        mask_fit = ~mask_fc
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

# LSTM加外部特征-BTC
# import pandas as pd
# import numpy as np
# import torch
# import torch.nn as nn
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import r2_score

# # =========================
# # 1. 读取数据
# # =========================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"

# df = pd.read_csv(file_path)
# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# # 使用的特征
# feature_cols = ['btc_new_developers', 'btc_price_lag1', 'btc_p_event', 'btc_q_event']
# target_col = 'btc_new_developers'

# series = df[['date'] + feature_cols].dropna()

# # =========================
# # 2. 时间划分
# # =========================
# peak1_start = pd.Timestamp("2017-01-01")
# peak1_end   = pd.Timestamp("2019-01-01")

# peak2_start = pd.Timestamp("2020-10-01")
# peak2_end   = pd.Timestamp("2022-10-01")

# # =========================
# # 3. 构造多变量序列
# # =========================
# def create_sequences_multivariate(data, seq_len, target_index=0):
#     xs, ys = [], []
#     for i in range(len(data)-seq_len):
#         x = data[i:i+seq_len, :]
#         y = data[i+seq_len, target_index]
#         xs.append(x)
#         ys.append(y)
#     return np.array(xs), np.array(ys)

# # =========================
# # 4. LSTM模型
# # =========================
# class LSTMModel(nn.Module):
#     def __init__(self, input_size=3, hidden_size=50, num_layers=2):
#         super().__init__()
#         self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
#         self.fc = nn.Linear(hidden_size, 1)

#     def forward(self, x):
#         out, _ = self.lstm(x)
#         out = out[:, -1, :]
#         out = self.fc(out)
#         return out

# # =========================
# # 5. 评价指标
# # =========================
# def evaluate(y_true, y_pred, p):
#     y_true = np.array(y_true)
#     y_pred = np.array(y_pred)

#     mad = np.mean(np.abs(y_true - y_pred))
#     sse = np.sum((y_true - y_pred) ** 2)
#     mse = np.mean((y_true - y_pred) ** 2)
#     rmse = np.sqrt(mse)
#     r2 = r2_score(y_true, y_pred)

#     n = len(y_true)
#     adj_r2 = 1 - (1-r2)*(n-1)/(n-p-1)

#     mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8)))
#     wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))

#     return {
#         "MAD": mad,
#         "SSE": sse,
#         "MSE": mse,
#         "RMSE": rmse,
#         "R2": r2,
#         "Adj_R2": adj_r2,
#         "MAPE": mape,
#         "WAPE": wape
#     }

# # =========================
# # 6. 反归一化（只还原目标变量）
# # =========================
# def inverse_transform_target(scaler, data_scaled, feature_dim, target_index=0):
#     temp = np.zeros((len(data_scaled), feature_dim))
#     temp[:, target_index] = data_scaled.flatten()
#     inv = scaler.inverse_transform(temp)
#     return inv[:, target_index]

# # =========================
# # 7. 单个阶段训练+预测函数
# # =========================
# def run_peak(train_df, test_df, seq_len=30, epochs=20):

#     scaler = MinMaxScaler()

#     train_values = train_df[feature_cols].values
#     test_values  = test_df[feature_cols].values

#     train_scaled = scaler.fit_transform(train_values)
#     test_scaled  = scaler.transform(test_values)

#     X_train, y_train = create_sequences_multivariate(train_scaled, seq_len)
#     X_test, y_test   = create_sequences_multivariate(test_scaled, seq_len)

#     X_train = torch.tensor(X_train, dtype=torch.float32)
#     y_train = torch.tensor(y_train, dtype=torch.float32)

#     X_test = torch.tensor(X_test, dtype=torch.float32)
#     y_test = torch.tensor(y_test, dtype=torch.float32)

#     model = LSTMModel(input_size=len(feature_cols))
#     criterion = nn.MSELoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

#     # 训练
#     for epoch in range(epochs):
#         model.train()
#         optimizer.zero_grad()
#         output = model(X_train)
#         loss = criterion(output, y_train)
#         loss.backward()
#         optimizer.step()

#     # 预测
#     model.eval()
#     with torch.no_grad():
#         pred = model(X_test).numpy()

#     y_pred = inverse_transform_target(scaler, pred, feature_dim=len(feature_cols))
#     y_true = inverse_transform_target(scaler, y_test.numpy(), feature_dim=len(feature_cols))

#     metrics = evaluate(y_true, y_pred, p=seq_len)

#     return y_true, y_pred, metrics

# # =========================
# # 8. Peak1
# # =========================
# train1 = series[series['date'] < peak1_start]
# test1  = series[(series['date'] >= peak1_start) & (series['date'] <= peak1_end)]

# y1_true, y1_pred, m1 = run_peak(train1, test1)

# # =========================
# # 9. Peak2
# # =========================
# train2 = series[series['date'] < peak2_start]
# test2  = series[(series['date'] >= peak2_start) & (series['date'] <= peak2_end)]

# y2_true, y2_pred, m2 = run_peak(train2, test2)

# # =========================
# # 10. 输出指标
# # =========================
# print("===== Peak1 2017-2019 =====")
# for k,v in m1.items():
#     print(k, ":", v)

# print("\n===== Peak2 2020-2022 =====")
# for k,v in m2.items():
#     print(k, ":", v)

# # =========================
# # 11. 绘图并保存
# # =========================
# plt.figure(figsize=(12,6))

# plt.plot(y1_true, label="Peak1 True")
# plt.plot(y1_pred, label="Peak1 Pred")

# offset = len(y1_true)
# plt.plot(range(offset, offset+len(y2_true)), y2_true, label="Peak2 True")
# plt.plot(range(offset, offset+len(y2_true)), y2_pred, label="Peak2 Pred")

# plt.legend()
# plt.title("Multivariate LSTM Prediction for BTC Developers")
# plt.savefig("btc_multivariate_lstm_prediction.png", dpi=300)
# plt.show()

# LStM+特征遍历组合-BTC
# import pandas as pd
# import numpy as np
# import torch
# import torch.nn as nn
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import r2_score
# from itertools import product

# # =========================
# # 1. 读取数据
# # =========================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# df = pd.read_csv(file_path)
# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# target_col = 'btc_new_developers'

# # =========================
# # 2. 特征分组（7×4×4）
# # =========================
# price_features = [
#     'btc_price_lag1', 'ln_btc_price_lag1', 'btc_return_1d',
#     'btc_return_7d', 'btc_vol_7d', 'btc_ma_7d', 'btc_trend_7d'
# ]

# p_event_features = [
#     'btc_p_event_lag1', 'btc_p_event_sum_7',
#     'btc_p_event_mean_7', 'btc_p_event_vol_7'
# ]

# q_event_features = [
#     'btc_q_event_lag1', 'btc_q_event_sum_7',
#     'btc_q_event_mean_7', 'btc_q_event_vol_7'
# ]

# # =========================
# # 3. 时间划分
# # =========================
# peak1_start = pd.Timestamp("2017-01-01")
# peak1_end   = pd.Timestamp("2019-01-01")
# peak2_start = pd.Timestamp("2020-10-01")
# peak2_end   = pd.Timestamp("2022-10-01")

# # =========================
# # 4. LSTM模型和辅助函数
# # =========================
# def create_sequences_multivariate(data, seq_len, target_index=0):
#     xs, ys = [], []
#     for i in range(len(data)-seq_len):
#         x = data[i:i+seq_len, :]
#         y = data[i+seq_len, target_index]
#         xs.append(x)
#         ys.append(y)
#     return np.array(xs), np.array(ys)

# class LSTMModel(nn.Module):
#     def __init__(self, input_size, hidden_size=50, num_layers=2):
#         super().__init__()
#         self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
#         self.fc = nn.Linear(hidden_size, 1)

#     def forward(self, x):
#         out, _ = self.lstm(x)
#         out = out[:, -1, :]
#         out = self.fc(out)
#         return out

# def evaluate(y_true, y_pred, p):
#     y_true = np.array(y_true)
#     y_pred = np.array(y_pred)
#     mad = np.mean(np.abs(y_true - y_pred))
#     sse = np.sum((y_true - y_pred) ** 2)
#     mse = np.mean((y_true - y_pred) ** 2)
#     rmse = np.sqrt(mse)
#     r2 = r2_score(y_true, y_pred)
#     n = len(y_true)
#     adj_r2 = 1 - (1-r2)*(n-1)/(n-p-1)
#     mape = np.mean(np.abs((y_true - y_pred)/(y_true+1e-8)))
#     wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))
#     return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
#             "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# def inverse_transform_target(scaler, data_scaled, feature_dim, target_index=0):
#     temp = np.zeros((len(data_scaled), feature_dim))
#     temp[:, target_index] = data_scaled.flatten()
#     inv = scaler.inverse_transform(temp)
#     return inv[:, target_index]

# def run_peak(train_df, test_df, feature_cols, seq_len=30, epochs=20):
#     scaler = MinMaxScaler()
#     train_values = train_df[feature_cols].values
#     test_values  = test_df[feature_cols].values
#     train_scaled = scaler.fit_transform(train_values)
#     test_scaled  = scaler.transform(test_values)

#     X_train, y_train = create_sequences_multivariate(train_scaled, seq_len)
#     X_test, y_test   = create_sequences_multivariate(test_scaled, seq_len)

#     X_train = torch.tensor(X_train, dtype=torch.float32)
#     y_train = torch.tensor(y_train, dtype=torch.float32)
#     X_test  = torch.tensor(X_test, dtype=torch.float32)
#     y_test  = torch.tensor(y_test, dtype=torch.float32)

#     model = LSTMModel(input_size=len(feature_cols))
#     criterion = nn.MSELoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

#     for epoch in range(epochs):
#         model.train()
#         optimizer.zero_grad()
#         output = model(X_train)
#         loss = criterion(output, y_train)
#         loss.backward()
#         optimizer.step()

#     model.eval()
#     with torch.no_grad():
#         pred = model(X_test).numpy()

#     y_pred = inverse_transform_target(scaler, pred, feature_dim=len(feature_cols))
#     y_true = inverse_transform_target(scaler, y_test.numpy(), feature_dim=len(feature_cols))
#     metrics = evaluate(y_true, y_pred, p=seq_len)
#     return y_true, y_pred, metrics

# # =========================
# # 5. 遍历特征组合并找最优
# # =========================
# results_peak1 = []
# results_peak2 = []

# for price_f, p_f, q_f in product(price_features, p_event_features, q_event_features):
#     feature_cols = [price_f, p_f, q_f]
#     tmp = df[['date'] + feature_cols + [target_col]].dropna()

#     train1 = tmp[tmp['date'] < peak1_start]
#     test1  = tmp[(tmp['date'] >= peak1_start) & (tmp['date'] <= peak1_end)]
#     train2 = tmp[tmp['date'] < peak2_start]
#     test2  = tmp[(tmp['date'] >= peak2_start) & (tmp['date'] <= peak2_end)]

#     if len(test1) < 30 or len(test2) < 30:
#         continue

#     _, _, m1 = run_peak(train1, test1, feature_cols)
#     _, _, m2 = run_peak(train2, test2, feature_cols)

#     results_peak1.append((feature_cols, m1))
#     results_peak2.append((feature_cols, m2))

# best_p1 = max(results_peak1, key=lambda x: x[1]['Adj_R2'])
# best_p2 = max(results_peak2, key=lambda x: x[1]['Adj_R2'])

# def print_result(title, result):
#     features, metrics = result
#     print("\n==========================")
#     print(title)
#     print("Best Features:", features)
#     print("--------------------------")
#     for k, v in metrics.items():
#         print(f"{k}: {v:.4f}")

# print_result("Peak1 BEST (Adj R2)", best_p1)
# print_result("Peak2 BEST (Adj R2)", best_p2)

# # =========================
# # 6. 绘图最优组合
# # =========================
# best_features = best_p2[0]
# tmp = df[['date'] + best_features + [target_col]].dropna()
# train = tmp[tmp['date'] < peak2_start]
# test  = tmp[(tmp['date'] >= peak2_start) & (tmp['date'] <= peak2_end)]
# y_true, y_pred, _ = run_peak(train, test, best_features)

# plt.figure(figsize=(12,6))
# plt.plot(y_true, label="True")
# plt.plot(y_pred, label="Pred")
# plt.title(f"Best Multivariate LSTM Prediction ({best_features})")
# plt.legend()
# plt.savefig("btc_multivariate_lstm_best_prediction.png", dpi=300)
# plt.show()

# # =========================
# # 7. 保存所有组合结果（可选）
# # =========================
# all_results = []
# for (f, m) in results_peak1:
#     row = {'Peak': 'Peak1', 'Features': str(f)}
#     row.update(m)
#     all_results.append(row)
# for (f, m) in results_peak2:
#     row = {'Peak': 'Peak2', 'Features': str(f)}
#     row.update(m)
#     all_results.append(row)

# res_df = pd.DataFrame(all_results)
# res_df.to_csv("multivariate_lstm_feature_combinations_results.csv", index=False)


# LStM+特征遍历组合-ETH
# import pandas as pd
# import numpy as np
# import torch
# import torch.nn as nn
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import r2_score
# from itertools import product

# # =========================
# # 1. 读取数据
# # =========================
# file_path = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
# df = pd.read_csv(file_path)
# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date')

# target_col = 'eth_new_developers'

# # =========================
# # 2. 特征分组（7×4×4）
# # =========================
# price_features = [
#     'eth_price_lag1', 'ln_eth_price_lag1', 'eth_return_1d',
#     'eth_return_7d', 'eth_vol_7d', 'eth_ma_7d', 'eth_trend_7d'
# ]

# p_event_features = [
#     'eth_p_event_lag1', 'eth_p_event_sum_7',
#     'eth_p_event_mean_7', 'eth_p_event_vol_7'
# ]

# q_event_features = [
#     'eth_q_event_lag1', 'eth_q_event_sum_7',
#     'eth_q_event_mean_7', 'eth_q_event_vol_7'
# ]

# # =========================
# # 3. 时间划分
# # =========================
# peak1_start = pd.Timestamp("2017-01-01")
# peak1_end   = pd.Timestamp("2019-01-01")
# peak2_start = pd.Timestamp("2020-10-01")
# peak2_end   = pd.Timestamp("2023-01-01")

# # =========================
# # 4. LSTM模型和辅助函数
# # =========================
# def create_sequences_multivariate(data, seq_len, target_index=0):
#     xs, ys = [], []
#     for i in range(len(data)-seq_len):
#         x = data[i:i+seq_len, :]
#         y = data[i+seq_len, target_index]
#         xs.append(x)
#         ys.append(y)
#     return np.array(xs), np.array(ys)

# class LSTMModel(nn.Module):
#     def __init__(self, input_size, hidden_size=50, num_layers=2):
#         super().__init__()
#         self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
#         self.fc = nn.Linear(hidden_size, 1)

#     def forward(self, x):
#         out, _ = self.lstm(x)
#         out = out[:, -1, :]
#         out = self.fc(out)
#         return out

# def evaluate(y_true, y_pred, p):
#     y_true = np.array(y_true)
#     y_pred = np.array(y_pred)
#     mad = np.mean(np.abs(y_true - y_pred))
#     sse = np.sum((y_true - y_pred) ** 2)
#     mse = np.mean((y_true - y_pred) ** 2)
#     rmse = np.sqrt(mse)
#     r2 = r2_score(y_true, y_pred)
#     n = len(y_true)
#     adj_r2 = 1 - (1-r2)*(n-1)/(n-p-1)
#     mape = np.mean(np.abs((y_true - y_pred)/(y_true+1e-8)))
#     wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true))
#     return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
#             "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# def inverse_transform_target(scaler, data_scaled, feature_dim, target_index=0):
#     temp = np.zeros((len(data_scaled), feature_dim))
#     temp[:, target_index] = data_scaled.flatten()
#     inv = scaler.inverse_transform(temp)
#     return inv[:, target_index]

# def run_peak(train_df, test_df, feature_cols, seq_len=30, epochs=20):
#     scaler = MinMaxScaler()
#     train_values = train_df[feature_cols].values
#     test_values  = test_df[feature_cols].values
#     train_scaled = scaler.fit_transform(train_values)
#     test_scaled  = scaler.transform(test_values)

#     X_train, y_train = create_sequences_multivariate(train_scaled, seq_len)
#     X_test, y_test   = create_sequences_multivariate(test_scaled, seq_len)

#     X_train = torch.tensor(X_train, dtype=torch.float32)
#     y_train = torch.tensor(y_train, dtype=torch.float32)
#     X_test  = torch.tensor(X_test, dtype=torch.float32)
#     y_test  = torch.tensor(y_test, dtype=torch.float32)

#     model = LSTMModel(input_size=len(feature_cols))
#     criterion = nn.MSELoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

#     for epoch in range(epochs):
#         model.train()
#         optimizer.zero_grad()
#         output = model(X_train)
#         loss = criterion(output, y_train)
#         loss.backward()
#         optimizer.step()

#     model.eval()
#     with torch.no_grad():
#         pred = model(X_test).numpy()

#     y_pred = inverse_transform_target(scaler, pred, feature_dim=len(feature_cols))
#     y_true = inverse_transform_target(scaler, y_test.numpy(), feature_dim=len(feature_cols))
#     metrics = evaluate(y_true, y_pred, p=seq_len)
#     return y_true, y_pred, metrics

# # =========================
# # 5. 遍历特征组合并找最优
# # =========================
# results_peak1 = []
# results_peak2 = []

# for price_f, p_f, q_f in product(price_features, p_event_features, q_event_features):
#     feature_cols = [price_f, p_f, q_f]
#     tmp = df[['date'] + feature_cols + [target_col]].dropna()

#     train1 = tmp[tmp['date'] < peak1_start]
#     test1  = tmp[(tmp['date'] >= peak1_start) & (tmp['date'] <= peak1_end)]
#     train2 = tmp[tmp['date'] < peak2_start]
#     test2  = tmp[(tmp['date'] >= peak2_start) & (tmp['date'] <= peak2_end)]

#     if len(test1) < 30 or len(test2) < 30:
#         continue

#     _, _, m1 = run_peak(train1, test1, feature_cols)
#     _, _, m2 = run_peak(train2, test2, feature_cols)

#     results_peak1.append((feature_cols, m1))
#     results_peak2.append((feature_cols, m2))

# best_p1 = max(results_peak1, key=lambda x: x[1]['Adj_R2'])
# best_p2 = max(results_peak2, key=lambda x: x[1]['Adj_R2'])

# def print_result(title, result):
#     features, metrics = result
#     print("\n==========================")
#     print(title)
#     print("Best Features:", features)
#     print("--------------------------")
#     for k, v in metrics.items():
#         print(f"{k}: {v:.4f}")

# print_result("Peak1 BEST (Adj R2)", best_p1)
# print_result("Peak2 BEST (Adj R2)", best_p2)

# # =========================
# # 6. 绘图最优组合
# # =========================
# best_features = best_p2[0]
# tmp = df[['date'] + best_features + [target_col]].dropna()
# train = tmp[tmp['date'] < peak2_start]
# test  = tmp[(tmp['date'] >= peak2_start) & (tmp['date'] <= peak2_end)]
# y_true, y_pred, _ = run_peak(train, test, best_features)

# plt.figure(figsize=(12,6))
# plt.plot(y_true, label="True")
# plt.plot(y_pred, label="Pred")
# plt.title(f"Best Multivariate LSTM Prediction ({best_features})")
# plt.legend()
# plt.savefig("eth_multivariate_lstm_best_prediction.png", dpi=300)
# plt.show()

# # =========================
# # 7. 保存所有组合结果（可选）
# # =========================
# all_results = []
# for (f, m) in results_peak1:
#     row = {'Peak': 'Peak1', 'Features': str(f)}
#     row.update(m)
#     all_results.append(row)
# for (f, m) in results_peak2:
#     row = {'Peak': 'Peak2', 'Features': str(f)}
#     row.update(m)
#     all_results.append(row)

# res_df = pd.DataFrame(all_results)
# res_df.to_csv("eth_multivariate_lstm_feature_combinations_results.csv", index=False)
