# 改进后的BTC
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# ===================================================================
# 文件路径定义
# ===================================================================

# BTC 主链
BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv"

# ETH 竞争链
ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all_2025_12_31.csv"

# 竞争链 - 格式1: ?_events_all_2025_12_31.csv
CHAINS_FORMAT1 = ['bitcoincash', 'bitcoinsv', 'bitcoingpu', 'bitcoincashnode', 'parity', 
                  'lightningnetwork', 'rootstock', 'stacks', 'bob', 'zcash', 
                  'solana', 'tron', 'bnb']

# 竞争链 - 格式2: ?_events_timeline_unified_all_2025_12_31.csv
CHAINS_FORMAT2 = ['lbtc', 'btcd', 'bcoin', 'litecoin', 'dogecoin', 'monero']

# ===================================================================
# 构建项目标签映射
# ===================================================================

PROJECT_LABELS = {}

# 添加 BTC 主链
PROJECT_LABELS[BTC_PATH] = 'BTC'

# 添加 ETH 竞争链
PROJECT_LABELS[ETH_PATH] = 'ETH'

# 添加格式1的竞争链
for chain in CHAINS_FORMAT1:
    path = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_events_all_2025_12_31.csv"
    # 创建友好的标签
    label = chain.upper() if len(chain) <= 5 else chain.replace('_', '').title()
    PROJECT_LABELS[path] = label

# 添加格式2的竞争链
for chain in CHAINS_FORMAT2:
    path = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_events_timeline_unified_all_2025_12_31.csv"
    label = chain.upper() if len(chain) <= 5 else chain.capitalize()
    PROJECT_LABELS[path] = label

# ===================================================================
# 显示将要加载的项目
# ===================================================================

print("="*80)
print(f"📋 将分析 {len(PROJECT_LABELS)} 个项目:")
print("="*80)
for i, (path, label) in enumerate(PROJECT_LABELS.items(), 1):
    filename = os.path.basename(path)
    print(f"  {i:2d}. {label:<20} <- {filename}")
print("="*80)

# ===================================================================
# 读取所有数据
# ===================================================================

print("\nLoading all project data...")
print("="*80)

dfs = []
loaded_projects = []
skipped_projects = []

for path, label in PROJECT_LABELS.items():
    try:
        # 检查文件是否存在
        if not os.path.exists(path):
            print(f"⚠️  {label:<20} 文件不存在，跳过")
            skipped_projects.append(label)
            continue
        
        # 读取数据
        df = pd.read_csv(path)
        df['project'] = label
        dfs.append(df)
        loaded_projects.append(label)
        print(f"✅ {label:<20} {len(df):>10,} 条记录")
        
    except Exception as e:
        print(f"❌ {label:<20} 加载失败: {str(e)}")
        skipped_projects.append(label)
        continue

print("="*80)
print(f"📊 加载汇总:")
print(f"  ✅ 成功: {len(loaded_projects)} 个项目")
print(f"  ⚠️  跳过: {len(skipped_projects)} 个项目")

if skipped_projects:
    print(f"\n跳过的项目: {', '.join(skipped_projects)}")

if not dfs:
    raise ValueError("❌ 错误：没有成功加载任何数据文件！")

# 合并所有数据
df_all = pd.concat(dfs, ignore_index=True)
print(f"\n✅ 合并后总记录数: {len(df_all):,}")
print(f"✅ 包含项目: {', '.join(sorted(loaded_projects))}")
print("="*80)

# ===================================================================
# 关键列检查
# ===================================================================

required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
missing = [col for col in required_cols if col not in df_all.columns]
if missing:
    raise ValueError(f"Missing columns in combined data: {missing}")

print(f"\n✅ 所有必需列都存在: {', '.join(required_cols)}")

# ===================================================================
# 数据预处理
# ===================================================================

print("\n处理数据...")

# 时间解析
df_all['created_at'] = pd.to_datetime(df_all['created_at'])

# 用户唯一标识：优先 actor_id，其次 actor_login
df_all['user_id'] = df_all['actor_id'].fillna(df_all['actor_login'])

# 按用户和时间排序
df_all = df_all.sort_values(['user_id', 'created_at']).reset_index(drop=True)

print(f"✅ 识别到 {df_all['user_id'].nunique():,} 个唯一用户")
print(f"✅ 时间范围: {df_all['created_at'].min()} 至 {df_all['created_at'].max()}")

# ===================================================================
# (1) 生成全局跨链迁移路径（去重同项目重复）
# ===================================================================

