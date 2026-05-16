# 两两配对
# 针对BTC,ETH,BCH,BSV,Litecoin,Dogecoin六大加密货币的完整事件记录文件路径如下：
# BTC完整的事件记录：/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv
# ETH完整的事件记录：/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv
# BCH完整的事件记录：/home/lab0/survival_diffusion_github/Bitcoin/bitcoinabc_events_all.csv
# BSV完整的事件记录：/home/lab0/survival_diffusion_github/Bitcoin/bitcoinsv_events_all.csv
# Litecoin完整的事件记录：/home/lab0/survival_diffusion_github/Bitcoin_compete/litecoin_events_timeline_unified_all.csv
# Dogecoin完整的事件记录：/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_events_timeline_unified_all.csv
# 请将BTC月ETH、BCH、BSV、Litecoin、Dogecoin分别组对，根据BTC中actor的行为轨迹（有actor id根据actor id来，没有actor id根据actor login）来给actor打标签。
# 以BTC和BCH为例，纯BTC新增（首次进入BTC并从来以后没有任何流动，标签为BTC_only）、纯BCH新增（首次进入BTC并从来以后没有任何流动，标签为BCH_only）、首次BTC→BCH后未回去一直在BCH，首次BCH→BTC后未回去一直在BTC，BTC回流者（首次BTC后在BCH之间来回切换但最终回归BTC后就不走了,其实可以不再区分“回流者”，回流已经隐含在 BTC_first_multihome 中），多栖者（轮流贡献多个项目，分为两种：如果一开始先在BCH→BTC→BCH…算迁入，如果一开始现在BTC→BCH→BTC…忽略流动）
# 最后计算每一天从BTC迁出（首次BTC→BCH后未回去一直在BCH，按迁去BCH的那天做准）和迁入BTC的不重复数量（首次BCH→BTC后未回去一直在BTC、首次BCH后来某一天BTC来回切换的多栖开发者，按迁来BTC的那天做准）
# BTC和ETH，BTC和BSV等类似操作

# Step 0：选定 BTC 作为 focal chain
# Step 1：基于全时间窗口，给每个 actor 打 BTC-centered 标签
# Step 2：从标签中，按时间聚合 BTC 的迁入与迁出流量
# Step 3：把“有效迁入”喂给 γ，把“永久迁出”喂给剩余市场或忽略

# BTC/BCH
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"
# BCH_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinabc_events_all.csv"

# # 读取数据
# print("Loading BTC and BCH data...")
# df_btc = pd.read_csv(BTC_PATH)
# df_bch = pd.read_csv(BCH_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df in [df_btc, df_bch]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in data: {missing}")

# # 时间解析
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])
# df_bch['created_at'] = pd.to_datetime(df_bch['created_at'])

# # 添加项目标签
# df_btc['project'] = 'BTC'
# df_bch['project'] = 'BCH'

# # 合并
# df_combined = pd.concat([df_btc, df_bch], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================

# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:  # 只在项目变化时记录
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None, 
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     # 细节路径：每步切换
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),  # 如 BTC-BCH-BTC
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)  # 原始总贡献次数
#     })

# print("Generating cross-chain migration paths (removing same-project repeats)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户（可选过滤）
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"Users with cross-chain migration: {len(cross_chain_users)}")

# # 展开细节表（每一步切换一行）
# detail_rows = []
# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': user,
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存
# df_migration_detail.to_csv('/home/lab0/survival_diffusion_github/btc_bch_migration_detail_clean.csv', index=False)
# user_paths.to_csv('/home/lab0/survival_diffusion_github/btc_bch_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv('/home/lab0/survival_diffusion_github/btc_bch_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths:")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（基于首次跨链切换）

# # 起点BTC → BCH永久不回：不计迁入，但计入迁出，日期是第一次去BCH那天 
# # 起点BCH → BTC永久不回：计入迁入，日期是第一次去BTC那天 
# # 起点BCH → BTC → 。。。→ BTC：只计第一次来BTC那天为迁入；
# # 起点BCH → BTC → 。。。→ BCH：计第一次来BTC那天为迁入，计最后一次迁出到BCH那天为迁出 
# # 起点BTC → 。。。。→ BTC ：不计迁入，也不计迁出；
# # 起点BTC → 。。。。→ BCH ：不计迁入，计最后一次迁出到BCH那天为迁出

# # ===================================================================

# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']  # [(proj, time), ...]
    
#     if len(detail) < 2:  # 没切换
#         continue
    
#     # 找第一次和最后一次切换日期
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]  # (from, to, date)
#     last_switch = switches[-1]   # (from, to, date)
    
