# # BTC
# import pandas as pd
# import os
# import matplotlib.pyplot as plt
# import re

# # =================配置区域=================

# # BTC 主链
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv"

# # ETH 竞争链
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv"

# # 竞争链 - 格式1: ?_first_actor_count_2025_12_31.csv
# CHAINS_FORMAT1 = ['bitcoincash', 'bitcoinsv', 'bitcoingpu', 'bitcoincashnode', 'parity', 
#                   'lightningnetwork', 'rootstock', 'stacks', 'bob', 'zcash', 
#                   'solana', 'tron', 'bnb']

# # 竞争链 - 格式2: ?_first_actor_count_timeline_event_2025_12_31.csv
# CHAINS_FORMAT2 = ['lbtc', 'btcd', 'bcoin', 'litecoin', 'dogecoin', 'monero']

# # 构建完整的文件路径列表
# file_paths = []

# # 添加 BTC 主链
# file_paths.append(BTC_PATH)

# # 添加 ETH 竞争链
# file_paths.append(ETH_PATH)

# # 添加格式1的竞争链
# for chain in CHAINS_FORMAT1:
#     path = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_first_actor_count_2025_12_31.csv"
#     file_paths.append(path)

# # 添加格式2的竞争链
# for chain in CHAINS_FORMAT2:
#     path = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_first_actor_count_timeline_event_2025_12_31.csv"
#     file_paths.append(path)

# # 输出配置
# output_dir = '/home/lab0/survival_diffusion_github/'
# output_csv_name = 'btc_merged_first_actor_for_competition_day_2025_12_31.csv'
# plot_new_devs_name = 'btc_comparison_new_developers_2025_12_31.png'
# plot_cum_users_name = 'btc_comparison_cumulative_users_2025_12_31.png'

# # =========================================

# def extract_project_name(file_path):
#     """
#     从文件路径中提取项目名称。
#     例如：/path/to/bitcoin_first_actor_count_timeline_event_2025_12_31.csv -> bitcoin
#          /path/to/litecoin_first_actor_count_2025_12_31.csv -> litecoin
#     """
#     basename = os.path.basename(file_path)
    
#     # 尝试匹配两种格式
#     # 格式1: name_first_actor_count_timeline_event_2025_12_31.csv
#     match1 = re.search(r'(.+?)_first_actor_count_timeline_event_\d{4}_\d{2}_\d{2}\.csv', basename)
#     if match1:
#         return match1.group(1)
    
#     # 格式2: name_first_actor_count_2025_12_31.csv
#     match2 = re.search(r'(.+?)_first_actor_count_\d{4}_\d{2}_\d{2}\.csv', basename)
#     if match2:
#         return match2.group(1)
    
#     # 如果都不匹配，返回基础文件名作为后备
#     print(f"⚠️  警告: 文件名 '{basename}' 不符合预期格式，将使用默认名称。")
#     return os.path.splitext(basename)[0]


# def process_files(paths):
#     """处理所有文件并返回数据框列表"""
#     dataframes = []
    
#     print("="*80)
#     print("开始处理文件...")
#     print("="*80)
    
#     successful = 0
#     skipped = 0
    
#     for i, path in enumerate(paths, 1):
#         if not os.path.exists(path):
#             print(f"❌ [{i}/{len(paths)}] 文件不存在，跳过: {os.path.basename(path)}")
#             skipped += 1
#             continue
            
#         project_name = extract_project_name(path)
        
#         try:
#             # 读取CSV
#             df = pd.read_csv(path)
            
#             # 确保 'date' 列存在
#             if 'date' not in df.columns:
#                 print(f"❌ [{i}/{len(paths)}] {project_name}: 缺少 'date' 列，跳过")
#                 skipped += 1
#                 continue
            
#             # 将日期列转换为 datetime 对象
#             df['date'] = pd.to_datetime(df['date'])
            
#             # 将日期设置为索引
#             df.set_index('date', inplace=True)
            
