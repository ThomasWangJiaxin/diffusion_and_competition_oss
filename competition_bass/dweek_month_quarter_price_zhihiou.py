# =========
# 第二周期的那行写第二周期/第一周期的回报率
# 原理：每个周期最后一天的闭盘价作为该周期的价格
# import pandas as pd
# import numpy as np

# # ====== 输入输出文件 ======
# FILES = {
#     "weekly":   "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_weekly_timeline_event_all.csv",
#     "monthly":  "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_monthly_timeline_event_all.csv",
#     "quarterly":"/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_quarterly_timeline_event_all.csv"
# }

# # 输出路径模板
# OUT_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_ETHdev_{}_timeline_event_all_with_price_features.csv"

# # 时间窗口（期数窗口）
# WINDOWS = [2, 4, 6, 8, 10]


# def insert_after(df, col, new_cols):
#     """把 new_cols 插在 col 后面"""
#     col_index = df.columns.get_loc(col)

#     # 去掉重复的（如果之前存在）
#     new_cols = [c for c in new_cols if c not in df.columns]

#     new_order = (
#         list(df.columns[:col_index+1]) +
#         new_cols +
#         list(df.columns[col_index+1:])
#     )
#     return df[new_order]


# # ====== 主循环 ======
# for freq, path in FILES.items():

#     print(f"处理文件：{freq}")

#     df = pd.read_csv(path, parse_dates=["date"])
#     df = df.sort_values("date").reset_index(drop=True)

#     for coin in ["btc", "eth"]:
#         price = df[f"{coin}_price_last"]

#         # 记录本币种的所有新变量
#         new_vars = []

#         # ---------- (1) lag1 ----------
#         lag1 = f"{coin}_price_last_lag1"
#         df[lag1] = price.shift(1)
#         df[f"ln_{lag1}"] = np.log(df[lag1])
#         new_vars += [lag1, f"ln_{lag1}"]

#         # ---------- (2) 1-period log return ----------
#         ret1 = f"{coin}_return_1p"
#         df[ret1] = np.log(price / price.shift(1))
#         new_vars.append(ret1)

#         # ---------- (3) 多期 return、(4) vol、(5) MA、(6) trend ----------
#         for n in WINDOWS:

#             # return
#             r = f"{coin}_return_{n}p"
#             df[r] = np.log(price / price.shift(n))
#             new_vars.append(r)

#             # volatility（基于 1-period return）
#             v = f"{coin}_vol_{n}p"
#             df[v] = df[ret1].rolling(n).std()
#             new_vars.append(v)

#             # moving average
#             ma = f"{coin}_ma_{n}p"
#             df[ma] = price.rolling(n).mean()
#             new_vars.append(ma)

#             # trend = ln(price / MA)
#             trend = f"{coin}_trend_{n}p"
#             df[trend] = np.log(price / df[ma])
#             new_vars.append(trend)

#         # 插入所有新变量
#         df = insert_after(df, f"{coin}_price_last", new_vars)

#     # 保存
#     out_file = OUT_PATH.format(freq)
#     df.to_csv(out_file, index=False)
#     print(f"已保存：{out_file}\n")

# print("全部完成！")


# =====
import pandas as pd
import numpy as np

# ====== 输入输出文件 ======
FILES = {
    "weekly":   "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_weekly_timeline_event_all.csv",
    "monthly":  "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_monthly_timeline_event_all.csv",
    "quarterly":"/home/lab0/survival_diffusion_github/competition_bass/ETHdev_quarterly_timeline_event_all.csv"
}

OUT_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_{}_timeline_event_all_with_price_features.csv"

# 时间窗口（期数窗口）
WINDOWS = [2, 4, 6, 8, 10]

# ====== 工具函数 ======
def insert_after(df, col, new_cols):
    """把 new_cols 插在 col 后面"""
    col_index = df.columns.get_loc(col)
    new_cols = [c for c in new_cols if c not in df.columns]
    new_order = (
        list(df.columns[:col_index+1]) +
        new_cols +
        list(df.columns[col_index+1:])
    )
    return df[new_order]


# ====== 主循环 ======
for freq, path in FILES.items():
    print(f"处理文件：{freq}")

    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    for coin in ["eth"]:                   # 跑之前这里需要修改选择
        price = df[f"{coin}_price_last"]

        new_vars = []

        # ----- (1) lag1 -----
        lag1 = f"{coin}_price_lag1"
        df[lag1] = price.shift(1)
        df[f"ln_{lag1}"] = np.log(df[lag1])
        new_vars += [lag1, f"ln_{lag1}"]

        # ----- (2) 1-period return -----
        ret1 = f"{coin}_return_1p"
        df[ret1] = np.log(price.shift(1) / price.shift(2))  # 对齐当前周期新增量
        new_vars.append(ret1)

        # ----- (3) 多期 return、vol、MA、trend -----
        for n in WINDOWS:
            # n-period return
            r = f"{coin}_return_{n}p"
            df[r] = np.log(price.shift(1) / price.shift(n+1))  # 当前周期开发者数量受上一周期/上n周期价格影响
            new_vars.append(r)

            # volatility（基于 1-period return）
            v = f"{coin}_vol_{n}p"
            df[v] = df[ret1].rolling(n).std()
            new_vars.append(v)

            # moving average
            ma = f"{coin}_ma_{n}p"
            df[ma] = price.shift(1).rolling(n).mean()
            new_vars.append(ma)

            # trend = ln(price / MA)
            trend = f"{coin}_trend_{n}p"
            df[trend] = np.log(price.shift(1) / df[ma])
            new_vars.append(trend)

        # 插入所有新变量
        df = insert_after(df, f"{coin}_price_last", new_vars)

    # 保存
    out_file = OUT_PATH.format(freq)
    df.to_csv(out_file, index=False)
    print(f"已保存：{out_file}\n")

print("全部完成！")