#     # 规则应用
#     if first_proj == 'BTC':
#         # 起点BTC系列
#         if last_proj == 'BCH':
#             # 最终停在BCH → 计迁出，用最后一次离开BTC的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BCH',
#                 'date': last_switch[2]  # last_switch date
#             })
#         # 最终回BTC → 不计任何迁入/迁出
    
#     elif first_proj == 'BCH':
#         # 起点BCH系列
#         # 所有情况都计第一次来BTC那天为迁入
#         if first_switch[1] == 'BTC':  # 第一次切换目标是BTC
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_BCH',
#                 'date': first_switch[2]
#             })
        
#         # 如果最终停在BCH → 额外计最后一次离开BTC那天为迁出
#         if last_proj == 'BCH' and last_switch[0] == 'BTC':
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BCH',
#                 'date': last_switch[2]
#             })

# # 构建DataFrame并去重（防止同一用户同类型重复）
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# # 统计
# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_BCH'].groupby('date').size().rename('daily_in_from_BCH')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_BCH'].groupby('date').size().rename('daily_out_to_BCH')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv('/home/lab0/survival_diffusion_github/btc_bch_migration_strict_rules.csv')
# print(daily_summary.tail(20))  # 查看最新数据验证

# ==================================================

# BTC/ETH
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（BCH → ETH）
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"  # 改为 ETH

# # 读取数据
# print("Loading BTC and ETH data...")
# df_btc = pd.read_csv(BTC_PATH)
# df_eth = pd.read_csv(ETH_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df in [df_btc, df_eth]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in data: {missing}")

# # 时间解析
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])

# # 添加项目标签
# df_btc['project'] = 'BTC'
# df_eth['project'] = 'ETH'   # 改为 ETH

# # 合并
# df_combined = pd.concat([df_btc, df_eth], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:  # 只在项目变化时记录
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None, 
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     # 细节路径：每步切换
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),  # 如 BTC-ETH-BTC
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)  # 原始总贡献次数
#     })

# print("Generating cross-chain migration paths (removing same-project repeats)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户（可选过滤）
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"Users with cross-chain migration: {len(cross_chain_users)}")

# # 展开细节表（每一步切换一行）
# detail_rows = []
# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': user,
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名全部改为 btc_eth）
# df_migration_detail.to_csv('/home/lab0/survival_diffusion_github/btc_eth_migration_detail_clean.csv', index=False)
# user_paths.to_csv('/home/lab0/survival_diffusion_github/btc_eth_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv('/home/lab0/survival_diffusion_github/btc_eth_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths:")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']  # [(proj, time), ...]
    
#     if len(detail) < 2:  # 没切换
#         continue
    
#     # 找第一次和最后一次切换日期
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]  # (from, to, date)
#     last_switch = switches[-1]   # (from, to, date)
    
#     # 规则应用（所有 BCH → ETH 替换）
#     if first_proj == 'BTC':
#         # 起点BTC系列
#         if last_proj == 'ETH':
#             # 最终停在ETH → 计迁出，用最后一次离开BTC的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_ETH',
#                 'date': last_switch[2]
#             })
#         # 最终回BTC → 不计任何迁入/迁出
    
#     elif first_proj == 'ETH':
#         # 起点ETH系列
#         # 所有情况都计第一次来BTC那天为迁入
#         if first_switch[1] == 'BTC':  # 第一次切换目标是BTC
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_ETH',
#                 'date': first_switch[2]
#             })
        
#         # 如果最终停在ETH → 额外计最后一次离开BTC那天为迁出
#         if last_proj == 'ETH' and last_switch[0] == 'BTC':
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_ETH',
#                 'date': last_switch[2]
#             })

# # 构建DataFrame并去重
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# # 统计（列名改为 ETH）
# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_ETH'].groupby('date').size().rename('daily_in_from_ETH')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_ETH'].groupby('date').size().rename('daily_out_to_ETH')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# # 保存（文件名改为 btc_eth）
# daily_summary.to_csv('/home/lab0/survival_diffusion_github/btc_eth_migration_strict_rules.csv')

# print("\nDaily migration summary (tail 20):")
# print(daily_summary.tail(20))


# Bitcoin sv
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH → BSV）
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"
# BSV_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinsv_events_all.csv"  # 改为 BSV

# # 读取数据
# print("Loading BTC and BSV data...")
# df_btc = pd.read_csv(BTC_PATH)
# df_bsv = pd.read_csv(BSV_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df in [df_btc, df_bsv]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in data: {missing}")

# # 时间解析
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])
# df_bsv['created_at'] = pd.to_datetime(df_bsv['created_at'])

