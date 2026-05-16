import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import seaborn as sns 

# --- 1. 配置和数据加载 ---

# 请确保文件和路径存在
FILE_PATH = '/home/lab0/survival_diffusion_github/Bitcoin/monero_events_timeline_unified_all_2025_12_31.csv'
SAVE_FOLDER = '/home/lab0/survival_diffusion_github/Bitcoin'

# 检查 SAVE_FOLDER 是否存在
os.makedirs(SAVE_FOLDER, exist_ok=True)

# 加载数据（假设数据已准备好）
try:
    df = pd.read_csv(FILE_PATH, low_memory=False)
except FileNotFoundError:
    print(f"❌ 错误：文件未找到于 {FILE_PATH}。请检查路径。")
    exit()

print(f"✅ 成功加载 {len(df)} 条记录。")

# --- 【新增代码块：打印所有 Event Types】 ---
if 'event_type' in df.columns:
    unique_event_types = df['event_type'].unique().tolist()
    unique_event_types.sort() # 对类型进行排序以方便查看
    
    print("\n--- 数据集包含的 Event 类型 ---")
    print(f"总计 {len(unique_event_types)} 种不重复的事件类型。")
    print(", ".join(unique_event_types))
    print("----------------------------------\n")
else:
    print("⚠️ 警告：数据集中未找到 'event_type' 列，无法打印事件类型。")
# -----------------------------------------------


# --- 2. 核心数据处理 ---

# 确保 created_at 字段是 datetime 类型
df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

# 提取日期部分（转换为 datetime 类型以便后续绘图）
df['date'] = df['created_at'].dt.date
df['date'] = pd.to_datetime(df['date']) # 转换为 datetime 对象

# 按照日期和 event_type 计算每个类型的数量
event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

# 保存各类事件每日计数结果到 CSV
output_path_per_day = os.path.join(SAVE_FOLDER, 'monero_event_count_per_day_timeline_event_2025_12_31.csv')
event_count_per_day.to_csv(output_path_per_day, index=False)
print(f"✅ 各类事件每日计数已保存到 {output_path_per_day}")


# --- 3. 计算每日总量和累计量 ---

# 按日期分组并计算每天的总事件数 (使用 event_count_per_day 作为源)
daily_totals = event_count_per_day.groupby('date')['event_count'].sum().reset_index()
daily_totals.columns = ['date', 'total_events']

# 计算累计总事件数
daily_totals['cumulative_events'] = daily_totals['total_events'].cumsum()


# --- 4. 统计表格生成 (用于打印和保存) ---

# 创建用于堆叠图和统计的透视表 (index='date', columns='event_type')
event_pivot = event_count_per_day.pivot_table(
    index='date', 
    columns='event_type', 
    values='event_count', 
    aggfunc='sum', 
    fill_value=0
)
daily_stats_with_total = event_pivot.copy()
daily_stats_with_total['All_events'] = daily_totals['total_events'].values # 从 daily_totals 中引入总数

# 打印统计结果
print("\n每日各类事件统计:")
print(daily_stats_with_total)

# 保存统计结果到CSV
output_path_stats = os.path.join(SAVE_FOLDER, 'monero_event_daily_stats_timeline_event_2025_12_31.csv')
daily_stats_with_total.to_csv(output_path_stats)
print(f"✅ 统计结果已保存到 {output_path_stats}")


# --- 5. 绘图与保存 ---

# 设置绘图风格
sns.set(style='whitegrid')

# 创建第一个图表：每日/累计趋势图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 第一个子图：每天的事件总量
ax1.plot(daily_totals['date'], daily_totals['total_events'], marker='o', linestyle='-', label='Daily Total')
ax1.set_title('每日事件总量趋势')
ax1.set_xlabel('日期')
ax1.set_ylabel('事件数量')
ax1.grid(True)
# 格式化日期
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 第二个子图：累计事件总量
ax2.plot(daily_totals['date'], daily_totals['cumulative_events'], marker='o', linestyle='-', color='green', label='Cumulative Total')
ax2.set_title('累计事件总量趋势')
ax2.set_xlabel('日期')
ax2.set_ylabel('累计事件数量')
ax2.grid(True)
# 格式化日期
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
fig.savefig(os.path.join(SAVE_FOLDER, 'monero_event_daily_trend_timeline_event_2025_12_31.png'), bbox_inches='tight')
print(f"✅ 趋势图已保存。")


# 创建第二个图表：堆叠条形图（每日各类事件分布）
fig2, ax3 = plt.subplots(figsize=(14, 8))
event_pivot.plot(kind='bar', stacked=True, ax=ax3, width=1.0) # width=1.0 使柱子间无缝连接