#             # 重命名列，加上项目前缀
#             new_columns = {}
#             if 'new_developers' in df.columns:
#                 new_columns['new_developers'] = f'{project_name}_new_developers'
#             if 'cum_users' in df.columns:
#                 new_columns['cum_users'] = f'{project_name}_cum_users'
            
#             if not new_columns:
#                 print(f"❌ [{i}/{len(paths)}] {project_name}: 缺少必要的列，跳过")
#                 skipped += 1
#                 continue
            
#             df.rename(columns=new_columns, inplace=True)
            
#             # 只保留需要的列
#             df = df[list(new_columns.values())]
            
#             dataframes.append(df)
#             successful += 1
#             print(f"✅ [{i}/{len(paths)}] {project_name:<20} {len(df):>8,} 条记录")
            
#         except Exception as e:
#             print(f"❌ [{i}/{len(paths)}] {project_name}: 处理失败 - {e}")
#             skipped += 1
    
#     print("="*80)
#     print(f"📊 处理汇总:")
#     print(f"  ✅ 成功: {successful} 个项目")
#     print(f"  ❌ 跳过: {skipped} 个项目")
#     print("="*80)
    
#     return dataframes


# def merge_dataframes(dfs):
#     """合并所有数据框"""
#     if not dfs:
#         print("❌ 没有有效的数据框可合并。")
#         return None
    
#     print("\n正在合并数据...")
    
#     # 使用 concat 按列(axis=1)合并所有数据框
#     # pandas 会自动根据索引（日期）对齐数据
#     merged_df = pd.concat(dfs, axis=1)
    
#     # 按日期索引排序
#     merged_df.sort_index(inplace=True)
    
#     # 🔥 保留 NaN 空值，不填充为 0
#     # merged_df.fillna(0, inplace=True)  # 已注释
    
#     print(f"✅ 合并完成")
#     print(f"   时间范围: {merged_df.index.min().date()} 到 {merged_df.index.max().date()}")
#     print(f"   总天数: {len(merged_df):,}")
#     print(f"   总列数: {len(merged_df.columns)}")
    
#     print("\n合并后数据预览 (前 5 行):")
#     print(merged_df.head())
#     print("\n合并后数据预览 (后 5 行):")
#     print(merged_df.tail())
    
#     return merged_df


# def plot_comparisons(df, output_folder):
#     """生成对比图表"""
#     # 确保输出目录存在
#     os.makedirs(output_folder, exist_ok=True)
    
#     # 使用 seaborn 样式
#     try:
#         import seaborn as sns
#         sns.set_theme(style="whitegrid")
#     except ImportError:
#         plt.style.use('ggplot')
    
#     # --- 图表 1: New Developers ---
#     print("\n正在绘制 New Developers 图表...")
#     plt.figure(figsize=(16, 8))
    
#     # 筛选出所有以 _new_developers 结尾的列
#     new_dev_cols = [col for col in df.columns if col.endswith('_new_developers')]
    
#     for col in new_dev_cols:
#         # 提取图例名称（去掉后缀）
#         label_name = col.replace('_new_developers', '').upper()
#         plt.plot(df.index, df[col], label=label_name, alpha=0.7, linewidth=1.5)
    
#     plt.title('Comparison of New Developers Over Time', fontsize=16, fontweight='bold')
#     plt.xlabel('Date', fontsize=12)
#     plt.ylabel('Count of New Developers', fontsize=12)
#     plt.legend(title="Projects", bbox_to_anchor=(1.05, 1), loc='upper left')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     save_path_dev = os.path.join(output_folder, plot_new_devs_name)
#     plt.savefig(save_path_dev, dpi=300, bbox_inches='tight')
#     plt.close()
#     print(f"✅ 图表已保存: {save_path_dev}")
    
#     # --- 图表 2: Cumulative Users ---
#     print("正在绘制 Cumulative Users 图表...")
#     plt.figure(figsize=(16, 8))
    