# # 添加项目标签
# df_btc['project'] = 'BTC'
# df_bsv['project'] = 'BSV'   # 改为 BSV

# # 合并
# df_combined = pd.concat([df_btc, df_bsv], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:  # 只在项目变化时记录
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None, 
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     # 细节路径：每步切换
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),  # 如 BTC-BSV-BTC
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)  # 原始总贡献次数
#     })

# print("Generating cross-chain migration paths (removing same-project repeats)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户（可选过滤）
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"Users with cross-chain migration: {len(cross_chain_users)}")

# # 展开细节表（每一步切换一行）
# detail_rows = []
# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': user,
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名全部改为 btc_bsv）
# df_migration_detail.to_csv('/home/lab0/survival_diffusion_github/btc_bsv_migration_detail_clean.csv', index=False)
# user_paths.to_csv('/home/lab0/survival_diffusion_github/btc_bsv_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv('/home/lab0/survival_diffusion_github/btc_bsv_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths:")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']  # [(proj, time), ...]
    
#     if len(detail) < 2:  # 没切换
#         continue
    
#     # 找第一次和最后一次切换日期
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]  # (from, to, date)
#     last_switch = switches[-1]   # (from, to, date)
    
#     # 规则应用（所有 ETH → BSV 替换）
#     if first_proj == 'BTC':
#         # 起点BTC系列
#         if last_proj == 'BSV':
#             # 最终停在BSV → 计迁出，用最后一次离开BTC的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BSV',
#                 'date': last_switch[2]
#             })
#         # 最终回BTC → 不计任何迁入/迁出
    
#     elif first_proj == 'BSV':
#         # 起点BSV系列
#         # 所有情况都计第一次来BTC那天为迁入
#         if first_switch[1] == 'BTC':  # 第一次切换目标是BTC
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_BSV',
#                 'date': first_switch[2]
#             })
        
#         # 如果最终停在BSV → 额外计最后一次离开BTC那天为迁出
#         if last_proj == 'BSV' and last_switch[0] == 'BTC':
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BSV',
#                 'date': last_switch[2]
#             })

# # 构建DataFrame并去重
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# # 统计（列名改为 BSV）
# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_BSV'].groupby('date').size().rename('daily_in_from_BSV')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_BSV'].groupby('date').size().rename('daily_out_to_BSV')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# # 保存（文件名改为 btc_bsv）
# daily_summary.to_csv('/home/lab0/survival_diffusion_github/btc_bsv_migration_strict_rules.csv')

# print("\nDaily migration summary (tail 20):")
# print(daily_summary.tail(20))

# ==================================================

# Litecoin
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（BSV → Litecoin）
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"
# LTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin_compete/litecoin_events_timeline_unified_all.csv"  # 改为 Litecoin

# # 读取数据
# print("Loading BTC and Litecoin data...")
# df_btc = pd.read_csv(BTC_PATH)
# df_ltc = pd.read_csv(LTC_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df in [df_btc, df_ltc]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in data: {missing}")

# # 时间解析
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])
# df_ltc['created_at'] = pd.to_datetime(df_ltc['created_at'])

# # 添加项目标签
# df_btc['project'] = 'BTC'
# df_ltc['project'] = 'LTC'   # 改为 LTC

# # 合并
# df_combined = pd.concat([df_btc, df_ltc], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:  # 只在项目变化时记录
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None, 
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     # 细节路径：每步切换
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),  # 如 BTC-LTC-BTC
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)  # 原始总贡献次数
#     })

# print("Generating cross-chain migration paths (removing same-project repeats)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户（可选过滤）
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"Users with cross-chain migration: {len(cross_chain_users)}")

# # 展开细节表（每一步切换一行）
# detail_rows = []
# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': user,
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名全部改为 btc_ltc）
# df_migration_detail.to_csv('/home/lab0/survival_diffusion_github/btc_ltc_migration_detail_clean.csv', index=False)
# user_paths.to_csv('/home/lab0/survival_diffusion_github/btc_ltc_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv('/home/lab0/survival_diffusion_github/btc_ltc_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths:")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']  # [(proj, time), ...]
    
#     if len(detail) < 2:  # 没切换
#         continue
    
#     # 找第一次和最后一次切换日期
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]  # (from, to, date)
#     last_switch = switches[-1]   # (from, to, date)
    
#     # 规则应用（所有 BSV → LTC 替换）
#     if first_proj == 'BTC':
#         # 起点BTC系列
#         if last_proj == 'LTC':
#             # 最终停在LTC → 计迁出，用最后一次离开BTC的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_LTC',
#                 'date': last_switch[2]
#             })
#         # 最终回BTC → 不计任何迁入/迁出
    
