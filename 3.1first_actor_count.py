import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import os

# 读取数据
df = pd.read_csv('/home/lab0/survival_diffusion_github/Ethereum/ronin_first_events_by_type_2025_12_31.csv', parse_dates=['created_at'])

# 找到每个 actor_id 最早出现时间
first_created = df.groupby('actor_id')['created_at'].min().reset_index()
first_created.columns = ['actor_id', 'first_created_at']

# 将 first_created 与原始 df 合并，只保留每个 actor 最早时间的那一行完整信息
df_first_event = pd.merge(df, first_created, on='actor_id')
df_first_event = df_first_event[df_first_event['created_at'] == df_first_event['first_created_at']].copy()

# 有些 actor_id 在同一时间做了多个行为，我们保留其中一条（只保留最早的唯一行）
df_first_event = df_first_event.sort_values('created_at').drop_duplicates('actor_id')

# 获取最终记录数
final_record_count = len(df_first_event)

# 添加日期字段
df_first_event['date'] = df_first_event['created_at'].dt.date

# 保存完整信息
df_first_event = df_first_event.sort_values('date')

# 调整列顺序：将 'created_at' 放在第二列
cols = list(df_first_event.columns)
# 检查 'created_at' 是否在列表中，防止重复 pop 导致错误
if 'created_at' in cols:
    cols.insert(1, cols.pop(cols.index('created_at')))
df_first_event = df_first_event[cols]

# 定义输出路径
output_file_path = '/home/lab0/survival_diffusion_github/Ethereum/ronin_first_actor_full_event_2025_12_31.csv'

# 保存完整的“首次行为事件”
df_first_event.to_csv(output_file_path, index=False)

# **【新增输出记录数】**
print(f"🎉 文件 '{output_file_path}' 已保存。")
print(f"✅ 最终筛选出的【每个用户首次行为】记录总数: {final_record_count:,}")
print(f"✅ 不重复用户总数 (应与记录总数相等): {df_first_event['actor_id'].nunique():,}")


# 每天新增用户数
daily_new_devs = df_first_event.groupby('date')['actor_id'].count().reset_index()
daily_new_devs.columns = ['date', 'new_developers']
daily_new_devs['date'] = pd.to_datetime(daily_new_devs['date'])

# 自动补全所有日期范围，空天数填 0
full_range = pd.date_range(start=daily_new_devs['date'].min(), end=daily_new_devs['date'].max())
daily_new_devs = daily_new_devs.set_index('date').reindex(full_range, fill_value=0).reset_index()
daily_new_devs.columns = ['date', 'new_developers']

# 添加累计用户数列
daily_new_devs['cum_users'] = daily_new_devs['new_developers'].cumsum()

# 保存结果
daily_new_devs.to_csv('/home/lab0/survival_diffusion_github/Ethereum/ronin_first_actor_count_2025_12_31.csv', index=False)

# 绘图
sns.set(style='whitegrid')
plt.figure(figsize=(14, 6))
sns.lineplot(data=daily_new_devs, x='date', y='new_developers', marker='o', linewidth=2)
plt.title('Daily Number of New Developers (First-Ever Behavior)', fontsize=14)
plt.xlabel('Date')
plt.ylabel('Number of New Developers')

# 设置横轴为季度起始月份
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('/home/lab0/survival_diffusion_github/Ethereum/ronin_first_actor_count_2025_12_31.png', dpi=300)
plt.show()


# 批量
# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# import matplotlib.dates as mdates
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

# # bitcoincash, bitcoinsv, bitcoingpu, bitcoincashnode, parity, lightningnetwork, rootstock, stacks, bob, zcash, solanaold, solananew, tron, bnb
# projects = ['bitcoincash', 'bitcoinsv', 'bitcoingpu', 'bitcoincashnode', 'parity', 'lightningnetwork', 'rootstock', 'stacks', 'bob', 'zcash', 'solanaold', 'solananew', 'tron', 'bnb']
            
# # 批量处理所有项目
# for project in projects:
#     try:
#         print(f"\n{'='*80}")
#         print(f"正在处理项目: {project.upper()}")
#         print(f"{'='*80}")
        
#         # 读取数据
#         input_file = f'/home/lab0/survival_diffusion_github/Bitcoin/{project}_first_events_by_type_2025_12_31.csv'
        