#     # 筛选出所有以 _cum_users 结尾的列
#     cum_user_cols = [col for col in df.columns if col.endswith('_cum_users')]
    
#     for col in cum_user_cols:
#         label_name = col.replace('_cum_users', '').upper()
#         plt.plot(df.index, df[col], label=label_name, linewidth=2)
    
#     plt.title('Comparison of Cumulative Users Over Time', fontsize=16, fontweight='bold')
#     plt.xlabel('Date', fontsize=12)
#     plt.ylabel('Cumulative Count of Users', fontsize=12)
#     plt.legend(title="Projects", bbox_to_anchor=(1.05, 1), loc='upper left')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     # 可选：使用对数坐标轴
#     # plt.yscale('log')
    
#     save_path_user = os.path.join(output_folder, plot_cum_users_name)
#     plt.savefig(save_path_user, dpi=300, bbox_inches='tight')
#     plt.close()
#     print(f"✅ 图表已保存: {save_path_user}")


# # ================= 主程序运行 =================
# if __name__ == "__main__":
#     print("\n" + "="*80)
#     print("🚀 Bitcoin 生态系统开发者数据合并分析")
#     print("="*80)
#     print(f"\n📋 配置信息:")
#     print(f"   将处理 {len(file_paths)} 个文件")
#     print(f"   输出目录: {output_dir}")
#     print(f"   输出CSV: {output_csv_name}")
    
#     # 1. 处理所有文件
#     processed_dfs = process_files(file_paths)
    
#     if not processed_dfs:
#         print("\n❌ 错误：没有成功处理任何文件，程序终止。")
#         exit(1)
    
#     # 2. 合并数据框
#     merged_df = merge_dataframes(processed_dfs)
    
#     if merged_df is not None:
#         # 确保输出目录存在
#         os.makedirs(output_dir, exist_ok=True)
        
#         # 3. 保存合并后的CSV
#         csv_save_path = os.path.join(output_dir, output_csv_name)
#         merged_df.to_csv(csv_save_path, index_label='date')
#         print(f"\n✅ 合并后的CSV已保存至: {csv_save_path}")
        
#         # 4. 生成并保存图表
#         plot_comparisons(merged_df, output_dir)
        
#         print("\n" + "="*80)
#         print("🎉 所有任务完成！")
#         print("="*80)
#         print(f"\n📁 输出文件:")
#         print(f"   1. {csv_save_path}")
#         print(f"   2. {os.path.join(output_dir, plot_new_devs_name)}")
#         print(f"   3. {os.path.join(output_dir, plot_cum_users_name)}")
#         print("="*80)
#     else:
#         print("\n❌ 合并失败，程序终止。")
#         exit(1)


# ETH
import pandas as pd
import os
import matplotlib.pyplot as plt
import re

# =================配置区域=================

# ETH 主链
ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv"

# BTC 竞争链
BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_count_timeline_event_2025_12_31.csv"

# 竞争链 - 格式1: ?_first_actor_count_2025_12_31.csv
CHAINS_FORMAT1 = ['etc', 'ethereumpow', 'erigon', 'reth', 'besu', 'nethermind', 
                  'bnb', 'polygon', 'harmony', 'avalanche', 'arbitrum', 'optimism', 
                  'zksync', 'skale', 'ronin', 'polkadot', 'cosmos', 'tron', 
                  'solana', 'near', 'aptos', 'sui', 'starknet', 'flow', 
                  'arweave', 'helium', 'theta', 'secretnetwork', 'alephzero']

# 构建完整的文件路径列表
file_paths = []

# 添加 ETH 主链
file_paths.append(ETH_PATH)

# 添加 BTC 竞争链
file_paths.append(BTC_PATH)

# 添加格式1的竞争链
for chain in CHAINS_FORMAT1:
    path = f"/home/lab0/survival_diffusion_github/Ethereum/{chain}_first_actor_count_2025_12_31.csv"
    file_paths.append(path)