#     elif first_proj == 'LTC':
#         # 起点LTC系列
#         # 所有情况都计第一次来BTC那天为迁入
#         if first_switch[1] == 'BTC':  # 第一次切换目标是BTC
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_LTC',
#                 'date': first_switch[2]
#             })
        
#         # 如果最终停在LTC → 额外计最后一次离开BTC那天为迁出
#         if last_proj == 'LTC' and last_switch[0] == 'BTC':
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_LTC',
#                 'date': last_switch[2]
#             })

# # 构建DataFrame并去重
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# # 统计（列名改为 LTC）
# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_LTC'].groupby('date').size().rename('daily_in_from_LTC')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_LTC'].groupby('date').size().rename('daily_out_to_LTC')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# # 保存（文件名改为 btc_ltc）
# daily_summary.to_csv('/home/lab0/survival_diffusion_github/btc_ltc_migration_strict_rules.csv')

# print("\nDaily migration summary (tail 20):")
# print(daily_summary.tail(20))


# Dogecoin
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（LTC → Dogecoin）
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"
# DOGE_PATH = "/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_events_timeline_unified_all.csv"  # 改为 Dogecoin

# # 读取数据
# print("Loading BTC and Dogecoin data...")
# df_btc = pd.read_csv(BTC_PATH)
# df_doge = pd.read_csv(DOGE_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df in [df_btc, df_doge]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"Missing columns in data: {missing}")

# # 时间解析
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])
# df_doge['created_at'] = pd.to_datetime(df_doge['created_at'])

# # 添加项目标签
# df_btc['project'] = 'BTC'
# df_doge['project'] = 'DOGE'   # 改为 DOGE

# # 合并
# df_combined = pd.concat([df_btc, df_doge], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:  # 只在项目变化时记录
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None, 
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     # 细节路径：每步切换
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),  # 如 BTC-DOGE-BTC
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)  # 原始总贡献次数
#     })

# print("Generating cross-chain migration paths (removing same-project repeats)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户（可选过滤）
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"Users with cross-chain migration: {len(cross_chain_users)}")

# # 展开细节表（每一步切换一行）
# detail_rows = []
# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': user,
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名全部改为 btc_doge）
# df_migration_detail.to_csv('/home/lab0/survival_diffusion_github/btc_doge_migration_detail_clean.csv', index=False)
# user_paths.to_csv('/home/lab0/survival_diffusion_github/btc_doge_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv('/home/lab0/survival_diffusion_github/btc_doge_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths:")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']  # [(proj, time), ...]
    
#     if len(detail) < 2:  # 没切换
#         continue
    
#     # 找第一次和最后一次切换日期
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]  # (from, to, date)
#     last_switch = switches[-1]   # (from, to, date)
    
#     # 规则应用（所有 LTC → DOGE 替换）
#     if first_proj == 'BTC':
#         # 起点BTC系列
#         if last_proj == 'DOGE':
#             # 最终停在DOGE → 计迁出，用最后一次离开BTC的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_DOGE',
#                 'date': last_switch[2]
#             })
#         # 最终回BTC → 不计任何迁入/迁出
    
#     elif first_proj == 'DOGE':
#         # 起点DOGE系列
#         # 所有情况都计第一次来BTC那天为迁入
#         if first_switch[1] == 'BTC':  # 第一次切换目标是BTC
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_DOGE',
#                 'date': first_switch[2]
#             })
        
#         # 如果最终停在DOGE → 额外计最后一次离开BTC那天为迁出
#         if last_proj == 'DOGE' and last_switch[0] == 'BTC':
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_DOGE',
#                 'date': last_switch[2]
#             })

# # 构建DataFrame并去重
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# # 统计（列名改为 DOGE）
# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_DOGE'].groupby('date').size().rename('daily_in_from_DOGE')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_DOGE'].groupby('date').size().rename('daily_out_to_DOGE')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# # 保存（文件名改为 btc_doge）
# daily_summary.to_csv('/home/lab0/survival_diffusion_github/btc_doge_migration_strict_rules.csv')

# print("\nDaily migration summary (tail 20):")
# print(daily_summary.tail(20))