def get_global_migration_sequence(group):
    """
    生成用户的去重跨链路径
    只保留项目切换点
    """
    seq = group.sort_values('created_at')
    projects = seq['project'].tolist()
    times = seq['created_at'].tolist()
    
    # 只保留项目切换
    clean_projects = []
    clean_times = []
    prev_proj = None
    for proj, time in zip(projects, times):
        if proj != prev_proj:
            clean_projects.append(proj)
            clean_times.append(time)
            prev_proj = proj
    
    if not clean_projects:
        return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
                         'first_time': None, 'last_project': None, 'last_time': None,
                         'contribution_count': 0})
    
    path_detail = list(zip(clean_projects, clean_times))
    
    return pd.Series({
        'path_detail': path_detail,
        'path_str': '-'.join(clean_projects),
        'first_project': clean_projects[0],
        'first_time': clean_times[0],
        'last_project': clean_projects[-1],
        'last_time': clean_times[-1],
        'contribution_count': len(seq)
    })

print("\n" + "="*80)
print("Generating global cross-chain migration paths...")
print("="*80)

user_paths = df_all.groupby('user_id').apply(get_global_migration_sequence).reset_index()

# 只保留包含 BTC 的路径
btc_users = user_paths[user_paths['path_str'].str.contains('BTC', na=False)].copy()
print(f"✅ Users with BTC in path: {len(btc_users):,}")
print(f"✅ 占总用户比例: {len(btc_users)/len(user_paths)*100:.2f}%")

# 保存全局路径（供检查）
output_path = '/home/lab0/survival_diffusion_github/sensitivity/outflow_window/btc_global_all_chains_user_paths_enhanced_1080.csv'
btc_users.to_csv(output_path, index=False)
print(f"✅ 用户路径已保存: {output_path}")

# ===================================================================
# (2) 新逻辑：首次进入BTC和永久离开BTC
# ===================================================================

# 定义截止日期和永久迁出判定窗口
CUTOFF_DATE = datetime(2025, 12, 31).date()
PERMANENT_EXIT_DAYS = 1080

print("\n" + "="*80)
print("Analyzing migration events...")
print("="*80)
print(f"📅 截止日期: {CUTOFF_DATE}")
print(f"⏰ 永久迁出判定窗口: {PERMANENT_EXIT_DAYS} 天")

migration_events = []

for _, row in btc_users.iterrows():
    user = row['user_id']
    detail = row['path_detail']  # [(proj, time), ...]
    
    if not detail:
        continue
    
    # 转换为列表方便索引
    projects = [p for p, _ in detail]
    times = [t for _, t in detail]
    
    # 找到所有 BTC 的位置索引
    btc_indices = [i for i, p in enumerate(projects) if p == 'BTC']
    
    if not btc_indices:
        continue
    
    # ===================================================================
    # 迁入逻辑：首次进入 BTC
    # ===================================================================
    first_btc_idx = btc_indices[0]  # 第一个BTC的位置
    
    if first_btc_idx > 0:
        # BTC之前存在其他链 → 视为迁入
        prev_proj = projects[first_btc_idx - 1]
        in_time = times[first_btc_idx]  # 第一个BTC的时间
        in_date = in_time.date()
        
        migration_events.append({
            'user_id': user,
            'type': f'in_from_{prev_proj}',
            'from_chain': prev_proj,
            'to_chain': 'BTC',
            'date': in_date,
            'event_type': 'inflow'
        })
    else:
        # BTC为路径起点 → 首次用户，不计入迁入
        pass
    
    # ===================================================================
    # 迁出逻辑：永久离开 BTC
    # ===================================================================
    last_btc_idx = btc_indices[-1]  # 最后一个BTC的位置
    
    # 检查路径是否以非BTC链结尾
    if last_btc_idx < len(projects) - 1:
        # 路径以非BTC结尾
        next_proj = projects[last_btc_idx + 1]  # 最后一个BTC之后紧邻的链
        out_time = times[last_btc_idx + 1]  # 该链的首次出现时间
        out_date = out_time.date()
        
        # 检查是否距离截止日期至少30天
        days_to_cutoff = (CUTOFF_DATE - out_date).days
        
        if days_to_cutoff >= PERMANENT_EXIT_DAYS:
            # 视为永久迁出
            migration_events.append({
                'user_id': user,
                'type': f'out_to_{next_proj}',
                'from_chain': 'BTC',
                'to_chain': next_proj,
                'date': out_date,
                'event_type': 'outflow'
            })
        else:
            # 距离截止日期不足30天 → 不算永久迁出（可能还会回来）
            pass
    else:
        # 路径以BTC结尾 → 视为多归属或持续活跃，不计为迁出
        pass

# 构建DataFrame
df_migration = pd.DataFrame(migration_events)

if df_migration.empty:
    print("⚠️ 没有检测到任何迁入/迁出事件！")
    df_migration = pd.DataFrame(columns=['user_id', 'type', 'from_chain', 'to_chain', 'date', 'event_type'])
else:
    # 去重：同一个用户同一天同一类型只计一次
    df_migration = df_migration.drop_duplicates(subset=['user_id', 'type', 'date'])

