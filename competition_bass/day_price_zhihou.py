# ====== 第二天的那行写第二天/第一天的回报率
# import pandas as pd
# import numpy as np

# # ====== 配置 ======
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_day_timeline_event_all.csv"
# OUT_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_day_timeline_event_all_with_price_features.csv"

# # ====== 载入数据 ======
# df = pd.read_csv(CSV_PATH, parse_dates=["date"])
# df = df.sort_values("date").reset_index(drop=True)

# # ====== 存储原始列顺序 ======
# original_cols = list(df.columns)

# def insert_after(df, col, new_cols):
#     """把 new_cols 插在 col 后，若列已存在则不重复插入"""
#     col_index = df.columns.get_loc(col)

#     # 过滤掉已经存在的重复列
#     filtered = [c for c in new_cols if c not in df.columns]

#     new_order = (
#         list(df.columns[:col_index+1]) +
#         filtered +
#         list(df.columns[col_index+1:])
#     )
#     return df[new_order]

# # ====== 为每个币生成变量，并插入到原列后 ======
# for coin in ["btc", "eth"]:
#     price = df[f"{coin}_price"]

#     new_vars = []

#     # (1) 前一天收盘价
#     lag1 = f"{coin}_price_lag1"
#     df[lag1] = price.shift(1)
#     df[f"ln_{lag1}"] = np.log(df[lag1])
#     new_vars += [lag1, f"ln_{lag1}"]

#     # (2) 日 log return
#     ret1 = f"{coin}_return_1d"
#     df[ret1] = np.log(price / price.shift(1))
#     new_vars.append(ret1)

#     # (3) 多期 log return + (4) 波动率 + (5) MA + (6) 趋势
#     for n in [7, 14, 21, 30]:
#         # return
#         r = f"{coin}_return_{n}d"
#         df[r] = np.log(price / price.shift(n))
#         new_vars.append(r)

#         # volatility (基于 1d return)
#         v = f"{coin}_vol_{n}d"
#         df[v] = df[f"{coin}_return_1d"].rolling(n).std()
#         new_vars.append(v)

#         # moving average
#         ma = f"{coin}_ma_{n}d"
#         df[ma] = price.rolling(n).mean()
#         new_vars.append(ma)

#         # trend price / MA
#         trend = f"{coin}_trend_{n}d"
#         df[trend] = np.log(price / df[ma])
#         new_vars.append(trend)

#     # 插入变量到 price 列后
#     df = insert_after(df, f"{coin}_price", new_vars)

# # ====== 保存 ======
# df.to_csv(OUT_PATH, index=False)
# print(f"价格特征数据已保存到：{OUT_PATH}")






# ======
# 考虑滞后：第三天的那行是写第二天/第一天的日回报率
import pandas as pd
import numpy as np

# ====== 配置 ======
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all.csv"
OUT_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_features.csv"