# ==================================================
# 换成ETH与BTC
# TARGET_PROJECTS = {
#     'BTC': "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv",
#     'BNB': "/home/lab0/survival_diffusion_github/Ethereum_compete/EVM/bnb_events_all.csv",
#     'SUI': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/sui_events_all.csv",
#     'SOLANA': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/solana_events_all.csv",
#     'NEAR': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/near_events_all.csv",
#     'HARMONY': "/home/lab0/survival_diffusion_github/Ethereum_compete/EVM/harmony_events_all.csv",
#     'APTOS': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/aptos_events_all.csv",
#     'ZKSYNC': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/zksync_events_all.csv",
#     'OPTIMISM': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/Optimism_events_all.csv",
#     'ARBITRUM': "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/Arbitrum_events_all.csv"
# }
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，BTC 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# BTC_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all.csv"

# # 读取数据
# print("Loading ETH (main) and BTC data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_btc = pd.read_csv(BTC_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_btc, 'BTC')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_btc['created_at'] = pd.to_datetime(df_btc['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_btc['project'] = 'BTC'

# # 合并
# df_combined = pd.concat([df_eth, df_btc], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs BTC: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_btc）
# base_out = '/home/lab0/survival_diffusion_github/eth_btc'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs BTC):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'BTC'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在BTC → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BTC',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点BTC系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_BTC',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在BTC → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BTC',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_BTC'].groupby('date').size().rename('daily_in_from_BTC')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_BTC'].groupby('date').size().rename('daily_out_to_BTC')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# ==================================================
# ETH和BNB
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，BNB 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# BNB_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/EVM/bnb_events_all.csv"  # 改为 BNB

# # 读取数据
# print("Loading ETH (main) and BNB data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_bnb = pd.read_csv(BNB_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_bnb, 'BNB')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_bnb['created_at'] = pd.to_datetime(df_bnb['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_bnb['project'] = 'BNB'   # 改为 BNB

# # 合并
# df_combined = pd.concat([df_eth, df_bnb], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs BNB: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_bnb）
# base_out = '/home/lab0/survival_diffusion_github/eth_bnb'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs BNB):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'BNB'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在BNB → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BNB',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点BNB系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_BNB',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在BNB → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_BNB',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_BNB'].groupby('date').size().rename('daily_in_from_BNB')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_BNB'].groupby('date').size().rename('daily_out_to_BNB')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))



# ==================================================
# ETH和SUI
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，SUI 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# SUI_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/sui_events_all.csv"  # 改为 SUI

# # 读取数据
# print("Loading ETH (main) and SUI data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_sui = pd.read_csv(SUI_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_sui, 'SUI')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_sui['created_at'] = pd.to_datetime(df_sui['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_sui['project'] = 'SUI'   # 改为 SUI

# # 合并
# df_combined = pd.concat([df_eth, df_sui], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs SUI: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_sui）
# base_out = '/home/lab0/survival_diffusion_github/eth_sui'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs SUI):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'SUI'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在SUI → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_SUI',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点SUI系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_SUI',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在SUI → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_SUI',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_SUI'].groupby('date').size().rename('daily_in_from_SUI')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_SUI'].groupby('date').size().rename('daily_out_to_SUI')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# ==================================================
# ETH和SOLANA
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，SOLANA 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# SOLANA_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/solana_events_all.csv"  # 改为 SOLANA

# # 读取数据
# print("Loading ETH (main) and SOLANA data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_solana = pd.read_csv(SOLANA_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_solana, 'SOLANA')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_solana['created_at'] = pd.to_datetime(df_solana['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_solana['project'] = 'SOLANA'   # 改为 SOLANA

# # 合并
# df_combined = pd.concat([df_eth, df_solana], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs SOLANA: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_solana）
# base_out = '/home/lab0/survival_diffusion_github/eth_solana'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs SOLANA):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'SOLANA'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在SOLANA → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_SOLANA',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点SOLANA系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_SOLANA',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在SOLANA → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_SOLANA',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_SOLANA'].groupby('date').size().rename('daily_in_from_SOLANA')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_SOLANA'].groupby('date').size().rename('daily_out_to_SOLANA')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# =======
# ETH和Near
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，NEAR 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# NEAR_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/near_events_all.csv"  # 改为 NEAR

# # 读取数据
# print("Loading ETH (main) and NEAR data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_near = pd.read_csv(NEAR_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_near, 'NEAR')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_near['created_at'] = pd.to_datetime(df_near['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_near['project'] = 'NEAR'   # 改为 NEAR

# # 合并
# df_combined = pd.concat([df_eth, df_near], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs NEAR: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_near）
# base_out = '/home/lab0/survival_diffusion_github/eth_near'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs NEAR):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'NEAR'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在NEAR → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_NEAR',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点NEAR系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_NEAR',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在NEAR → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_NEAR',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_NEAR'].groupby('date').size().rename('daily_in_from_NEAR')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_NEAR'].groupby('date').size().rename('daily_out_to_NEAR')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# =====
# ETH和aptos
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，APTOS 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# APTOS_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer1/aptos_events_all.csv"  # 改为 APTOS