#         # 检查文件是否存在
#         if not os.path.exists(input_file):
#             print(f"⚠️  文件不存在，跳过: {input_file}")
#             continue
            
#         df = pd.read_csv(input_file, parse_dates=['created_at'])
        
#         # 找到每个 actor_id 最早出现时间
#         first_created = df.groupby('actor_id')['created_at'].min().reset_index()
#         first_created.columns = ['actor_id', 'first_created_at']
        
#         # 将 first_created 与原始 df 合并，只保留每个 actor 最早时间的那一行完整信息
#         df_first_event = pd.merge(df, first_created, on='actor_id')
#         df_first_event = df_first_event[df_first_event['created_at'] == df_first_event['first_created_at']].copy()
        
#         # 有些 actor_id 在同一时间做了多个行为，我们保留其中一条（只保留最早的唯一行）
#         df_first_event = df_first_event.sort_values('created_at').drop_duplicates('actor_id')
        
#         # 获取最终记录数
#         final_record_count = len(df_first_event)
        
#         # 添加日期字段
#         df_first_event['date'] = df_first_event['created_at'].dt.date
        
#         # 保存完整信息
#         df_first_event = df_first_event.sort_values('date')
        
#         # 调整列顺序：将 'created_at' 放在第二列
#         cols = list(df_first_event.columns)
#         if 'created_at' in cols:
#             cols.insert(1, cols.pop(cols.index('created_at')))
#         df_first_event = df_first_event[cols]
        
#         # 定义输出路径
#         output_file_path = f'/home/lab0/survival_diffusion_github/Bitcoin/{project}_first_actor_full_event_2025_12_31.csv'
        
#         # 保存完整的"首次行为事件"
#         df_first_event.to_csv(output_file_path, index=False)
        
#         print(f"🎉 文件 '{output_file_path}' 已保存。")
#         print(f"✅ 最终筛选出的【每个用户首次行为】记录总数: {final_record_count:,}")
#         print(f"✅ 不重复用户总数 (应与记录总数相等): {df_first_event['actor_id'].nunique():,}")
        
#         # 每天新增用户数
#         daily_new_devs = df_first_event.groupby('date')['actor_id'].count().reset_index()
#         daily_new_devs.columns = ['date', 'new_developers']
#         daily_new_devs['date'] = pd.to_datetime(daily_new_devs['date'])
        
#         # 自动补全所有日期范围，空天数填 0
#         full_range = pd.date_range(start=daily_new_devs['date'].min(), end=daily_new_devs['date'].max())
#         daily_new_devs = daily_new_devs.set_index('date').reindex(full_range, fill_value=0).reset_index()
#         daily_new_devs.columns = ['date', 'new_developers']
        
#         # 添加累计用户数列
#         daily_new_devs['cum_users'] = daily_new_devs['new_developers'].cumsum()
        
#         # 保存结果
#         count_output = f'/home/lab0/survival_diffusion_github/Bitcoin/{project}_first_actor_count_2025_12_31.csv'
#         daily_new_devs.to_csv(count_output, index=False)
#         print(f"✅ 每日新增用户统计已保存: {count_output}")
        
#         # 绘图
#         sns.set(style='whitegrid')
#         plt.figure(figsize=(14, 6))
#         sns.lineplot(data=daily_new_devs, x='date', y='new_developers', marker='o', linewidth=2)
#         plt.title(f'Daily Number of New Developers - {project.upper()} (First-Ever Behavior)', fontsize=14)
#         plt.xlabel('Date')
#         plt.ylabel('Number of New Developers')
        
#         # 设置横轴为季度起始月份
#         ax = plt.gca()
#         ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
#         plt.xticks(rotation=45)
        
#         plt.tight_layout()
        
#         # 保存图片
#         plot_output = f'/home/lab0/survival_diffusion_github/Bitcoin/{project}_first_actor_count_2025_12_31.png'
#         plt.savefig(plot_output, dpi=300)
#         plt.close()  # 关闭图形，避免内存占用
#         print(f"✅ 图表已保存: {plot_output}")
        
#         print(f"✅ {project.upper()} 处理完成！")
        
#     except Exception as e:
#         print(f"❌ 处理 {project.upper()} 时出错: {str(e)}")
#         continue

# print(f"\n{'='*80}")
# print("🎊 所有项目批量处理完成！")
# print(f"{'='*80}")