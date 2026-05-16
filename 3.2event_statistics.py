import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# 读取CSV文件
file_path = '/home/lab0/survival_diffusion_github/Ethereum/ronin_event_count_per_day_2025_12_31.csv'
df = pd.read_csv(file_path)

# 将date列转换为日期类型
df['date'] = pd.to_datetime(df['date'])

# 按日期分组并计算每天的总事件数
daily_totals = df.groupby('date')['event_count'].sum().reset_index()
daily_totals.columns = ['date', 'total_events']

# 计算累计总事件数
daily_totals['cumulative_events'] = daily_totals['total_events'].cumsum()

# 创建一个图表，包含两个子图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 第一个子图：每天的事件总量
ax1.plot(daily_totals['date'], daily_totals['total_events'], marker='o', linestyle='-')
ax1.set_title('每日事件总量')
ax1.set_xlabel('日期')
ax1.set_ylabel('事件数量')
ax1.grid(True)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 第二个子图：累计事件总量
ax2.plot(daily_totals['date'], daily_totals['cumulative_events'], marker='o', linestyle='-', color='green')
ax2.set_title('累计事件总量')
ax2.set_xlabel('日期')
ax2.set_ylabel('累计事件数量')
ax2.grid(True)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# 创建一个堆叠条形图来显示每天各类事件的分布
event_pivot = df.pivot_table(index='date', columns='event_type', values='event_count', aggfunc='sum', fill_value=0)

# 绘制堆叠条形图
fig2, ax3 = plt.subplots(figsize=(14, 8))
event_pivot.plot(kind='bar', stacked=True, ax=ax3)
ax3.set_title('每日各类事件分布')
ax3.set_xlabel('日期')
ax3.set_ylabel('事件数量')
ax3.legend(title='事件类型')
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 生成统计表格
daily_event_stats = df.groupby(['date', 'event_type'])['event_count'].sum().reset_index()
daily_stats_with_total = daily_event_stats.pivot_table(index='date', columns='event_type', values='event_count', aggfunc='sum', fill_value=0)
daily_stats_with_total['All_events'] = daily_stats_with_total.sum(axis=1)

# 打印统计结果
print("\n每日各类事件统计:")
print(daily_stats_with_total)

# 调整布局并显示图表
plt.tight_layout()
plt.show()

# 保存统计结果到CSV
daily_stats_with_total.to_csv('/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_stats_2025_12_31.csv')

# 保存图表
fig.savefig('/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_trend_2025_12_31.png', bbox_inches='tight')
fig2.savefig('/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_distribution_2025_12_31.png', bbox_inches='tight')

print("统计结果已保存到 '/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_stats_2025_12_31.csv'")
print("图表已保存到 '/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_trend_2025_12_31.png' 和 '/home/lab0/survival_diffusion_github/Ethereum/ronin_event_daily_distribution_2025_12_31.png'")



# 批量
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import numpy as np
# import os

# # 定义所有项目列表
# # projects = [
# #     'etc', 'ethereumpow', 'erigon', 'reth', 'besu', 'nethermind', 
# #     'bnb', 'polygon', 'harmony', 'avalanche', 'arbitrum', 'optimism', 
# #     'zksync', 'skale', 'roninold', 'roninnew', 'polkadot', 'cosmos', 
# #     'tron', 'solanaold', 'solananew', 'near', 'aptos', 'sui', 
# #     'starknet', 'flow', 'arweave', 'helium', 'theta', 'secretnetwork', 
# #     'alephzero'
# # ]

# projects = ['bitcoincash', 'bitcoinsv', 'bitcoingpu', 'bitcoincashnode', 'parity', 'lightningnetwork', 'rootstock', 'stacks', 'bob', 'zcash', 'solanaold', 'solananew', 'tron', 'bnb']

# # 批量处理所有项目
# for project in projects:
#     try:
#         print(f"\n{'='*80}")
#         print(f"正在处理项目: {project.upper()}")
#         print(f"{'='*80}")
        
#         # 读取CSV文件
#         file_path = f'/home/lab0/survival_diffusion_github/Ethereum/{project}_event_count_per_day_2025_12_31.csv'
        