# # 读取数据
# print("Loading ETH (main) and APTOS data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_aptos = pd.read_csv(APTOS_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_aptos, 'APTOS')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_aptos['created_at'] = pd.to_datetime(df_aptos['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_aptos['project'] = 'APTOS'   # 改为 APTOS

# # 合并
# df_combined = pd.concat([df_eth, df_aptos], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs APTOS: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_aptos）
# base_out = '/home/lab0/survival_diffusion_github/eth_aptos'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs APTOS):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'APTOS'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在APTOS → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_APTOS',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点APTOS系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_APTOS',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在APTOS → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_APTOS',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_APTOS'].groupby('date').size().rename('daily_in_from_APTOS')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_APTOS'].groupby('date').size().rename('daily_out_to_APTOS')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# =========
# ETH和harmony
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，HARMONY 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# HARMONY_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/EVM/harmony_events_all.csv"  # 改为 HARMONY

# # 读取数据
# print("Loading ETH (main) and HARMONY data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_harmony = pd.read_csv(HARMONY_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_harmony, 'HARMONY')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_harmony['created_at'] = pd.to_datetime(df_harmony['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_harmony['project'] = 'HARMONY'   # 改为 HARMONY

# # 合并
# df_combined = pd.concat([df_eth, df_harmony], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs HARMONY: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_harmony）
# base_out = '/home/lab0/survival_diffusion_github/eth_harmony'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs HARMONY):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'HARMONY'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在HARMONY → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_HARMONY',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点HARMONY系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_HARMONY',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在HARMONY → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_HARMONY',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_HARMONY'].groupby('date').size().rename('daily_in_from_HARMONY')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_HARMONY'].groupby('date').size().rename('daily_out_to_HARMONY')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# =========
# ETH和zk
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，ZKSYNC 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# ZKSYNC_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/zksync_events_all.csv"  # 改为 ZKSYNC

# # 读取数据
# print("Loading ETH (main) and ZKSYNC data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_zksync = pd.read_csv(ZKSYNC_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_zksync, 'ZKSYNC')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_zksync['created_at'] = pd.to_datetime(df_zksync['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_zksync['project'] = 'ZKSYNC'   # 改为 ZKSYNC

# # 合并
# df_combined = pd.concat([df_eth, df_zksync], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs ZKSYNC: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_zksync）
# base_out = '/home/lab0/survival_diffusion_github/eth_zksync'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs ZKSYNC):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'ZKSYNC'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在ZKSYNC → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_ZKSYNC',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点ZKSYNC系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_ZKSYNC',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在ZKSYNC → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_ZKSYNC',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_ZKSYNC'].groupby('date').size().rename('daily_in_from_ZKSYNC')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_ZKSYNC'].groupby('date').size().rename('daily_out_to_ZKSYNC')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))

# =================================================================
# ETH和Optimism
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # 文件路径（ETH 为主体，OPTIMISM 为目标）
# ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
# OPTIMISM_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/Optimism_events_all.csv"  # 改为 OPTIMISM

# # 读取数据
# print("Loading ETH (main) and OPTIMISM data...")
# df_eth = pd.read_csv(ETH_PATH)
# df_optimism = pd.read_csv(OPTIMISM_PATH)

# # 关键列检查
# required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
# for df, name in [(df_eth, 'ETH'), (df_optimism, 'OPTIMISM')]:
#     missing = [col for col in required_cols if col not in df.columns]
#     if missing:
#         raise ValueError(f"{name} data missing columns: {missing}")

# # 时间解析
# df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
# df_optimism['created_at'] = pd.to_datetime(df_optimism['created_at'])

# # 添加项目标签（ETH 为主体）
# df_eth['project'] = 'ETH'
# df_optimism['project'] = 'OPTIMISM'   # 改为 OPTIMISM

# # 合并
# df_combined = pd.concat([df_eth, df_optimism], ignore_index=True)

# # 用户唯一标识：优先 actor_id，其次 actor_login
# df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# # 按用户和时间排序
# df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# # ===================================================================
# # (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# # ===================================================================
# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times = seq['created_at'].tolist()
    
#     # 只保留项目切换的路径（去重连续相同项目）
#     clean_projects = []
#     clean_times = []
#     prev_proj = None
#     for proj, time in zip(projects, times):
#         if proj != prev_proj:
#             clean_projects.append(proj)
#             clean_times.append(time)
#             prev_proj = proj
    
