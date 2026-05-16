# import pandas as pd
# import os

# # --- 请在此处替换为您要查看的 CSV 文件的路径 ---
# FILE_PATH = '/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv'

# def display_time_range(file_path):
#     """
#     读取指定路径的 CSV 文件，并输出其 created_at 列的最早和最晚时间。
#     """
#     if not os.path.exists(file_path):
#         print(f"❌ 错误：文件未找到。请检查路径是否正确: {file_path}")
#         return

#     try:
#         # 1. 加载数据
#         df = pd.read_csv(file_path, low_memory=False)
        
#         # 2. 确保 'created_at' 字段是日期时间类型
#         # errors='coerce' 会将无法解析的值设为 NaT (Not a Time)，避免程序中断
#         df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
#         if 'created_at' not in df.columns:
#             print("❌ 错误：文件中未找到 'created_at' 列。")
#             return
            
#         # 3. 移除 NaT 值后，计算最早和最晚时间
#         df_valid_time = df.dropna(subset=['created_at'])
        
#         if df_valid_time.empty:
#             print("❌ 错误：'created_at' 列中没有有效的日期时间数据。")
#             return

#         min_time = df_valid_time['created_at'].min()
#         max_time = df_valid_time['created_at'].max()

#         print(f"✅ 文件加载成功: {file_path}")
#         print("\n--- 'created_at' 时间范围 ---")
#         print(f"最早时间 (Min): {min_time}")
#         print(f"最晚时间 (Max): {max_time}")
        
#         # 额外输出统计信息
#         print("\n--- 统计信息 ---")
#         print(f"总记录数: {len(df):,}")
#         print(f"有效时间记录数: {len(df_valid_time):,}")

#     except Exception as e:
#         print(f"❌ 读取或处理文件时发生错误: {e}")

# # --- 执行函数 ---
# if __name__ == "__main__":
#     display_time_range(FILE_PATH)

import pandas as pd
import os

# 假设您正在处理的是 Ethereum 数据集
FILE_PATH = '/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv' 
EVENT_TYPE_TO_CHECK = 'Event'

def check_event_existence(file_path, event_type):
    """
    检查特定事件类型是否存在，并找出其最早和最晚的出现时间。
    """
    if not os.path.exists(file_path):
        print(f"❌ 错误：文件未找到于 {file_path}")
        return

    try:
        df = pd.read_csv(file_path, low_memory=False)
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # 1. 检查事件是否存在于整个数据集
        if event_type not in df['event_type'].unique():
            print(f"【结论】: {event_type} 在整个数据集中不存在。您的全集列表可能记录有误。")
            return

        # 2. 筛选出目标事件
        df_target = df[df['event_type'] == event_type].copy()
        
        if df_target.empty:
            print(f"【结论】: 尽管 {event_type} 被列出，但没有找到实际记录。可能在数据清洗阶段被移除。")
            return

        # 3. 找出最早和最晚时间
        min_time = df_target['created_at'].min()
        max_time = df_target['created_at'].max()
        count = len(df_target)
        
        print(f"\n--- {event_type} 存在时间段 ---")
        print(f"总记录数: {count:,}")
        print(f"最早出现时间: {min_time}")
        print(f"最晚出现时间: {max_time}")
        
        # 4. 确认是否跨越 2015 年
        boundary = pd.to_datetime('2015-01-01')
        
        exists_before_2015 = min_time < boundary
        exists_after_2015 = max_time >= boundary
        
        print("\n--- 2015 分割线验证 ---")
        print(f"存在于 2015 年前: {'✅ 是' if exists_before_2015 else '❌ 否'}")
        print(f"存在于 2015 年后: {'✅ 是' if exists_after_2015 else '❌ 否'}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")

check_event_existence(FILE_PATH, EVENT_TYPE_TO_CHECK)