# 输出配置
output_dir = '/home/lab0/survival_diffusion_github/'
output_csv_name = 'eth_merged_first_actor_for_competition_day_2025_12_31.csv'
plot_new_devs_name = 'eth_comparison_new_developers_2025_12_31.png'
plot_cum_users_name = 'eth_comparison_cumulative_users_2025_12_31.png'

# =========================================

def extract_project_name(file_path):
    """
    从文件路径中提取项目名称。
    例如：/path/to/bitcoin_first_actor_count_timeline_event_2025_12_31.csv -> bitcoin
         /path/to/litecoin_first_actor_count_2025_12_31.csv -> litecoin
    """
    basename = os.path.basename(file_path)
    
    # 尝试匹配两种格式
    # 格式1: name_first_actor_count_timeline_event_2025_12_31.csv
    match1 = re.search(r'(.+?)_first_actor_count_timeline_event_\d{4}_\d{2}_\d{2}\.csv', basename)
    if match1:
        return match1.group(1)
    
    # 格式2: name_first_actor_count_2025_12_31.csv
    match2 = re.search(r'(.+?)_first_actor_count_\d{4}_\d{2}_\d{2}\.csv', basename)
    if match2:
        return match2.group(1)
    
    # 如果都不匹配，返回基础文件名作为后备
    print(f"⚠️  警告: 文件名 '{basename}' 不符合预期格式，将使用默认名称。")
    return os.path.splitext(basename)[0]


def process_files(paths):
    """处理所有文件并返回数据框列表"""
    dataframes = []
    
    print("="*80)
    print("开始处理文件...")
    print("="*80)
    
    successful = 0
    skipped = 0
    
    for i, path in enumerate(paths, 1):
        if not os.path.exists(path):
            print(f"❌ [{i}/{len(paths)}] 文件不存在，跳过: {os.path.basename(path)}")
            skipped += 1
            continue
            
        project_name = extract_project_name(path)
        
        try:
            # 读取CSV
            df = pd.read_csv(path)
            
            # 确保 'date' 列存在
            if 'date' not in df.columns:
                print(f"❌ [{i}/{len(paths)}] {project_name}: 缺少 'date' 列，跳过")
                skipped += 1
                continue
            
            # 将日期列转换为 datetime 对象
            df['date'] = pd.to_datetime(df['date'])
            
            # 将日期设置为索引
            df.set_index('date', inplace=True)
            
            # 重命名列，加上项目前缀
            new_columns = {}
            if 'new_developers' in df.columns:
                new_columns['new_developers'] = f'{project_name}_new_developers'
            if 'cum_users' in df.columns:
                new_columns['cum_users'] = f'{project_name}_cum_users'
            
            if not new_columns:
                print(f"❌ [{i}/{len(paths)}] {project_name}: 缺少必要的列，跳过")
                skipped += 1
                continue
            
            df.rename(columns=new_columns, inplace=True)
            
            # 只保留需要的列
            df = df[list(new_columns.values())]
            
            dataframes.append(df)
            successful += 1
            print(f"✅ [{i}/{len(paths)}] {project_name:<20} {len(df):>8,} 条记录")
            
        except Exception as e:
            print(f"❌ [{i}/{len(paths)}] {project_name}: 处理失败 - {e}")
            skipped += 1
    
    print("="*80)
    print(f"📊 处理汇总:")
    print(f"  ✅ 成功: {successful} 个项目")
    print(f"  ❌ 跳过: {skipped} 个项目")
    print("="*80)
    
    return dataframes