#         # 检查文件是否存在
#         if not os.path.exists(file_path):
#             print(f"⚠️  文件不存在，跳过: {file_path}")
#             continue
        
#         df = pd.read_csv(file_path)
        
#         # 将date列转换为日期类型
#         df['date'] = pd.to_datetime(df['date'])
        
#         # 按日期分组并计算每天的总事件数
#         daily_totals = df.groupby('date')['event_count'].sum().reset_index()
#         daily_totals.columns = ['date', 'total_events']
        
#         # 计算累计总事件数
#         daily_totals['cumulative_events'] = daily_totals['total_events'].cumsum()
        
#         print(f"✅ 数据加载完成，共 {len(daily_totals)} 天的数据")
#         print(f"   总事件数: {daily_totals['total_events'].sum():,}")
        
#         # 创建一个图表，包含两个子图
#         fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
#         # 第一个子图：每天的事件总量
#         ax1.plot(daily_totals['date'], daily_totals['total_events'], marker='o', linestyle='-')
#         ax1.set_title(f'{project.upper()} - 每日事件总量')
#         ax1.set_xlabel('日期')
#         ax1.set_ylabel('事件数量')
#         ax1.grid(True)
#         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#         plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
#         # 第二个子图：累计事件总量
#         ax2.plot(daily_totals['date'], daily_totals['cumulative_events'], marker='o', linestyle='-', color='green')
#         ax2.set_title(f'{project.upper()} - 累计事件总量')
#         ax2.set_xlabel('日期')
#         ax2.set_ylabel('累计事件数量')
#         ax2.grid(True)
#         ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#         plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
#         # 创建一个堆叠条形图来显示每天各类事件的分布
#         event_pivot = df.pivot_table(index='date', columns='event_type', values='event_count', aggfunc='sum', fill_value=0)
        
#         # 绘制堆叠条形图
#         fig2, ax3 = plt.subplots(figsize=(14, 8))
#         event_pivot.plot(kind='bar', stacked=True, ax=ax3)
#         ax3.set_title(f'{project.upper()} - 每日各类事件分布')
#         ax3.set_xlabel('日期')
#         ax3.set_ylabel('事件数量')
#         ax3.legend(title='事件类型', bbox_to_anchor=(1.05, 1), loc='upper left')
#         plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
#         # 生成统计表格
#         daily_event_stats = df.groupby(['date', 'event_type'])['event_count'].sum().reset_index()
#         daily_stats_with_total = daily_event_stats.pivot_table(index='date', columns='event_type', values='event_count', aggfunc='sum', fill_value=0)
#         daily_stats_with_total['All_events'] = daily_stats_with_total.sum(axis=1)
        
#         # 打印统计结果（只显示前5行和后5行）
#         print("\n每日各类事件统计 (前5行):")
#         print(daily_stats_with_total.head())
#         print("...")
#         print(daily_stats_with_total.tail())
        
#         # 调整布局
#         plt.tight_layout()
        
#         # 保存统计结果到CSV
#         stats_output = f'/home/lab0/survival_diffusion_github/Ethereum/{project}_event_daily_stats_2025_12_31.csv'
#         daily_stats_with_total.to_csv(stats_output)
#         print(f"✅ 统计结果已保存: {stats_output}")
        
#         # 保存图表
#         trend_output = f'/home/lab0/survival_diffusion_github/Ethereum/{project}_event_daily_trend_2025_12_31.png'
#         fig.savefig(trend_output, bbox_inches='tight')
#         print(f"✅ 趋势图已保存: {trend_output}")
        
#         dist_output = f'/home/lab0/survival_diffusion_github/Ethereum/{project}_event_daily_distribution_2025_12_31.png'
#         fig2.savefig(dist_output, bbox_inches='tight')
#         print(f"✅ 分布图已保存: {dist_output}")
        
#         # 关闭图形，释放内存
#         plt.close(fig)
#         plt.close(fig2)
        
#         print(f"✅ {project.upper()} 处理完成！")
        
#     except Exception as e:
#         print(f"❌ 处理 {project.upper()} 时出错: {str(e)}")
#         # 确保关闭可能打开的图形
#         plt.close('all')
#         continue

# print(f"\n{'='*80}")
# print("🎊 所有项目批量处理完成！")
# print(f"{'='*80}")