#     if not clean_projects:
#         return pd.Series({'path_detail': [], 'path_str': '', 'first_project': None,
#                          'first_time': None, 'last_project': None, 'last_time': None,
#                          'contribution_count': 0})
    
#     path_detail = list(zip(clean_projects, clean_times))
    
#     return pd.Series({
#         'path_detail': path_detail,
#         'path_str': '-'.join(clean_projects),
#         'first_project': clean_projects[0],
#         'first_time': clean_times[0],
#         'last_project': clean_projects[-1],
#         'last_time': clean_times[-1],
#         'contribution_count': len(seq)
#     })

# print("Generating cross-chain migration paths (ETH as main)...")
# user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# # 只保留有跨链迁移的用户
# cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
# print(f"ETH vs OPTIMISM: {len(cross_chain_users)} users with cross-chain migration")

# # 展开细节表
# detail_rows = []
# for _, row in user_paths.iterrows():
#     for i, (proj, time) in enumerate(row['path_detail']):
#         detail_rows.append({
#             'user_id': row['user_id'],
#             'step': i + 1,
#             'project': proj,
#             'time': time,
#             'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
#         })

# df_migration_detail = pd.DataFrame(detail_rows)

# # 保存（文件名统一 eth_optimism）
# base_out = '/home/lab0/survival_diffusion_github/eth_optimism'
# df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
# user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
# cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

# print("Sample cross-chain paths (ETH vs OPTIMISM):")
# print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# # ===================================================================
# # (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# # ===================================================================
# migration_events = []

# for _, row in user_paths.iterrows():
#     user = row['user_id']
#     first_proj = row['first_project']
#     last_proj = row['last_project']
#     detail = row['path_detail']
    
#     if len(detail) < 2:
#         continue
    
#     switches = []
#     prev_proj = detail[0][0]
#     for proj, time in detail[1:]:
#         if proj != prev_proj:
#             switches.append((prev_proj, proj, time.date()))
#         prev_proj = proj
    
#     if not switches:
#         continue
    
#     first_switch = switches[0]
#     last_switch = switches[-1]
    
#     target_proj = 'OPTIMISM'  # 目标项目
    
#     if first_proj == 'ETH':
#         # 起点ETH系列
#         if last_proj == target_proj:
#             # 最终停在OPTIMISM → 计迁出，用最后一次离开ETH的日期
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_OPTIMISM',
#                 'date': last_switch[2]
#             })
    
#     elif first_proj == target_proj:
#         # 起点OPTIMISM系列
#         if first_switch[1] == 'ETH':
#             # 第一次来ETH → 计迁入
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'in_from_OPTIMISM',
#                 'date': first_switch[2]
#             })
        
#         if last_proj == target_proj and last_switch[0] == 'ETH':
#             # 最终停在OPTIMISM → 计最后一次离开ETH为迁出
#             migration_events.append({
#                 'user_id': user,
#                 'type': 'out_to_OPTIMISM',
#                 'date': last_switch[2]
#             })

# # 去重 + 统计
# df_daily_migration = pd.DataFrame(migration_events)
# df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

# daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_OPTIMISM'].groupby('date').size().rename('daily_in_from_OPTIMISM')
# daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_OPTIMISM'].groupby('date').size().rename('daily_out_to_OPTIMISM')

# daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
# daily_summary = daily_summary.sort_index()

# daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

# print("\nDaily migration summary (ETH as main, tail 20):")
# print(daily_summary.tail(20))


# =================================================================
# ETH和ARBITRUM
import pandas as pd
import numpy as np
from datetime import datetime
import os

# 文件路径（ETH 为主体，ARBITRUM 为目标）
ETH_PATH = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all.csv"
ARBITRUM_PATH = "/home/lab0/survival_diffusion_github/Ethereum_compete/Layer2/Arbitrum_events_all.csv"  # 改为 ARBITRUM

# 读取数据
print("Loading ETH (main) and ARBITRUM data...")
df_eth = pd.read_csv(ETH_PATH)
df_arbitrum = pd.read_csv(ARBITRUM_PATH)

# 关键列检查
required_cols = ['created_at', 'event_type', 'actor_id', 'actor_login', 'repository_url']
for df, name in [(df_eth, 'ETH'), (df_arbitrum, 'ARBITRUM')]:
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} data missing columns: {missing}")

# 时间解析
df_eth['created_at'] = pd.to_datetime(df_eth['created_at'])
df_arbitrum['created_at'] = pd.to_datetime(df_arbitrum['created_at'])

# 添加项目标签（ETH 为主体）
df_eth['project'] = 'ETH'
df_arbitrum['project'] = 'ARBITRUM'   # 改为 ARBITRUM