# ====== 载入数据 ======
df = pd.read_csv(CSV_PATH, parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

# ====== 插入新列的函数 ======
def insert_after(df, col, new_cols):
    col_index = df.columns.get_loc(col)
    filtered = [c for c in new_cols if c not in df.columns]
    new_order = list(df.columns[:col_index+1]) + filtered + list(df.columns[col_index+1:])
    return df[new_order]

# ====== 生成滞后价格相关特征 ======
for coin in ["eth"]:
    price = df[f"{coin}_price"]

    new_vars = []

    # (1) 前一天收盘价
    lag1 = f"{coin}_price_lag1"
    df[lag1] = price.shift(1)
    df[f"ln_{lag1}"] = np.log(df[lag1])
    new_vars += [lag1, f"ln_{lag1}"]

    # (2) 前一天日 log return
    ret1 = f"{coin}_return_1d"
    df[ret1] = np.log(price.shift(1) / price.shift(2))
    new_vars.append(ret1)

    # (3) 多期 log return + (4) 波动率 + (5) MA + (6) trend
    for n in [7, 14, 21, 30]:
        # return
        r = f"{coin}_return_{n}d"
        df[r] = np.log(price.shift(1) / price.shift(n+1))
        new_vars.append(r)

        # volatility (基于 1d return)
        v = f"{coin}_vol_{n}d"
        df[v] = df[ret1].rolling(n).std()
        new_vars.append(v)

        # moving average
        ma = f"{coin}_ma_{n}d"
        df[ma] = price.shift(1).rolling(n).mean()
        new_vars.append(ma)

        # trend price / MA
        trend = f"{coin}_trend_{n}d"
        df[trend] = np.log(df[lag1] / df[ma])
        new_vars.append(trend)

    # 插入变量到 price 列后
    df = insert_after(df, f"{coin}_price", new_vars)

# ====== 保存 ======
df.to_csv(OUT_PATH, index=False)
print(f"价格特征数据已保存到：{OUT_PATH}")





# ====== 和第二段代码功能和结果一样 都是第三行放第二天/第一天的回报率 但代码结构更清晰 可读性更好 ======
# import pandas as pd
# import numpy as np
# import os
# import sys

# # --- Configuration (假设路径已修正) ---
# FILE_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_day_timeline_event_all.csv" 
# OUTPUT_FILE = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_day_timeline_event_all_financial_features.csv"

# # 定义资产和窗口大小
# ASSETS = ['btc', 'eth']
# WINDOWS = [7, 14, 21, 30]
# NEW_LAGGED_COLUMNS = [] 

# def calculate_financial_features(df):
#     """
#     计算所有必需的价格相关金融变量，并确保 t-1 滞后，同时保留所有原始行。
#     """
#     # ❗️ 注意：初始排序已经在 main 块完成，这里不再重复 reset_index
    
#     # 确保价格列是浮点数
#     for asset in ASSETS:
#         price_col = f'{asset}_price'
#         df[price_col] = pd.to_numeric(df[price_col], errors='coerce')

#     print("⏳ Starting feature calculation...")

#     df_temp = pd.DataFrame(index=df.index) 
    
#     for asset in ASSETS:
#         price_col = f'{asset}_price'
        
#         # 核心计算：Log Price 和 Log Return
#         df_temp[f'{asset}_log_price'] = np.log(df[price_col].replace(0, np.nan)) 
#         df_temp[f'{asset}_daily_return'] = np.log(df[price_col] / df[price_col].shift(1))
        
#         for n in WINDOWS:
#             # 2a. 移动平均 (MA) - 用于趋势
#             ma_t = df[price_col].rolling(window=n, min_periods=n).mean()
            
#             # 2b. 短期回报波动率 (Volatility) - 用于风险
#             vol_t = df_temp[f'{asset}_daily_return'].rolling(window=n, min_periods=n).std()

#             # 2c. N日累计回报率 (N-day Return) - 用于长期动量
#             n_day_ret_t = df_temp[f'{asset}_log_price'] - df_temp[f'{asset}_log_price'].shift(n)
            
#             # 2d. 高低位趋势 (Price Log / MA Log) - 用于相对强度
#             trend_t = df_temp[f'{asset}_log_price'] - np.log(ma_t)
            
#             # 3. 最终滞后处理 (t-1) 并添加到原始 DataFrame
            
#             # Log Price (价值信号)
#             new_col_name = f'{asset}_log_price_t1'
#             df[new_col_name] = df_temp[f'{asset}_log_price'].shift(1)
#             NEW_LAGGED_COLUMNS.append(new_col_name)

#             # Daily Return (动量)
#             new_col_name = f'{asset}_daily_return_t1'
#             df[new_col_name] = df_temp[f'{asset}_daily_return'].shift(1)
#             NEW_LAGGED_COLUMNS.append(new_col_name)
            
#             # Volatility
#             new_col_name = f'{asset}_volatility_{n}_t1'
#             df[new_col_name] = vol_t.shift(1)
#             NEW_LAGGED_COLUMNS.append(new_col_name)
            
#             # N-day Return
#             new_col_name = f'{asset}_n_day_return_{n}_t1'
#             df[new_col_name] = n_day_ret_t.shift(1)
#             NEW_LAGGED_COLUMNS.append(new_col_name)

#             # Trend Ratio
#             new_col_name = f'{asset}_trend_ratio_{n}_t1'
#             df[new_col_name] = trend_t.shift(1)
#             NEW_LAGGED_COLUMNS.append(new_col_name)


#     # 4. 最终排序和保存
    
#     # 确保最终输出按日期排序（虽然数据已经有序，但再次保证）
#     df = df.sort_values('date', ascending=True).reset_index(drop=True)
    
#     print("\n--- Features Added ---")
#     print(f"Total Original Rows (Preserved): {len(df):,}")
    
#     # 保存结果
#     df.to_csv(OUTPUT_FILE, index=False)
#     print(f"\n🎉 Feature enrichment complete. Data saved to {OUTPUT_FILE}")
#     print("\n--- New Feature Columns (Lagged) ---")
#     print([col for col in df.columns if '_t1' in col])
    
#     return df

# # --- Execution Block (新增初始排序) ---
# if __name__ == "__main__":
#     # 确保文件存在，并加载
#     try:
#         # 1. 加载数据
#         df_base = pd.read_csv(FILE_PATH)
        
#         # 2. 强化：确保 date 列是 datetime 类型
#         df_base['date'] = pd.to_datetime(df_base['date'])
        
#         # 3. 强化：按日期从早到晚排序 (保证后续 shift/rolling 的正确性)
#         df_base = df_base.sort_values('date', ascending=True).reset_index(drop=True)
        
#         # 4. 调用核心函数
#         calculate_financial_features(df_base)
        
#     except FileNotFoundError:
#         print(f"❌ 错误：请修正配置中的 FILE_PATH 变量，文件未找到。")
#     except Exception as e:
#         print(f"❌ 运行过程中发生错误: {e}")