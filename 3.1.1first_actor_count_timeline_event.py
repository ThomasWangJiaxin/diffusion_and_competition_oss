import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import os

# 路径配置
FILE_PATH_INPUT = '/home/lab0/survival_diffusion_github/Bitcoin/monero_first_events_by_type_timeline_unified_2025_12_31.csv'
OUTPUT_DIR = '/home/lab0/survival_diffusion_github/Bitcoin/'

# --- 身份解析与筛选 ---
print("⏳ 正在读取数据并尝试修复 CSV 解析错误...")
df = pd.read_csv(
    FILE_PATH_INPUT, 
    parse_dates=['created_at'],
    # 强制使用 Python 引擎来处理复杂的引用和分隔符问题
    engine='python',
    # 强制使用逗号作为分隔符
    sep=',',
    # 设置严格的引号处理，忽略错误的换行符
    on_bad_lines='skip' 
)

# 1. 核心步骤：找到每个 stable_actor_id 对应的最早一行记录
# 确保数据按时间排序，然后对 stable_actor_id 去重，保留第一次出现的行（即最早的记录）
df_first_event = df.sort_values(by='created_at', ascending=True).drop_duplicates(
    subset=['stable_actor_id'], 
    keep='first'
)

# 2. 验证记录数
final_record_count = len(df_first_event)
unique_contributors = df_first_event['stable_actor_id'].nunique()

print(f"✅ 最终筛选出的记录数: {final_record_count:,}")
print(f"✅ 不重复的用户数: {unique_contributors:,}")

if final_record_count == unique_contributors:
    print("🎉 记录数与不重复用户数已匹配，筛选正确。")
else:
    print(f"⚠️ 警告：记录数 ({final_record_count}) 仍与不重复用户数 ({unique_contributors}) 不匹配。")


# --- 后续处理与绘图 ---

# 调整列顺序
cols = df_first_event.columns.tolist()
cols.insert(1, cols.pop(cols.index('created_at')))
df_first_event = df_first_event[cols]

# 保存完整的“首次行为事件”
df_first_event.to_csv(os.path.join(OUTPUT_DIR, 'monero_first_actor_full_event_timeline_event_2025_12_31.csv'), index=False)

# 每天新增用户数计算 (保持原逻辑)
df_first_event['date'] = df_first_event['created_at'].dt.date
daily_new_devs = df_first_event.groupby('date')['stable_actor_id'].count().reset_index()
daily_new_devs.columns = ['date', 'new_developers']
daily_new_devs['date'] = pd.to_datetime(daily_new_devs['date'])

# ... (后续的每日新增和累计用户计算代码保持不变) ...

# 自动补全所有日期范围，空天数填 0
full_range = pd.date_range(start=daily_new_devs['date'].min(), end=daily_new_devs['date'].max())
daily_new_devs = daily_new_devs.set_index('date').reindex(full_range, fill_value=0).reset_index()
daily_new_devs.columns = ['date', 'new_developers']

# 添加累计用户数列
daily_new_devs['cum_users'] = daily_new_devs['new_developers'].cumsum()

# 保存结果
daily_new_devs.to_csv(os.path.join(OUTPUT_DIR, 'monero_first_actor_count_timeline_event_2025_12_31.csv'), index=False)

# 绘图 (保持原逻辑)
sns.set(style='whitegrid')
plt.figure(figsize=(14, 6))
sns.lineplot(data=daily_new_devs, x='date', y='new_developers', marker='o', linewidth=2)
plt.title('Daily Number of New Developers (First-Ever Behavior)', fontsize=14)
plt.xlabel('Date')
plt.ylabel('Number of New Developers')

ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'monero_first_actor_count_timeline_event_2025_12_31.png'), dpi=300)
plt.show()

# -----2024-12-31
# ✅ BTC最终筛选出的记录数: 121,995
# ✅ 不重复的用户数: 121,995
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ BIPs最终筛选出的记录数: 16,534
# ✅ 不重复的用户数: 16,534
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ ETH最终筛选出的记录数: 76,357
# ✅ 不重复的用户数: 76,357
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ Litecoin最终筛选出的记录数: 10,852
# ✅ 不重复的用户数: 10,852
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# --------- 2025-12-31
# ✅ Bitcoin最终筛选出的记录数: 129,030
# ✅ 不重复的用户数: 129,030
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ BIPs最终筛选出的记录数: 17,601
# ✅ 不重复的用户数: 17,601
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ ETH最终筛选出的记录数: 79,735
# ✅ 不重复的用户数: 79,735
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ Litecoin最终筛选出的记录数: 11,115
# ✅ 不重复的用户数: 11,115
# 🎉 记录数与不重复用户数已匹配，筛选正确。

# ✅ Dogecoin最终筛选出的记录数: 21,774
# ✅ 不重复的用户数: 21,774
# 🎉 记录数与不重复用户数已匹配，筛选正确。