def merge_dataframes(dfs):
    """合并所有数据框"""
    if not dfs:
        print("❌ 没有有效的数据框可合并。")
        return None
    
    print("\n正在合并数据...")
    
    # 使用 concat 按列(axis=1)合并所有数据框
    # pandas 会自动根据索引（日期）对齐数据
    merged_df = pd.concat(dfs, axis=1)
    
    # 按日期索引排序
    merged_df.sort_index(inplace=True)
    
    # 🔥 保留 NaN 空值，不填充为 0
    # merged_df.fillna(0, inplace=True)  # 已注释
    
    print(f"✅ 合并完成")
    print(f"   时间范围: {merged_df.index.min().date()} 到 {merged_df.index.max().date()}")
    print(f"   总天数: {len(merged_df):,}")
    print(f"   总列数: {len(merged_df.columns)}")
    
    print("\n合并后数据预览 (前 5 行):")
    print(merged_df.head())
    print("\n合并后数据预览 (后 5 行):")
    print(merged_df.tail())
    
    return merged_df


def plot_comparisons(df, output_folder):
    """生成对比图表"""
    # 确保输出目录存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 使用 seaborn 样式
    try:
        import seaborn as sns
        sns.set_theme(style="whitegrid")
    except ImportError:
        plt.style.use('ggplot')
    
    # --- 图表 1: New Developers ---
    print("\n正在绘制 New Developers 图表...")
    plt.figure(figsize=(16, 8))
    
    # 筛选出所有以 _new_developers 结尾的列
    new_dev_cols = [col for col in df.columns if col.endswith('_new_developers')]
    
    for col in new_dev_cols:
        # 提取图例名称（去掉后缀）
        label_name = col.replace('_new_developers', '').upper()
        plt.plot(df.index, df[col], label=label_name, alpha=0.7, linewidth=1.5)
    
    plt.title('Comparison of New Developers Over Time', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Count of New Developers', fontsize=12)
    plt.legend(title="Projects", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path_dev = os.path.join(output_folder, plot_new_devs_name)
    plt.savefig(save_path_dev, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 图表已保存: {save_path_dev}")
    
    # --- 图表 2: Cumulative Users ---
    print("正在绘制 Cumulative Users 图表...")
    plt.figure(figsize=(16, 8))
    
    # 筛选出所有以 _cum_users 结尾的列
    cum_user_cols = [col for col in df.columns if col.endswith('_cum_users')]
    
    for col in cum_user_cols:
        label_name = col.replace('_cum_users', '').upper()
        plt.plot(df.index, df[col], label=label_name, linewidth=2)
    
    plt.title('Comparison of Cumulative Users Over Time', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Count of Users', fontsize=12)
    plt.legend(title="Projects", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 可选：使用对数坐标轴
    # plt.yscale('log')
    
    save_path_user = os.path.join(output_folder, plot_cum_users_name)
    plt.savefig(save_path_user, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 图表已保存: {save_path_user}")


# ================= 主程序运行 =================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Ethereum 生态系统开发者数据合并分析")
    print("="*80)
    print(f"\n📋 配置信息:")
    print(f"   将处理 {len(file_paths)} 个文件")
    print(f"   输出目录: {output_dir}")
    print(f"   输出CSV: {output_csv_name}")
    
    # 1. 处理所有文件
    processed_dfs = process_files(file_paths)
    
    if not processed_dfs:
        print("\n❌ 错误：没有成功处理任何文件，程序终止。")
        exit(1)
    
    # 2. 合并数据框
    merged_df = merge_dataframes(processed_dfs)
    
    if merged_df is not None:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. 保存合并后的CSV
        csv_save_path = os.path.join(output_dir, output_csv_name)
        merged_df.to_csv(csv_save_path, index_label='date')
        print(f"\n✅ 合并后的CSV已保存至: {csv_save_path}")
        
        # 4. 生成并保存图表
        plot_comparisons(merged_df, output_dir)
        
        print("\n" + "="*80)
        print("🎉 所有任务完成！")
        print("="*80)
        print(f"\n📁 输出文件:")
        print(f"   1. {csv_save_path}")
        print(f"   2. {os.path.join(output_dir, plot_new_devs_name)}")
        print(f"   3. {os.path.join(output_dir, plot_cum_users_name)}")
        print("="*80)
    else:
        print("\n❌ 合并失败，程序终止。")
        exit(1)