print(f"\n📊 迁移事件统计:")
print(f"  总迁入事件: {len(df_migration[df_migration['event_type'] == 'inflow']):,}")
print(f"  总迁出事件: {len(df_migration[df_migration['event_type'] == 'outflow']):,}")

# ===================================================================
# (3) 按链别统计每日迁入/迁出人数
# ===================================================================

if not df_migration.empty:
    # 分离迁入和迁出
    df_in = df_migration[df_migration['event_type'] == 'inflow']
    df_out = df_migration[df_migration['event_type'] == 'outflow']
    
    # 每日迁入统计
    if not df_in.empty:
        daily_in = df_in.groupby(['date', 'type']).size().unstack(fill_value=0)
        daily_in.columns = [col for col in daily_in.columns]
        daily_in['total_in'] = daily_in.sum(axis=1)
    else:
        daily_in = pd.DataFrame()
    
    # 每日迁出统计
    if not df_out.empty:
        daily_out = df_out.groupby(['date', 'type']).size().unstack(fill_value=0)
        daily_out.columns = [col for col in daily_out.columns]
        daily_out['total_out'] = daily_out.sum(axis=1)
    else:
        daily_out = pd.DataFrame()
    
    # 合并
    if not daily_in.empty and not daily_out.empty:
        daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
    elif not daily_in.empty:
        daily_summary = daily_in.fillna(0).astype(int)
    elif not daily_out.empty:
        daily_summary = daily_out.fillna(0).astype(int)
    else:
        daily_summary = pd.DataFrame()
    
    if not daily_summary.empty:
        daily_summary = daily_summary.sort_index()
else:
    daily_summary = pd.DataFrame()

# ===================================================================
# (4) 保存结果
# ===================================================================

base_out = '/home/lab0/survival_diffusion_github/sensitivity/outflow_window/btc_global_migration_enhanced_1080'

if not daily_summary.empty:
    daily_summary.to_csv(f'{base_out}_daily_strict_rules.csv')
    print(f"\n✅ 每日汇总已保存: {base_out}_daily_strict_rules.csv")
    print("\nDaily migration summary (tail 20):")
    print(daily_summary.tail(20))
else:
    print("\n⚠️ 没有每日汇总数据可保存")

if not df_migration.empty:
    df_migration.to_csv(f'{base_out}_all_events.csv', index=False)
    print(f"✅ 所有事件已保存: {base_out}_all_events.csv")
else:
    print("⚠️ 没有迁移事件可保存")

print("\n" + "="*80)
print("🎉 All done! Files saved:")
print(f" - {base_out}_daily_strict_rules.csv")
print(f" - {base_out}_all_events.csv")
print(f" - btc_global_all_chains_user_paths_enhanced.csv")
print("="*80)

# ===================================================================
# (5) 额外诊断信息
# ===================================================================

print("\n" + "="*80)
print("📊 迁移模式诊断")
print("="*80)

if not df_migration.empty:
    # 迁入来源分布
    print("\n🔵 迁入来源分布:")
    if 'from_chain' in df_migration.columns:
        in_sources = df_migration[df_migration['event_type'] == 'inflow']['from_chain'].value_counts()
        for chain, count in in_sources.items():
            print(f"  从 {chain:<20} 迁入: {count:>6,} 人")
    
    # 迁出目标分布
    print("\n🔴 迁出目标分布:")
    if 'to_chain' in df_migration.columns:
        out_targets = df_migration[df_migration['event_type'] == 'outflow']['to_chain'].value_counts()
        for chain, count in out_targets.items():
            print(f"  迁出到 {chain:<20}: {count:>6,} 人")
    
    # 时间分布
    print("\n📅 时间分布:")
    inflow_dates = df_migration[df_migration['event_type'] == 'inflow']['date']
    outflow_dates = df_migration[df_migration['event_type'] == 'outflow']['date']
    
    if not inflow_dates.empty:
        print(f"  最早迁入: {inflow_dates.min()}")
        print(f"  最晚迁入: {inflow_dates.max()}")
    else:
        print(f"  无迁入事件")
    
    if not outflow_dates.empty:
        print(f"  最早迁出: {outflow_dates.min()}")
        print(f"  最晚迁出: {outflow_dates.max()}")
    else:
        print(f"  无迁出事件")

# 路径模式统计
print("\n📊 路径模式统计:")
print(f"  总用户数（包含BTC）: {len(btc_users):,}")
print(f"  路径以BTC开始的用户: {len(btc_users[btc_users['first_project'] == 'BTC']):,}")
print(f"  路径以BTC结束的用户: {len(btc_users[btc_users['last_project'] == 'BTC']):,}")

# 常见路径模式
print("\n最常见的路径模式（Top 10）:")
top_paths = btc_users['path_str'].value_counts().head(10)
for i, (path, count) in enumerate(top_paths.items(), 1):
    print(f"  {i:2d}. {path:<50} {count:>6,} 人")

print("\n" + "="*80)
print("✅ 分析完成！")
print("="*80)