# 合并
df_combined = pd.concat([df_eth, df_arbitrum], ignore_index=True)

# 用户唯一标识：优先 actor_id，其次 actor_login
df_combined['user_id'] = df_combined['actor_id'].fillna(df_combined['actor_login'])

# 按用户和时间排序
df_combined = df_combined.sort_values(['user_id', 'created_at']).reset_index(drop=True)

# ===================================================================
# (1) 生成跨链迁移路径（只记录项目切换，去掉同项目重复）
# ===================================================================
def get_migration_sequence(group):
    seq = group.sort_values('created_at')
    projects = seq['project'].tolist()
    times = seq['created_at'].tolist()
    
    # 只保留项目切换的路径（去重连续相同项目）
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

print("Generating cross-chain migration paths (ETH as main)...")
user_paths = df_combined.groupby('user_id').apply(get_migration_sequence).reset_index()

# 只保留有跨链迁移的用户
cross_chain_users = user_paths[user_paths['path_str'].str.contains('-', na=False)]
print(f"ETH vs ARBITRUM: {len(cross_chain_users)} users with cross-chain migration")

# 展开细节表
detail_rows = []
for _, row in user_paths.iterrows():
    for i, (proj, time) in enumerate(row['path_detail']):
        detail_rows.append({
            'user_id': row['user_id'],
            'step': i + 1,
            'project': proj,
            'time': time,
            'path_so_far': '-'.join([p for p, _ in row['path_detail'][:i+1]])
        })

df_migration_detail = pd.DataFrame(detail_rows)

# 保存（文件名统一 eth_arbitrum）
base_out = '/home/lab0/survival_diffusion_github/eth_arbitrum'
df_migration_detail.to_csv(f'{base_out}_migration_detail_clean.csv', index=False)
user_paths.to_csv(f'{base_out}_user_summary_paths_clean.csv', index=False)
cross_chain_users.to_csv(f'{base_out}_cross_chain_users_only.csv', index=False)

print("Sample cross-chain paths (ETH vs ARBITRUM):")
print(cross_chain_users[['user_id', 'path_str', 'first_project', 'first_time', 'last_project', 'last_time']].head(15))

# ===================================================================
# (2) 每日迁入/迁出不重复人数（严格规则，以 ETH 为主体）
# ===================================================================
migration_events = []

for _, row in user_paths.iterrows():
    user = row['user_id']
    first_proj = row['first_project']
    last_proj = row['last_project']
    detail = row['path_detail']
    
    if len(detail) < 2:
        continue
    
    switches = []
    prev_proj = detail[0][0]
    for proj, time in detail[1:]:
        if proj != prev_proj:
            switches.append((prev_proj, proj, time.date()))
        prev_proj = proj
    
    if not switches:
        continue
    
    first_switch = switches[0]
    last_switch = switches[-1]
    
    target_proj = 'ARBITRUM'  # 目标项目
    
    if first_proj == 'ETH':
        # 起点ETH系列
        if last_proj == target_proj:
            # 最终停在ARBITRUM → 计迁出，用最后一次离开ETH的日期
            migration_events.append({
                'user_id': user,
                'type': 'out_to_ARBITRUM',
                'date': last_switch[2]
            })
    
    elif first_proj == target_proj:
        # 起点ARBITRUM系列
        if first_switch[1] == 'ETH':
            # 第一次来ETH → 计迁入
            migration_events.append({
                'user_id': user,
                'type': 'in_from_ARBITRUM',
                'date': first_switch[2]
            })
        
        if last_proj == target_proj and last_switch[0] == 'ETH':
            # 最终停在ARBITRUM → 计最后一次离开ETH为迁出
            migration_events.append({
                'user_id': user,
                'type': 'out_to_ARBITRUM',
                'date': last_switch[2]
            })

# 去重 + 统计
df_daily_migration = pd.DataFrame(migration_events)
df_daily_migration = df_daily_migration.drop_duplicates(subset=['user_id', 'type'])

daily_in = df_daily_migration[df_daily_migration['type'] == 'in_from_ARBITRUM'].groupby('date').size().rename('daily_in_from_ARBITRUM')
daily_out = df_daily_migration[df_daily_migration['type'] == 'out_to_ARBITRUM'].groupby('date').size().rename('daily_out_to_ARBITRUM')

daily_summary = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
daily_summary = daily_summary.sort_index()

daily_summary.to_csv(f'{base_out}_migration_strict_rules.csv')

print("\nDaily migration summary (ETH as main, tail 20):")
print(daily_summary.tail(20))