ax3.set_title('每日各类事件分布')
ax3.set_xlabel('日期')
ax3.set_ylabel('事件数量')
ax3.legend(title='事件类型', bbox_to_anchor=(1.05, 1), loc='upper left') # 将图例移到外部
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha="right")

plt.tight_layout()
fig2.savefig(os.path.join(SAVE_FOLDER, 'monero_event_daily_distribution_timeline_event_2025_12_31.png'), bbox_inches='tight')
print(f"✅ 分布图已保存。")

plt.show()

# --- 数据集包含的 Event 类型 ---
# 总计 15 种不重复的事件类型。
# CommitCommentEvent, CreateEvent, DeleteEvent, DownloadEvent, Event, ForkEvent, GollumEvent, IssueCommentEvent, IssuesEvent, PullRequestEvent, PullRequestReviewCommentEvent, PullRequestReviewEvent, PushEvent, ReleaseEvent, WatchEvent
# 2015年后（没有 DownloadEvent, Event, GollumEvent）
# 2015年前（没有PullRequestReviewEvent, ReleaseEvent）：CommitCommentEvent, PullRequestReviewCommentEvent, GollumEvent, PullRequestEvent, ForkEvent, IssueCommentEvent, WatchEvent, IssuesEvent, CreateEvent, PushEvent, DeleteEvent, Event, DownloadEvent

# --- 数据集包含的 Bips Event 类型 ---
# 总计 12 种不重复的事件类型。
# CommitCommentEvent, CreateEvent, DeleteEvent, ForkEvent, GollumEvent, IssueCommentEvent, IssuesEvent, PullRequestEvent, PullRequestReviewCommentEvent, PullRequestReviewEvent, PushEvent, WatchEvent
# 2015年后（没有IssuesEvent）：流程淘汰： 社区决定将 Issues 机制排除在协议管理之外。正式的提案必须通过 Pull Request (PR) 机制提交，以确保格式和版本控制的严谨性。
# 2015年前（没有CommitCommentEvent、GollumEvent、PullRequestReviewEvent): PullRequestEvent, PullRequestReviewCommentEvent, ForkEvent, CreateEvent, PushEvent, WatchEvent, IssueCommentEvent, DeleteEvent, IssuesEvent
# 在 2015 年之前，GitHub 没有独立的 PullRequestReviewEvent 类型。

# --- 数据集包含的 Eth Event 类型 ---
# 总计 14 种不重复的事件类型。
# CommitCommentEvent, CreateEvent, DeleteEvent, ForkEvent, GollumEvent, IssueCommentEvent, IssuesEvent, MemberEvent, PullRequestEvent, PullRequestReviewCommentEvent, PullRequestReviewEvent, PushEvent, ReleaseEvent, WatchEvent
# 2015后14种类型：以上全部
# 2015前12种类型（缺了MemberEvent, PullRequestReviewEvent）：CommitCommentEvent, PullRequestEvent, ForkEvent, IssuesEvent, CreateEvent, PushEvent, WatchEvent, PullRequestReviewCommentEvent, GollumEvent, ReleaseEvent, DeleteEvent, IssueCommentEvent
# 1. PullRequestReviewEvent (PR 审查事件)
# 缺失原因：GitHub API 的演变

# 在 2015 年之前，GitHub 没有独立的 PullRequestReviewEvent 类型。

# 在早期，所有关于 PR 的评论和审查意见，都被归类在 PullRequestReviewCommentEvent 中（即针对 PR 中特定代码行的评论）。

# GitHub 在 2015 年左右引入了 "PR Review" 机制，允许贡献者进行正式的“批准”（Approve）、“要求更改”（Request Changes）或“评论”（Comment）的状态提交。只有当这个机制推出后，PullRequestReviewEvent 这个独立的事件类型才出现并被 Timeline API 捕获。

# 因此，这不是 Ethereum 项目没有进行审查，而是 API 缺乏细分捕获。

# 2. MemberEvent (成员变动事件)
# 缺失原因：项目组织结构和 API 权限

# MemberEvent 表示 用户被添加或移除组织/仓库成员的权限变动。

# 权限问题： 早期 GitHub Archive 对权限相关的事件捕获可能较为保守，或者只对公共事件开放。

# 活动集中： Ethereum 在早期（2015 年前）可能由少数核心团队成员以非正式的方式管理权限。随着项目规模扩大和 DAO/基金会的建立（2015 年后），对组织成员的添加和移除（如将用户从外部贡献者提升为维护者）变得更加正式和频繁，MemberEvent 也因此成为明显的、可追踪的事件类型。

# 简而言之，它要么是 API 遗漏，要么是 2015 年前权限变动不频繁或未被公开记录。