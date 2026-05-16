# # import requests
# # import csv
# # from io import StringIO

# # def get_readme_markdown_raw(owner: str, repo: str, branch: str = 'main', path: str = 'README.md') -> str or None:
# #     """
# #     通过 raw.githubusercontent.com 链接获取指定 GitHub 仓库的 README.md 原始内容。
# #     """
# #     raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    
# #     print(f"正在尝试从 URL: {raw_url} 获取数据...")
    
# #     try:
# #         response = requests.get(raw_url)
        
# #         if response.status_code == 200:
# #             print("数据获取成功。")
# #             return response.text
# #         else:
# #             print(f"请求失败，状态码: {response.status_code}。请检查分支名 '{branch}' 和文件路径 '{path}' 是否正确。")
# #             return None
            
# #     except requests.exceptions.RequestException as e:
# #         print(f"发生请求错误: {e}")
# #         return None

# # def save_to_csv(data: list, filename: str = 'github_readmes.csv'):
# #     """
# #     将包含仓库信息和 README 内容的数据列表保存到 CSV 文件。

# #     :param data: 包含字典的列表，每个字典包含 'Owner', 'Repo', 'Branch', 'README_Content' 键。
# #     :param filename: 要保存的 CSV 文件名。
# #     """
# #     if not data:
# #         print("没有数据可写入 CSV 文件。")
# #         return

# #     # 定义 CSV 文件的列名
# #     fieldnames = ['Owner', 'Repo', 'Branch', 'README_Content']
    
# #     try:
# #         with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
# #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
# #             # 写入表头
# #             writer.writeheader()
            
# #             # 写入数据行
# #             writer.writerows(data)
            
# #         print(f"\n✅ 数据成功保存到文件: {filename}")
# #     except Exception as e:
# #         print(f"\n❌ 保存 CSV 文件时发生错误: {e}")


# # # --- 示例用法：批量处理多个仓库 ---

# # # 待处理的仓库列表 (Owner, Repo, Branch)
# # REPOS_TO_FETCH = [
# #     ("openai", "openai-python", "main"),
# #     ("pallets", "flask", "main"),
# #     ("facebook", "react", "main") # 假设主分支是 main
# #     # 示例：一个可能不存在的分支或文件，用于测试错误处理
# #     #("invalid_owner", "invalid_repo", "master") 
# # ]

# # results = []
# # for owner, repo, branch in REPOS_TO_FETCH:
# #     readme_content = get_readme_markdown_raw(owner, repo, branch)
    
# #     # 无论成功或失败，都记录结果
# #     results.append({
# #         'Owner': owner,
# #         'Repo': repo,
# #         'Branch': branch,
# #         # 如果获取失败，内容为空字符串
# #         'README_Content': readme_content if readme_content else "" 
# #     })
    
# # save_to_csv(results, 'github_readme_data.csv')

# # import pandas as pd
# # import numpy as np
# # import scipy.stats as stats
# # import matplotlib.pyplot as plt
# # import seaborn as sns

# # # 文件路径（请确保路径正确）
# # file_path = '/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv'
# # feature_col = 'btc_event'
# # target_col = 'btc_price'

# # def analyze_correlation(df, feature, target):
# #     """
# #     计算并打印特征与目标变量的线性和非线性相关性。
    
# #     参数:
# #     df (pd.DataFrame): 包含数据的DataFrame。
# #     feature (str): 要分析的特征列名 (btc_p_event)。
# #     target (str): 目标变量列名 (btc_price)。
# #     """
    
# #     # 检查目标列和特征列是否存在
# #     if feature not in df.columns or target not in df.columns:
# #         print(f"错误: 文件中缺少列 '{feature}' 或 '{target}'。")
# #         return

# #     # 1. 数据清洗和准备
# #     df = df.dropna(subset=[feature, target]).copy()
    
# #     # 确保特征值非负（进行 log, sqrt 变换的前提）
# #     if (df[feature] < 0).any():
# #         print(f"警告: 特征 '{feature}' 包含负值，可能导致某些非线性变换失败。")
# #         # 排除负值或调整变换（此处假设数据大多非负或已处理）
    
    
# #     # 2. 定义要测试的变换
# #     transformations = {
# #         'Linear (X)': lambda x: x,
# #         'Log (ln(1+X))': lambda x: np.log1p(x), # 使用 log1p 处理可能存在的0值
# #         'Square Root (sqrt(X))': lambda x: np.sqrt(x),
# #         'Squared (X^2)': lambda x: np.power(x, 2),
# #         'Cubic (X^3)': lambda x: np.power(x, 3),
# #         'Inverse (1/X)': lambda x: np.where(x != 0, 1 / x, np.nan) # 处理除以0的情况
# #     }
    
# #     results = {}
    
# #     # 3. 计算相关性
# #     print(f"=== 分析 {feature} 与 {target} 的相关性 ===")
    
# #     for name, func in transformations.items():
# #         try:
# #             # 应用变换
# #             transformed_feature = func(df[feature])
            
# #             # 清理变换后可能产生的 NaN/Inf
# #             valid_data = transformed_feature.replace([np.inf, -np.inf], np.nan).dropna()
            
# #             # 确保价格数据也匹配 valid_data 的索引
# #             target_aligned = df.loc[valid_data.index, target]
            
# #             if len(valid_data) > 1:
# #                 # 计算皮尔逊相关系数
# #                 corr, p_value = stats.pearsonr(valid_data, target_aligned)
# #                 results[name] = {'Correlation (r)': corr, 'P-Value': p_value}
                
# #                 print(f"{name:<25} | r = {corr:.4f}, P-Value = {p_value:.4f}")
# #             else:
# #                  print(f"{name:<25} | 数据点不足，无法计算相关性。")
            
# #         except Exception as e:
# #             results[name] = {'Correlation (r)': np.nan, 'P-Value': np.nan}
# #             print(f"{name:<25} | 计算失败: {e}")
            
# #     return df, results

# # # --- 执行分析 ---
# # try:
# #     df = pd.read_csv(file_path)
# #     df, correlation_results = analyze_correlation(df, feature_col, target_col)

# #     print("\n=== 相关性结果总结 ===")
# #     summary_df = pd.DataFrame(correlation_results).T
# #     print(summary_df.sort_values(by='Correlation (r)', key=lambda x: abs(x), ascending=False))
    
    
# #     # --- 可视化最佳相关性 (可选) ---
# #     best_form = summary_df['Correlation (r)'].abs().idxmax()
# #     if best_form and best_form != 'Inverse (1/X)': # 避免对倒数形式进行可视化，除非它是最佳形式
# #         print(f"\n=== 最佳相关性形式散点图: {best_form} ===")
        
# #         # 重新应用最佳变换
# #         func = transformations.get(best_form)
# #         transformed_feature = func(df[feature_col].dropna())
# #         target_aligned = df.loc[transformed_feature.index, target_col].dropna()
        
# #         plt.figure(figsize=(10, 6))
# #         sns.regplot(x=transformed_feature, y=target_aligned, scatter_kws={'alpha':0.6}, line_kws={"color": "red"})
# #         plt.title(f'{target_col} vs. {best_form} of {feature_col} (r={correlation_results[best_form]["Correlation (r)"]:.4f})')
# #         plt.xlabel(best_form)
# #         plt.ylabel(target_col)
# #         plt.grid(True, linestyle='--', alpha=0.6)
# #         plt.show()

# # except FileNotFoundError:
# #     print(f"错误: 文件未找到，请检查路径: {file_path}")
# # except Exception as e:
# #     print(f"发生未知错误: {e}")

# # import pandas as pd
# # import numpy as np
# # import scipy.stats as stats
# # import matplotlib.pyplot as plt
# # import seaborn as sns

# # file_path = '/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv'
# # target_col = 'eth_price'


# # def analyze_correlation(df, feature, target):
# #     """
# #     计算并返回单个 event 与 eth_price 的多种变换相关性
# #     """

# #     if feature not in df.columns or target not in df.columns:
# #         return None

# #     # pairwise dropna（非常关键）
# #     df_sub = df[[feature, target]].dropna().copy()

# #     if len(df_sub) < 5:
# #         return None

# #     transformations = {
# #         'Linear': lambda x: x,
# #         'Log': lambda x: np.log1p(np.maximum(x, 0)),
# #         'Sqrt': lambda x: np.sqrt(np.maximum(x, 0)),
# #         'Squared': lambda x: np.power(x, 2),
# #         'Cubic': lambda x: np.power(x, 3),
# #         'Inverse': lambda x: np.where(x != 0, 1 / x, np.nan)
# #     }

# #     records = []

# #     for name, func in transformations.items():
# #         try:
# #             x = func(df_sub[feature])
# #             valid = x.replace([np.inf, -np.inf], np.nan).dropna()
# #             y = df_sub.loc[valid.index, target]

# #             if len(valid) < 3:
# #                 continue

# #             r, p = stats.pearsonr(valid, y)

# #             records.append({
# #                 "event_var": feature,
# #                 "transform": name,
# #                 "pearson_r": r,
# #                 "p_value": p,
# #                 "N_used": len(valid)
# #             })

# #         except Exception:
# #             continue

# #     return records


# # # ================== 主程序 ==================
# # df = pd.read_csv(file_path)

# # event_cols = [c for c in df.columns if "event" in c.lower()]

# # all_results = []

# # for event in event_cols:
# #     print(f"→ 分析 {event}")
# #     res = analyze_correlation(df, event, target_col)
# #     if res:
# #         all_results.extend(res)

# # corr_df = pd.DataFrame(all_results)

# # # 按绝对相关系数排序
# # corr_df = corr_df.sort_values(
# #     by="pearson_r",
# #     key=lambda x: x.abs(),
# #     ascending=False
# # )

# # out_path = "/home/lab0/survival_diffusion_github/competition_bass/eth_price_event_all_transform_correlations.csv"
# # corr_df.to_csv(out_path, index=False)

# # print(f"\n✅ 完成：所有 event × eth_price 相关性分析")
# # print(f"📄 结果保存至：{out_path}")

# # import pandas as pd
# # import numpy as np
# # import matplotlib.pyplot as plt
# # import seaborn as sns
# # from scipy.stats import pearsonr

# # # ============= 路径配置 =============
# # CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# # MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_daily_strict_rules.csv"
# # START_DATE = "2017-01-01"
# # END_DATE = "2019-01-01"

# # # ============= P事件列表（选择几个代表性的） =============
# # P_EVENT_COLS = [
# #     "btc_p_event_lag1",
# #     "btc_p_event_sum_7",
# #     "btc_p_event_mean_7",
# #     "btc_p_bip_p_event_lag1",
# #     "btc_p_bip_p_event_sum_7",
# # ]

# # # ============= Q事件列表（选择几个代表性的） =============
# # Q_EVENT_COLS = [
# #     "btc_q_event_lag1",
# #     "btc_q_event_sum_7",
# #     "btc_q_event_mean_7",
# #     "btc_q_bip_q_event_lag1",
# #     "btc_q_bip_q_event_sum_7",
# # ]

# # # ============= 币种列表 =============
# # COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "DOGE"]

# # # ============= 读取数据 =============
# # print("📂 读取数据...")
# # df_event = pd.read_csv(CSV_PATH, parse_dates=['date'])
# # df_migration = pd.read_csv(MIGRATION_PATH)

# # # 解析迁移数据的日期
# # df_migration['date'] = pd.to_datetime(df_migration['date'], format='mixed', dayfirst=False)

# # print(f"✅ 事件数据: {len(df_event)} 行")
# # print(f"✅ 迁移数据: {len(df_migration)} 行")

# # # ============= 筛选日期窗口 =============
# # df_event = df_event[(df_event['date'] >= START_DATE) & (df_event['date'] <= END_DATE)].copy()
# # df_migration = df_migration[(df_migration['date'] >= START_DATE) & (df_migration['date'] <= END_DATE)].copy()

# # print(f"📅 窗口期 {START_DATE} 至 {END_DATE}")
# # print(f"   事件数据: {len(df_event)} 行")
# # print(f"   迁移数据: {len(df_migration)} 行")

# # # ============= 合并数据 =============
# # df = df_event.merge(df_migration, on='date', how='inner')
# # print(f"✅ 合并后数据: {len(df)} 行")

# # # ============= 构建迁入迁出列名映射 =============
# # migration_cols = {
# #     'in': {
# #         'BCH': 'in_from_BCH',
# #         'BSV': 'in_from_BSV', 
# #         'ETH': 'in_from_ETH',
# #         'LTC': 'in_from_LTC',
# #         'DOGE': 'in_from_DOGE'
# #     },
# #     'out': {
# #         'BCH': 'out_to_BCH',
# #         'BSV': 'out_to_BSV',
# #         'ETH': 'out_to_ETH', 
# #         'LTC': 'out_to_LTC',
# #         'DOGE': 'out_to_DOGE'
# #     }
# # }

# # # ============= 检查列是否存在 =============
# # print("\n🔍 检查迁移数据列...")
# # for direction in ['in', 'out']:
# #     print(f"\n{direction.upper()}:")
# #     for coin, col in migration_cols[direction].items():
# #         if col in df.columns:
# #             total = df[col].sum()
# #             non_zero = (df[col] > 0).sum()
# #             print(f"  ✅ {col:15s}: 总数={total:6.0f}, 非零天数={non_zero:4d}")
# #         else:
# #             print(f"  ❌ {col:15s}: 列不存在")

# # # ============= 计算总迁入迁出 =============
# # df['M_in_total'] = 0
# # df['M_out_total'] = 0

# # for coin, col in migration_cols['in'].items():
# #     if col in df.columns:
# #         df['M_in_total'] += df[col].fillna(0)

# # for coin, col in migration_cols['out'].items():
# #     if col in df.columns:
# #         df['M_out_total'] += df[col].fillna(0)

# # df['M_net_total'] = df['M_in_total'] - df['M_out_total']

# # print(f"\n📊 迁移数据汇总:")
# # print(f"   总迁入:  {df['M_in_total'].sum():.0f}")
# # print(f"   总迁出:  {df['M_out_total'].sum():.0f}")
# # print(f"   净迁移:  {df['M_net_total'].sum():.0f}")

# # # ============= 相关性计算函数 =============
# # def calculate_correlations(df, event_cols, migration_cols_dict):
# #     """
# #     计算事件与迁移的相关系数
    
# #     Returns:
# #         corr_matrix: DataFrame with correlations
# #         pval_matrix: DataFrame with p-values
# #     """
# #     results = []
    
# #     for event_col in event_cols:
# #         if event_col not in df.columns:
# #             print(f"⚠️  跳过不存在的列: {event_col}")
# #             continue
            
# #         for direction in ['in', 'out']:
# #             # 各币种
# #             for coin, migration_col in migration_cols_dict[direction].items():
# #                 if migration_col in df.columns:
# #                     # 去除NaN
# #                     mask = df[event_col].notna() & df[migration_col].notna()
# #                     if mask.sum() > 10:  # 至少10个观测
# #                         corr, pval = pearsonr(
# #                             df.loc[mask, event_col], 
# #                             df.loc[mask, migration_col]
# #                         )
# #                         results.append({
# #                             'Event': event_col,
# #                             'Direction': direction,
# #                             'Coin': coin,
# #                             'Migration_Col': migration_col,
# #                             'Correlation': corr,
# #                             'P_value': pval,
# #                             'N': mask.sum(),
# #                             'Significant': '***' if pval < 0.01 else ('**' if pval < 0.05 else ('*' if pval < 0.10 else ''))
# #                         })
            
# #             # 总迁入/总迁出
# #             total_col = f'M_{direction}_total'
# #             mask = df[event_col].notna() & df[total_col].notna()
# #             if mask.sum() > 10:
# #                 corr, pval = pearsonr(
# #                     df.loc[mask, event_col], 
# #                     df.loc[mask, total_col]
# #                 )
# #                 results.append({
# #                     'Event': event_col,
# #                     'Direction': direction,
# #                     'Coin': 'TOTAL',
# #                     'Migration_Col': total_col,
# #                     'Correlation': corr,
# #                     'P_value': pval,
# #                     'N': mask.sum(),
# #                     'Significant': '***' if pval < 0.01 else ('**' if pval < 0.05 else ('*' if pval < 0.10 else ''))
# #                 })
        
# #         # 净迁移
# #         mask = df[event_col].notna() & df['M_net_total'].notna()
# #         if mask.sum() > 10:
# #             corr, pval = pearsonr(
# #                 df.loc[mask, event_col], 
# #                 df.loc[mask, 'M_net_total']
# #             )
# #             results.append({
# #                 'Event': event_col,
# #                 'Direction': 'net',
# #                 'Coin': 'TOTAL',
# #                 'Migration_Col': 'M_net_total',
# #                 'Correlation': corr,
# #                 'P_value': pval,
# #                 'N': mask.sum(),
# #                 'Significant': '***' if pval < 0.01 else ('**' if pval < 0.05 else ('*' if pval < 0.10 else ''))
# #             })
    
# #     return pd.DataFrame(results)

# # # ============= 计算P事件相关性 =============
# # print("\n" + "="*80)
# # print("📊 计算 P事件 与迁移的相关性...")
# # print("="*80)

# # results_p = calculate_correlations(df, P_EVENT_COLS, migration_cols)

# # # ============= 计算Q事件相关性 =============
# # print("\n" + "="*80)
# # print("📊 计算 Q事件 与迁移的相关性...")
# # print("="*80)

# # results_q = calculate_correlations(df, Q_EVENT_COLS, migration_cols)

# # # ============= 输出结果 =============
# # def print_correlation_table(results, event_type):
# #     """打印格式化的相关性表格"""
# #     print(f"\n{'='*100}")
# #     print(f"{event_type}事件 与 迁移的相关性")
# #     print(f"{'='*100}")
    
# #     # 按事件分组
# #     for event in results['Event'].unique():
# #         print(f"\n【{event}】")
# #         df_event = results[results['Event'] == event].copy()
        
# #         # 按方向分组
# #         for direction in ['in', 'out', 'net']:
# #             df_dir = df_event[df_event['Direction'] == direction]
# #             if len(df_dir) == 0:
# #                 continue
                
# #             print(f"\n  {direction.upper()}:")
            
# #             # 排序：先总计，后各币种
# #             df_dir = df_dir.sort_values('Coin', key=lambda x: x.map({'TOTAL': '0_TOTAL'}).fillna(x))
            
# #             for _, row in df_dir.iterrows():
# #                 corr_str = f"{row['Correlation']:+.4f}"
# #                 pval_str = f"{row['P_value']:.4f}"
# #                 sig = row['Significant']
                
# #                 # 根据显著性和符号着色（文本）
# #                 if row['P_value'] < 0.05:
# #                     if row['Correlation'] > 0:
# #                         marker = "↑"
# #                     else:
# #                         marker = "↓"
# #                 else:
# #                     marker = " "
                
# #                 print(f"    {row['Coin']:6s}: r={corr_str} (p={pval_str}) {sig:3s} {marker}")

# # print_correlation_table(results_p, "P")
# # print_correlation_table(results_q, "Q")

# # # ============= 保存详细结果到CSV =============
# # results_p['Event_Type'] = 'P'
# # results_q['Event_Type'] = 'Q'
# # results_all = pd.concat([results_p, results_q], ignore_index=True)

# # output_file = 'event_migration_correlations.csv'
# # results_all.to_csv(output_file, index=False)
# # print(f"\n✅ 详细结果已保存至: {output_file}")

# # # ============= 可视化：热力图 =============
# # print("\n📊 生成可视化...")

# # def create_heatmap(results, event_type, output_filename):
# #     """创建相关性热力图"""
    
# #     # 只保留总迁入/迁出/净迁移
# #     df_plot = results[results['Coin'] == 'TOTAL'].copy()
    
# #     if len(df_plot) == 0:
# #         print(f"⚠️  没有数据可绘制: {event_type}")
# #         return
    
# #     # 创建透视表
# #     pivot = df_plot.pivot(index='Event', columns='Direction', values='Correlation')
    
# #     # 创建显著性标记
# #     pval_pivot = df_plot.pivot(index='Event', columns='Direction', values='P_value')
# #     annot = pivot.copy()
# #     for i in range(annot.shape[0]):
# #         for j in range(annot.shape[1]):
# #             val = pivot.iloc[i, j]
# #             pval = pval_pivot.iloc[i, j]
# #             if pd.notna(val):
# #                 sig = '***' if pval < 0.01 else ('**' if pval < 0.05 else ('*' if pval < 0.10 else ''))
# #                 annot.iloc[i, j] = f"{val:.3f}{sig}"
    
# #     # 绘图
# #     plt.figure(figsize=(10, 8))
# #     sns.heatmap(pivot, annot=annot, fmt='', cmap='RdBu_r', center=0, 
# #                 vmin=-0.5, vmax=0.5, cbar_kws={'label': 'Correlation'})
# #     plt.title(f'{event_type}事件 与 迁移的相关性\n(*, **, *** 表示 p<0.10, 0.05, 0.01)', 
# #               fontsize=14, pad=20)
# #     plt.xlabel('迁移方向', fontsize=12)
# #     plt.ylabel('事件类型', fontsize=12)
# #     plt.tight_layout()
# #     plt.savefig(output_filename, dpi=300, bbox_inches='tight')
# #     print(f"✅ 热力图已保存: {output_filename}")
# #     plt.close()

# # create_heatmap(results_p, 'P', 'heatmap_p_events.png')
# # create_heatmap(results_q, 'Q', 'heatmap_q_events.png')

# # # ============= 对比图：P vs Q =============
# # print("\n📊 生成对比图...")

# # def create_comparison_plot(results_p, results_q, output_filename):
# #     """对比P事件和Q事件与迁移的相关性"""
    
# #     # 筛选总计数据
# #     df_p = results_p[results_p['Coin'] == 'TOTAL'].groupby('Direction')['Correlation'].mean()
# #     df_q = results_q[results_q['Coin'] == 'TOTAL'].groupby('Direction')['Correlation'].mean()
    
# #     # 合并
# #     df_compare = pd.DataFrame({
# #         'P事件': df_p,
# #         'Q事件': df_q
# #     })
    
# #     # 绘图
# #     fig, ax = plt.subplots(figsize=(10, 6))
# #     df_compare.plot(kind='bar', ax=ax, width=0.7, color=['#d62728', '#1f77b4'])
    
# #     ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
# #     ax.set_ylabel('平均相关系数', fontsize=12)
# #     ax.set_xlabel('迁移方向', fontsize=12)
# #     ax.set_title('P事件 vs Q事件 与迁移的相关性对比', fontsize=14, pad=20)
# #     ax.legend(title='事件类型', fontsize=11)
# #     ax.grid(axis='y', alpha=0.3)
    
# #     plt.xticks(rotation=0)
# #     plt.tight_layout()
# #     plt.savefig(output_filename, dpi=300, bbox_inches='tight')
# #     print(f"✅ 对比图已保存: {output_filename}")
# #     plt.close()

# # create_comparison_plot(results_p, results_q, 'comparison_p_vs_q.png')

# # # ============= 关键发现总结 =============
# # print("\n" + "="*100)
# # print("🎯 关键发现总结")
# # print("="*100)

# # def summarize_findings(results, event_type):
# #     """总结关键发现"""
# #     print(f"\n【{event_type}事件】")
    
# #     # 总迁入
# #     df_in = results[(results['Direction'] == 'in') & (results['Coin'] == 'TOTAL')]
# #     if len(df_in) > 0:
# #         avg_corr_in = df_in['Correlation'].mean()
# #         sig_in = (df_in['P_value'] < 0.05).sum()
# #         print(f"  与迁入的平均相关性: {avg_corr_in:+.4f} (显著: {sig_in}/{len(df_in)})")
    
# #     # 总迁出
# #     df_out = results[(results['Direction'] == 'out') & (results['Coin'] == 'TOTAL')]
# #     if len(df_out) > 0:
# #         avg_corr_out = df_out['Correlation'].mean()
# #         sig_out = (df_out['P_value'] < 0.05).sum()
# #         print(f"  与迁出的平均相关性: {avg_corr_out:+.4f} (显著: {sig_out}/{len(df_out)})")
    
# #     # 净迁移
# #     df_net = results[(results['Direction'] == 'net') & (results['Coin'] == 'TOTAL')]
# #     if len(df_net) > 0:
# #         avg_corr_net = df_net['Correlation'].mean()
# #         sig_net = (df_net['P_value'] < 0.05).sum()
# #         print(f"  与净迁移的平均相关性: {avg_corr_net:+.4f} (显著: {sig_net}/{len(df_net)})")
    
# #     # 判断
# #     if len(df_in) > 0 and len(df_out) > 0:
# #         if abs(avg_corr_out) > abs(avg_corr_in):
# #             print(f"  ⚠️  迁出相关性 > 迁入相关性！可能存在遗漏迁出偏误")
# #         else:
# #             print(f"  ✅ 迁入相关性 > 迁出相关性")

# # summarize_findings(results_p, 'P')
# # summarize_findings(results_q, 'Q')

# # print("\n" + "="*100)
# # print("✅ 分析完成！")
# # print("="*100)


# # import pandas as pd
# # import numpy as np
# # from scipy.stats import pearsonr
# # import seaborn as sns
# # import matplotlib.pyplot as plt
# # from sklearn.linear_model import LinearRegression
# # from sklearn.preprocessing import StandardScaler

# # # 加载数据
# # df = pd.read_csv("/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv")
# # df_mig = pd.read_csv("/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv")

# # df['date'] = pd.to_datetime(df['date'])
# # df_mig['date'] = pd.to_datetime(df_mig['date'])

# # # 选择窗口
# # df = df[(df['date'] >= '2017-01-01') & (df['date'] <= '2019-01-01')]
# # df_merged = df.merge(df_mig, on='date', how='left').fillna(0)

# # # ===================================================================
# # # 诊断1：迁入 vs 价格的相关性
# # # ===================================================================
# # print("="*80)
# # print("🔍 诊断1：迁入与价格的相关性")
# # print("="*80)

# # # 总迁入
# # df_merged['total_in'] = df_merged['total_in'].fillna(0)

# # # 价格变量
# # price_vars = ['eth_price_lag1', 'eth_ma_7d', 'eth_ma_14d', 'eth_ma_21d', 'eth_ma_30d']

# # for price_var in price_vars:
# #     if price_var in df_merged.columns:
# #         try:
# #             corr, pval = pearsonr(df_merged[price_var].fillna(0), df_merged['total_in'])
# #             significance = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else ""))
# #             print(f"  {price_var:20s}: r={corr:6.3f}, p={pval:.4f} {significance}")
# #         except Exception as e:
# #             print(f"  {price_var:20s}: 计算失败")

# # # ===================================================================
# # # 诊断2：迁入 vs 协议事件的相关性
# # # ===================================================================
# # print("\n" + "="*80)
# # print("🔍 诊断2：迁入与协议事件的相关性")
# # print("="*80)

# # event_vars = [
# #     'eth_p_event_lag1', 'eth_p_event_sum_7', 
# #     'eth_q_event_lag1', 'eth_q_event_sum_7',
# #     'eth_p_eip_event_lag1', 'eth_q_eip_event_lag1'
# # ]

# # for event_var in event_vars:
# #     if event_var in df_merged.columns:
# #         try:
# #             corr, pval = pearsonr(df_merged[event_var].fillna(0), df_merged['total_in'])
# #             significance = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else ""))
# #             print(f"  {event_var:30s}: r={corr:6.3f}, p={pval:.4f} {significance}")
# #         except Exception as e:
# #             print(f"  {event_var:30s}: 计算失败")

# # # ===================================================================
# # # 诊断3：各竞争链迁入的相关性矩阵
# # # ===================================================================
# # print("\n" + "="*80)
# # print("🔍 诊断3：各竞争链迁入之间的相关性")
# # print("="*80)

# # inflow_cols = ['in_from_BTC', 'in_from_SOLANA', 'in_from_BNB', 'in_from_OPTIMISM', 
# #                'in_from_APTOS', 'in_from_SUI', 'in_from_NEAR', 'in_from_ZKSYNC', 
# #                'in_from_ARBITRUM', 'in_from_HARMONY', 'in_from_ETC', 'in_from_ETHPOW']

# # available_inflow = [col for col in inflow_cols if col in df_merged.columns]
# # df_inflow = df_merged[available_inflow].fillna(0)

# # # 计算相关性矩阵
# # corr_matrix = df_inflow.corr()

# # # 显示高度相关的对（r > 0.7）
# # print("\n高度相关的迁入对（|r| > 0.7）:")
# # high_corr_found = False
# # for i in range(len(corr_matrix.columns)):
# #     for j in range(i+1, len(corr_matrix.columns)):
# #         corr_val = corr_matrix.iloc[i, j]
# #         if abs(corr_val) > 0.7:
# #             high_corr_found = True
# #             print(f"  {corr_matrix.columns[i]:20s} <-> {corr_matrix.columns[j]:20s}: r={corr_val:.3f}")

# # if not high_corr_found:
# #     print("  未发现高度相关的变量对（这是好事！）")

# # # 热力图
# # try:
# #     plt.figure(figsize=(12, 10))
# #     sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
# #                 square=True, linewidths=1, cbar_kws={"shrink": 0.8})
# #     plt.title('迁入变量相关性矩阵', fontsize=14, pad=20)
# #     plt.tight_layout()
# #     plt.savefig('eth_inflow_correlation_matrix.png', dpi=300, bbox_inches='tight')
# #     print("\n✅ 相关性热力图已保存: eth_inflow_correlation_matrix.png")
# # except Exception as e:
# #     print(f"\n⚠️ 无法生成热力图: {e}")

# # # ===================================================================
# # # 诊断4：方差膨胀因子（VIF）- 手动实现
# # # ===================================================================
# # print("\n" + "="*80)
# # print("🔍 诊断4：方差膨胀因子（VIF）检验")
# # print("="*80)

# # def calculate_vif_manual(X, feature_idx):
# #     """
# #     手动计算VIF
# #     VIF_i = 1 / (1 - R²_i)
# #     """
# #     # 提取第i个特征作为因变量
# #     y = X[:, feature_idx]
    
# #     # 其他特征作为自变量
# #     X_others = np.delete(X, feature_idx, axis=1)
    
# #     if X_others.shape[1] == 0:
# #         return 1.0
    
# #     # 线性回归
# #     model = LinearRegression()
# #     model.fit(X_others, y)
    
# #     # 计算R²
# #     y_pred = model.predict(X_others)
# #     ss_res = np.sum((y - y_pred)**2)
# #     ss_tot = np.sum((y - np.mean(y))**2)
    
# #     if ss_tot == 0:
# #         return np.inf
    
# #     r_squared = 1 - (ss_res / ss_tot)
    
# #     # VIF = 1 / (1 - R²)
# #     if r_squared >= 0.999:
# #         return np.inf
    
# #     vif = 1 / (1 - r_squared)
    
# #     return vif

# # # 构建设计矩阵
# # X_vars = ['eth_price_lag1', 'eth_p_event_sum_7', 'eth_q_event_sum_7', 'total_in']
# # X_vars_available = [v for v in X_vars if v in df_merged.columns]

# # X = df_merged[X_vars_available].fillna(0).values

# # # 计算VIF
# # print("\nVIF值（VIF > 10 表示严重多重共线性）:")
# # for i, var in enumerate(X_vars_available):
# #     try:
# #         vif = calculate_vif_manual(X, i)
        
# #         if np.isinf(vif):
# #             severity = "🔥🔥 极严重（完全共线）"
# #             vif_str = "∞"
# #         elif vif > 10:
# #             severity = "🔥 严重"
# #             vif_str = f"{vif:7.2f}"
# #         elif vif > 5:
# #             severity = "⚠️  中等"
# #             vif_str = f"{vif:7.2f}"
# #         else:
# #             severity = "✅ 轻微"
# #             vif_str = f"{vif:7.2f}"
        
# #         print(f"  {var:30s}: VIF={vif_str}  {severity}")
# #     except Exception as e:
# #         print(f"  {var:30s}: 计算失败 ({e})")

# # # ===================================================================
# # # 诊断5：条件数（Condition Number）
# # # ===================================================================
# # print("\n" + "="*80)
# # print("🔍 诊断5：条件数检验")
# # print("="*80)

# # try:
# #     # 标准化后计算条件数
# #     scaler = StandardScaler()
# #     X_scaled = scaler.fit_transform(X)
    
# #     cond_num = np.linalg.cond(X_scaled)
# #     print(f"\n条件数: {cond_num:.2f}")
    
# #     if cond_num > 30:
# #         print("  🔥 严重多重共线性（条件数 > 30）")
# #     elif cond_num > 15:
# #         print("  ⚠️  中等多重共线性（条件数 > 15）")
# #     else:
# #         print("  ✅ 多重共线性较轻（条件数 < 15）")
# # except Exception as e:
# #     print(f"⚠️ 无法计算条件数: {e}")

# # print("\n" + "="*80)
# # print("✅ 诊断完成")
# # print("="*80)

# # # ===================================================================
# # # 额外：计算各迁入变量的描述统计
# # # ===================================================================
# # print("\n" + "="*80)
# # print("📊 迁入变量描述统计")
# # print("="*80)

# # for col in available_inflow:
# #     data = df_merged[col].fillna(0)
# #     non_zero = data[data > 0]
    
# #     print(f"\n{col}:")
# #     print(f"  总数: {data.sum():,.0f}")
# #     print(f"  非零天数: {len(non_zero)}/{len(data)} ({len(non_zero)/len(data)*100:.1f}%)")
# #     if len(non_zero) > 0:
# #         print(f"  均值: {data.mean():.2f}")
# #         print(f"  中位数: {data.median():.2f}")
# #         print(f"  标准差: {data.std():.2f}")
# #         print(f"  最大值: {data.max():.0f}")


# import numpy as np
# import pandas as pd

# # ========================================
# # 手动计算VIF
# # ========================================

# def calculate_vif_manual(X):
#     """手动计算VIF"""
#     n, p = X.shape
#     vif_values = []
    
#     for j in range(p):
#         y = X[:, j]
#         X_others = np.delete(X, j, axis=1)
        
#         try:
#             beta = np.linalg.lstsq(X_others, y, rcond=None)[0]
#             y_pred = X_others @ beta
            
#             ss_res = np.sum((y - y_pred)**2)
#             ss_tot = np.sum((y - y.mean())**2)
#             r_squared = 1 - (ss_res / ss_tot)
            
#             vif = 1 / (1 - r_squared + 1e-10)
#             vif_values.append(vif)
#         except:
#             vif_values.append(np.nan)
    
#     return np.array(vif_values)


# # ========================================
# # 加载数据
# # ========================================

# # print("="*70)
# # print("🔍 加载数据")
# # print("="*70)

# # df = pd.read_csv("/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv")

# # print(f"\n原始数据：")
# # print(f"  行数: {len(df)}")

# # # 🔥 检查date列格式
# # print(f"\ndate列信息：")
# # print(f"  数据类型: {df['date'].dtype}")
# # print(f"  前5行: {df['date'].head().tolist()}")

# # # 转换日期
# # df['date'] = pd.to_datetime(df['date'])
# # print(f"  转换后日期范围: {df['date'].min()} 到 {df['date'].max()}")

# # # 🔥 过滤日期（检查是否有数据）
# # df_filtered = df[(df['date'] >= '2017-01-01') & (df['date'] <= '2019-01-01')].copy()

# # print(f"\n过滤后数据：")
# # print(f"  行数: {len(df_filtered)}")

# # if len(df_filtered) == 0:
# #     print("\n❌ 错误：过滤后没有数据！")
# #     print("\n可能原因：")
# #     print("  1. 日期范围不对")
# #     print("  2. date列格式问题")
    
# #     print("\n尝试使用全部数据...")
# #     df_filtered = df.copy()
# #     print(f"  使用全部数据：{len(df_filtered)}行")

# # # ========================================
# # # 提取价格和事件数据
# # # ========================================

# # print("\n" + "="*70)
# # print("📊 提取变量")
# # print("="*70)

# # # 检查列是否存在
# # print(f"\n检查列名：")
# # print(f"  'btc_ma_7d' 存在? {('btc_ma_7d' in df_filtered.columns)}")
# # print(f"  'btc_p_event_vol_7' 存在? {('btc_p_event_vol_7' in df_filtered.columns)}")

# # if 'btc_ma_7d' not in df_filtered.columns:
# #     print(f"\n可用列：")
# #     print(df_filtered.columns.tolist())
# #     exit()

# # # 提取数据
# # price = df_filtered['btc_ma_7d'].values
# # event = df_filtered['btc_p_event_vol_7'].values

# # print(f"\n数据统计：")
# # print(f"  价格（btc_ma_7d）：")
# # print(f"    长度: {len(price)}")
# # print(f"    均值: {np.mean(price):.2f}")
# # print(f"    标准差: {np.std(price):.2f}")
# # print(f"    缺失值: {np.isnan(price).sum()}")

# # print(f"\n  事件（btc_p_event_vol_7）：")
# # print(f"    长度: {len(event)}")
# # print(f"    均值: {np.mean(event):.4f}")
# # print(f"    标准差: {np.std(event):.4f}")
# # print(f"    缺失值: {np.isnan(event).sum()}")

# # # 处理缺失值
# # if np.isnan(price).any() or np.isnan(event).any():
# #     print(f"\n⚠️ 发现缺失值，删除...")
# #     mask = ~(np.isnan(price) | np.isnan(event))
# #     price = price[mask]
# #     event = event[mask]
# #     print(f"  删除后长度: {len(price)}")

# # # 标准化
# # price_std = (price - np.mean(price)) / (np.std(price) + 1e-10)
# # event_std = (event - np.mean(event)) / (np.std(event) + 1e-10)

# # # 交互项
# # interaction = price_std * event_std

# # # ========================================
# # # 多重共线性诊断
# # # ========================================

# # print("\n" + "="*70)
# # print("🔥 多重共线性诊断（Price × Event 交互项）")
# # print("="*70)

# # # 1. 相关系数
# # print(f"\n📊 相关系数：")
# # corr_price_event = np.corrcoef(price_std, event_std)[0, 1]
# # corr_price_interaction = np.corrcoef(price_std, interaction)[0, 1]
# # corr_event_interaction = np.corrcoef(event_std, interaction)[0, 1]

# # print(f"  Corr(price, event)       = {corr_price_event:7.3f}")
# # print(f"  Corr(price, interaction) = {corr_price_interaction:7.3f}")
# # print(f"  Corr(event, interaction) = {corr_event_interaction:7.3f}")

# # # 判断
# # if abs(corr_price_event) > 0.7:
# #     print(f"\n❌ price和event高度相关（|r| = {abs(corr_price_event):.3f} > 0.7）")
# #     print(f"   → 严重多重共线性风险")
# # elif abs(corr_price_event) > 0.5:
# #     print(f"\n⚠️ price和event中度相关（|r| = {abs(corr_price_event):.3f} > 0.5）")
# #     print(f"   → 中度多重共线性风险")
# # else:
# #     print(f"\n✅ price和event相关性较低（|r| = {abs(corr_price_event):.3f} < 0.5）")

# # # 2. VIF
# # print(f"\n📊 VIF（方差膨胀因子）：")
# # X = np.column_stack([price_std, event_std, interaction])
# # vif_values = calculate_vif_manual(X)

# # vif_data = pd.DataFrame({
# #     "Variable": ["price", "event", "interaction"],
# #     "VIF": vif_values
# # })
# # print(vif_data.to_string(index=False))

# # # 判断VIF
# # max_vif = np.max(vif_values)
# # if max_vif > 10:
# #     print(f"\n❌ 严重多重共线性（max VIF = {max_vif:.1f} > 10）")
# #     print(f"   后果：参数估计极不稳定，p值不可靠")
# # elif max_vif > 5:
# #     print(f"\n⚠️ 中度多重共线性（max VIF = {max_vif:.1f} > 5）")
# #     print(f"   建议：谨慎使用交互项")
# # else:
# #     print(f"\n✅ 多重共线性可接受（max VIF = {max_vif:.1f} < 5）")

# # # 3. 条件数
# # print(f"\n📊 条件数（Condition Number）：")
# # try:
# #     cond_number = np.linalg.cond(X.T @ X)
# #     print(f"  Condition Number = {cond_number:.1f}")
    
# #     if cond_number > 100:
# #         print(f"  ❌ 条件数 > 100，严重共线性")
# #     elif cond_number > 30:
# #         print(f"  ⚠️ 条件数 > 30，中度共线性")
# #     else:
# #         print(f"  ✅ 条件数 < 30，可接受")
# # except:
# #     print(f"  ⚠️ 无法计算条件数")

# # # ========================================
# # # 结论与建议
# # # ========================================

# # print("\n" + "="*70)
# # print("💡 诊断结论")
# # print("="*70)

# # # 综合判断
# # high_corr = abs(corr_price_event) > 0.6
# # high_vif = max_vif > 5

# # if high_corr and high_vif:
# #     print("\n❌ 强烈不推荐使用交互项")
# #     print("\n原因：")
# #     print(f"  1. price和event高度相关（r = {corr_price_event:.3f}）")
# #     print(f"  2. 交互项VIF过高（{max_vif:.1f}）")
# #     print(f"  3. 这会导致：")
# #     print(f"     - 参数估计不稳定")
# #     print(f"     - 标准误膨胀（p值不可靠）")
# #     print(f"     - 系数符号可能翻转")
    
# #     print("\n✅ 推荐：")
# #     print("  使用加法模型：p(t) = p0 + α·price + β·event")
# #     print("  不包含交互项")
    
# # elif high_corr or high_vif:
# #     print("\n⚠️ 谨慎使用交互项")
# #     print(f"  相关性: {corr_price_event:.3f}")
# #     print(f"  最大VIF: {max_vif:.1f}")
    
# #     print("\n建议：")
# #     print("  1. 主模型：不用交互项")
# #     print("  2. 稳健性检验：报告交互模型结果")
# #     print("  3. 说明交互项不稳定的原因")
    
# # else:
# #     print("\n✅ 可以尝试交互项")
# #     print(f"  相关性较低: {corr_price_event:.3f}")
# #     print(f"  VIF可接受: {max_vif:.1f}")
    
# #     print("\n但仍需检查：")
# #     print("  - 交互系数是否显著")
# #     print("  - AIC/BIC是否改善")
# #     print("  - 核心发现是否稳健")

# # print("\n" + "="*70)


# # 最终代码什么都有了 指标加全了-ETH
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "eth_bass_pqfit_results_inflow_outflow_network20172019-test-eip.csv"

# # 2017-2019
# COMPETITORS = ["BTC", "Solana","Cosmos", "TRON"]


# P_EVENT_LIST = [
#     "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "eth_q_event_lag1","eth_q_event_sum_7","eth_q_event_vol_7"
# ]
# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "eth_price_lag1","eth_ma_7d","eth_vol_7d","eth_return_7d"
# ]

# # ----------------- 评估指标 -----------------
# def compute_metrics(y_true, y_pred, k):
#     """
#     计算全套拟合优度指标。
#     y_true: 真实值数组
#     y_pred: 预测值数组
#     k:      模型参数个数（用于 adjusted R²）
#     返回: dict
#     """
#     y_true = np.array(y_true, dtype=float)
#     y_pred = np.array(y_pred, dtype=float)
#     n = len(y_true)
#     resid = y_true - y_pred

#     sse  = np.sum(resid ** 2)
#     mse  = sse / n
#     rmse = math.sqrt(mse)
#     mad  = np.mean(np.abs(resid))

#     ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
#     r2 = 1 - sse / ss_tot if ss_tot > 0 else np.nan

#     # Adjusted R²
#     if n - k - 1 > 0 and ss_tot > 0:
#         adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k - 1)
#     else:
#         adj_r2 = np.nan

#     # MAPE: 跳过 y_true == 0 的点，避免除零
#     mask = y_true != 0
#     mape = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan

#     # WAPE = sum|resid| / sum|y_true|
#     denom = np.sum(np.abs(y_true))
#     wape = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan

#     return {
#         "MAD":      mad,
#         "SSE":      sse,
#         "MSE":      mse,
#         "RMSE":     rmse,
#         "R2":       r2,
#         "Adj_R2":   adj_r2,
#         "MAPE":     mape,
#         "WAPE":     wape,
#     }

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# def compute_q_t_from_array(event_arr, q_params, q_form):
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     ev = normalize(df[p_event_col].values)
#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * ev
#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
#     else:
#         raise ValueError("未知 p_model")
#     return np.maximum(p_t, 0)

# def get_param_indices(p_model):
#     n_comp = len(COMPETITORS)
#     p_param_count = 3 if p_model in ["additive", "nonlinear_event"] else 4
#     q_start     = p_param_count
#     gamma_start = q_start + 2
#     delta_start = gamma_start + n_comp
#     m_idx       = delta_start + n_comp
#     total       = m_idx + 1
#     return p_param_count, q_start, gamma_start, delta_start, m_idx, total

# def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, inflow_dict, outflow_dict, gamma_in_params, delta_out_params):
#     remaining = np.maximum(m - N_lag, 0)
#     base_rate = p_t_arr + q_t_arr * (N_lag / m)

#     inflow_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in inflow_dict:
#             M_in = inflow_dict[coin]
#             M_in_lag = np.concatenate([[0], M_in[:-1]])
#             M_in_norm = normalize(M_in_lag)
#             inflow_network_rate += gamma_in_params[i] * M_in_norm

#     outflow_network_rate = np.zeros_like(N_lag)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in outflow_dict:
#             M_out = outflow_dict[coin]
#             M_out_lag = np.concatenate([[0], M_out[:-1]])
#             M_out_norm = normalize(M_out_lag)
#             outflow_network_rate += delta_out_params[i] * M_out_norm

#     total_rate = base_rate + inflow_network_rate - outflow_network_rate
#     constrained_growth = total_rate * remaining

#     direct_migration = np.zeros_like(N_lag)
#     for coin in COMPETITORS:
#         if coin in inflow_dict:
#             direct_migration += inflow_dict[coin]

#     return constrained_growth + direct_migration

# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
#     p_param_count, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
#     p_params        = params[:p_param_count]
#     q0, beta_q      = params[q_start], params[q_start + 1]
#     gamma_in_params = params[gamma_start: gamma_start + len(COMPETITORS)]
#     delta_out_params= params[delta_start: delta_start + len(COMPETITORS)]
#     m               = params[m_idx]
#     p_t  = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t  = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag= df["N_lag"].values
#     dN   = dN_pred_from_Nlag(N_lag, p_t, q_t, m, inflow_dict, outflow_dict, gamma_in_params, delta_out_params)
#     return dN, p_t, q_t

# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
#     _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
#     q0 = params[q_start]
#     m  = params[m_idx]
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return df[NEW_COL].values - dN_predicted

# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
#         n_comp  = len(COMPETITORS)
#         _, q_start, gamma_start, delta_start, m_idx, total = get_param_indices(p_model)

#         if p_model in ["additive", "nonlinear_event"]:
#             p_init = [0.001, 0.01, 0.01];  p_lo = [0, -10, -10];  p_hi = [1, 10, 10]
#         else:
#             p_init = [0.001, 0.01, 0.01, 0.01];  p_lo = [0, -10, -10, -10];  p_hi = [1, 10, 10, 10]

#         q_init = [0.01, 0.01];  q_lo = [0, -10];  q_hi = [1, 10]
#         gamma_init = [0.0001] * n_comp;  gamma_lo = [-0.01] * n_comp;  gamma_hi = [0.01] * n_comp
#         delta_init = [0.0001] * n_comp;  delta_lo = [-0.01] * n_comp;  delta_hi = [0.01] * n_comp

#         init   = p_init + q_init + gamma_init + delta_init + [m_guess]
#         lo     = p_lo   + q_lo   + gamma_lo   + delta_lo   + [0.9 * m_guess]
#         hi     = p_hi   + q_hi   + gamma_hi   + delta_hi   + [20  * m_guess]

#         res = least_squares(residuals_pair, init, bounds=(lo, hi),
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict),
#                             method="trf")
#         if not res.success:
#             return None

#         params = res.x
#         eps = 1e-6
#         n   = len(df)
#         k   = len(params)

#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)

#         J = []
#         for i in range(k):
#             p_eps = params.copy();  p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T

#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except np.linalg.LinAlgError:
#             cond = np.nan

#         resid_vec = df[NEW_COL].values - y_pred
#         sigma2    = np.sum(resid_vec**2) / (n - k)

#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se  = np.sqrt(np.diag(cov))
#         except np.linalg.LinAlgError:
#             se = np.full(k, np.nan)

#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
#         return res

#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # --------- 加载迁移数据 ----------
# def load_migration_data(migration_path, main_df):
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}");  return None, None

#     print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
#     print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
#     print(f"📊 迁移数据行数: {len(df_mig)}")

#     if 'date' not in df_mig.columns:
#         print("⚠️ 迁移数据缺少 'date' 列");  return None, None

#     date_range = pd.date_range(start=main_df[DATE_COL].min(), end=main_df[DATE_COL].max(), freq='D')
#     df_full    = pd.DataFrame({DATE_COL: date_range})
#     df_merged  = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')

#     # 列名映射：coin -> 文件中实际列名（根据需要修改/扩充）
#     inflow_col_mapping = {
#         # "Aptos": "in_from_Aptos",
#         # "Alephzero": "in_from_Alephzero",
#         # "Arbitrum": "in_from_Arbitrum",
#         # "Arweave": "in_from_Arweave",
#         # "Avalanche": "in_from_Avalanche",
#         # "Besu": "in_from_Besu",
#         # "BNBChain": "in_from_BNBChain",
#         "BTC": "in_from_BTC",
#         "Cosmos": "in_from_Cosmos",
#         # "ETC": "in_from_ETC",
#         # "Erigon": "in_from_Erigon",
#         # "Ethereumpow": "in_from_Ethereumpow",
#         # "FLOW": "in_from_FLOW",
#         # "Harmony": "in_from_Harmony",
#         # "Helium": "in_from_Helium",
#         # "Near": "in_from_Near",
#         # "Nethermind": "in_from_Nethermind",
#         # "Optimism": "in_from_Optimism",
#         # "Polkadot": "in_from_Polkadot",
#         # "Polygon": "in_from_Polygon",
#         # "Reth": "in_from_Reth",
#         # "Ronin": "in_from_Ronin",
#         # "SKALE": "in_from_SKALE",
#         # "Sui": "in_from_Sui",
#         # "SecretNetwork": "in_from_SecretNetwork",
#         "Solana": "in_from_Solana",
#         # "Starknet": "in_from_Starknet",
#         # "THETA": "in_from_THETA",
#         "TRON": "in_from_TRON",
#         # "Zksync": "in_from_Zksync",
#     }
    
#     outflow_col_mapping = {
#         # "Aptos": "out_to_Aptos",
#         # "Alephzero": "out_to_Alephzero",
#         # "Arbitrum": "out_to_Arbitrum",
#         # "Arweave": "out_to_Arweave",
#         # "Avalanche": "out_to_Avalanche",
#         # "Besu": "out_to_Besu",
#         # "BNBChain": "out_to_BNBChain",
#         "BTC": "out_to_BTC",
#         "Cosmos": "out_to_Cosmos",
#         # "ETC": "out_to_ETC",
#         # "Erigon": "out_to_Erigon",
#         # "Ethereumpow": "out_to_Ethereumpow",
#         # "FLOW": "out_to_FLOW",
#         # "Harmony": "out_to_Harmony",
#         # "Helium": "out_to_Helium",
#         # "Near": "out_to_Near",
#         # "Nethermind": "out_to_Nethermind",
#         # "Optimism": "out_to_Optimism",
#         # "Polkadot": "out_to_Polkadot",
#         # "Polygon": "out_to_Polygon",
#         # "Reth": "out_to_Reth",
#         # "Ronin": "out_to_Ronin",
#         # "SKALE": "out_to_SKALE",
#         # "Sui": "out_to_Sui",
#         # "SecretNetwork": "out_to_Secretnetwork",  # 注意这里文件里是小写 n
#         "Solana": "out_to_Solana",
#         # "Starknet": "out_to_Starknet",
#         # "THETA": "out_to_THETA",
#         "TRON": "out_to_TRON",
#         # "Zksync": "out_to_Zksync",
#     }

#     df_merged_indexed = df_merged.set_index(DATE_COL)
#     main_dates        = pd.DatetimeIndex(main_df[DATE_COL].values)
#     inflow_dict_aligned  = {}
#     outflow_dict_aligned = {}

#     for coin in COMPETITORS:
#         actual_col = inflow_col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             inflow_dict_aligned[coin] = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁入数据列: {actual_col}")
#         else:
#             inflow_dict_aligned[coin] = np.zeros(len(main_df))
#             print(f"⚠️ 未找到 {coin} 对应的迁入列: {actual_col}")

#         actual_col = outflow_col_mapping.get(coin)
#         if actual_col and actual_col in df_merged.columns:
#             outflow_dict_aligned[coin] = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
#             print(f"✅ 成功加载 {coin} 的迁出数据列: {actual_col}")
#         else:
#             outflow_dict_aligned[coin] = np.zeros(len(main_df))
#             print(f"⚠️ 未找到 {coin} 对应的迁出列: {actual_col}")

#     print("\n📈 迁移数据统计（窗口期内）:")
#     print("🔥 方法：网络效应中迁入和迁出都使用标准化值(t-1)，直接迁入使用原始值(t)")
#     for coin in COMPETITORS:
#         M_in  = inflow_dict_aligned[coin]
#         M_out = outflow_dict_aligned[coin]
#         nz_in  = np.sum(M_in  > 0)
#         nz_out = np.sum(M_out > 0)
#         if nz_in > 0 or nz_out > 0:
#             print(f"  {coin:20s}:")
#             print(f"    迁入: 总数={np.sum(M_in):6.0f}, 非零天数={nz_in:4d}")
#             print(f"    迁出: 总数={np.sum(M_out):6.0f}, 非零天数={nz_out:4d}")
#         else:
#             print(f"  {coin:20s}: 无数据")

#     return inflow_dict_aligned, outflow_dict_aligned

# # ----------------- 主程序 -----------------
# def main():
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}");  sys.exit(1)

#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
#     results       = []
#     combos_done   = 0
#     combos_skipped= 0

#     for p_event_col in P_EVENT_LIST:
#         for q_event_col in Q_EVENT_LIST:
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + list(PRICE_LAG_COLS)
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失: {missing[:5]}")
#                 combos_skipped += 1;  continue

#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + list(PRICE_LAG_COLS)].copy()
#             df = df.fillna(method="ffill").fillna(0)
#             df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()

#             if df.empty:
#                 print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1;  continue

#             # ===== 各peak独立归零 =====
#             cum_offset = df[CUM_COL].iloc[0] - df[NEW_COL].iloc[0]
#             df[CUM_COL] = df[CUM_COL] - cum_offset
#             df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values
#             # ==========================

#             inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df)
#             if inflow_dict is None or outflow_dict is None:
#                 print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
#                 combos_skipped += 1;  continue

#             for price_col in PRICE_LAG_COLS:
#                 raw_price = df[price_col].values.astype(float)
#                 try:
#                     price_transforms = {
#                         "linear": normalize(raw_price),
#                         "log":    normalize(np.log(np.maximum(raw_price, 1e-8))),
#                         "exp":    normalize(np.exp(np.clip(raw_price, -50, 50)))
#                     }
#                 except Exception:
#                     print(f"⚠️ price transform error for {price_col}, skipping.");  continue

#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             model_tag = (f"P={p_event_col} | Q={q_event_col} | "
#                                          f"price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}")
#                             print(f"\n→ 拟合: {model_tag}")

#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
#                             if res is None:
#                                 print(" ✖ 拟合失败或不收敛，跳过。")
#                                 combos_skipped += 1;  continue

#                             combos_done += 1
#                             params = res.x
#                             k      = len(params)

#                             dN_pred, p_t, q_t = compute_prediction_pair(
#                                 df, params, price_arr, p_event_col, q_event_col,
#                                 p_model, q_form, inflow_dict, outflow_dict)

#                             # -------- 计算全套指标 --------
#                             metrics = compute_metrics(df[NEW_COL].values, dN_pred, k)

#                             # 动态生成参数名
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma_price", "q0", "beta_q"]
#                             for coin in COMPETITORS:
#                                 param_names.append(f"gamma_in_{coin}")
#                             for coin in COMPETITORS:
#                                 param_names.append(f"delta_out_{coin}")
#                             param_names.append("m")

#                             row = {
#                                 "P_event":   p_event_col,
#                                 "Q_event":   q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf":  pt_name,
#                                 "p_model":   p_model,
#                                 "q_form":    q_form,
#                                 # ---- 全套指标 ----
#                                 "MAD":     metrics["MAD"],
#                                 "SSE":     metrics["SSE"],
#                                 "MSE":     metrics["MSE"],
#                                 "RMSE":    metrics["RMSE"],
#                                 "R2":      metrics["R2"],
#                                 "Adj_R2":  metrics["Adj_R2"],
#                                 "MAPE":    metrics["MAPE"],
#                                 "WAPE":    metrics["WAPE"],
#                                 "cond":    float(getattr(res, "cond", np.nan))
#                             }

#                             for i, name in enumerate(param_names):
#                                 row[name]          = float(params[i]) if i < len(params) else np.nan
#                                 row["se_" + name]  = float(res.se[i])    if hasattr(res, "se")    and i < len(res.se)    else np.nan
#                                 row["t_"  + name]  = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
#                                 row["p_"  + name]  = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan

#                             results.append(row)

#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
#     print(f"✅ 结果已保存：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()


# ETH 版本1：inflow 和 outflow 网络效应都使用原始值（不标准化）
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"
OUTPUT_CSV = "eth_bass_pqfit_results_inflow_outflow_network20172019-raw.csv"

COMPETITORS = ["BTC", "Solana", "Cosmos", "TRON"]

P_EVENT_LIST = [
    "eth_p_event_lag1","eth_p_event_sum_7"
    #,"eth_p_event_vol_7"
]
Q_EVENT_LIST = [
    "eth_q_event_lag1","eth_q_event_sum_7"
    #,"eth_q_event_vol_7"
]
PRICE_LAG_COLS = [
    "eth_price_lag1","eth_ma_7d"
    #,"eth_vol_7d","eth_return_7d"
]

# ----------------- 评估指标 -----------------
def compute_metrics(y_true, y_pred, k):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    n = len(y_true)
    resid = y_true - y_pred
    sse   = np.sum(resid ** 2)
    mse   = sse / n
    rmse  = math.sqrt(mse)
    mad   = np.mean(np.abs(resid))
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    if n - k - 1 > 0 and ss_tot > 0:
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k - 1)
    else:
        adj_r2 = np.nan
    mask = y_true != 0
    mape = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
    denom = np.sum(np.abs(y_true))
    wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
    return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
            "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# ----------------- 工具函数 -----------------
def normalize(x):
    x = np.array(x, dtype=float)
    std = np.std(x)
    if std <= 0:
        return x - np.mean(x)
    return (x - np.mean(x)) / (std + 1e-12)

def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        return np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        return q0 * np.exp(beta * ev)
    else:
        raise ValueError("未知 q_form")

def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    if p_model == "additive":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * ev
    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
    elif p_model == "interaction_linear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
    elif p_model == "interaction_nonlinear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
    else:
        raise ValueError("未知 p_model")
    return np.maximum(p_t, 0)

def get_param_indices(p_model):
    n_comp = len(COMPETITORS)
    p_param_count = 3 if p_model in ["additive", "nonlinear_event"] else 4
    q_start     = p_param_count
    gamma_start = q_start + 2
    delta_start = gamma_start + n_comp
    m_idx       = delta_start + n_comp
    total       = m_idx + 1
    return p_param_count, q_start, gamma_start, delta_start, m_idx, total

def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, inflow_dict, outflow_dict, gamma_in_params, delta_out_params):
    remaining = np.maximum(m - N_lag, 0)
    base_rate = p_t_arr + q_t_arr * (N_lag / m)

    # *** 版本1：inflow 网络效应使用原始值 ***
    inflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            M_in = inflow_dict[coin]
            M_in_lag = np.concatenate([[0], M_in[:-1]])   # 原始值，不标准化
            inflow_network_rate += gamma_in_params[i] * M_in_lag

    # *** 版本1：outflow 网络效应使用原始值 ***
    outflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            M_out = outflow_dict[coin]
            M_out_lag = np.concatenate([[0], M_out[:-1]])  # 原始值，不标准化
            outflow_network_rate += delta_out_params[i] * M_out_lag

    total_rate = base_rate + inflow_network_rate - outflow_network_rate
    constrained_growth = total_rate * remaining

    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_migration += inflow_dict[coin]

    return constrained_growth + direct_migration

def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    p_param_count, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_params         = params[:p_param_count]
    q0, beta_q       = params[q_start], params[q_start + 1]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    m                = params[m_idx]
    p_t   = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t   = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    N_lag = df["N_lag"].values
    dN    = dN_pred_from_Nlag(N_lag, p_t, q_t, m, inflow_dict, outflow_dict, gamma_in_params, delta_out_params)
    return dN, p_t, q_t

def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
    q0 = params[q_start]
    m  = params[m_idx]
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_predicted

def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        n_comp  = len(COMPETITORS)
        _, q_start, gamma_start, delta_start, m_idx, total = get_param_indices(p_model)

        if p_model in ["additive", "nonlinear_event"]:
            p_init = [0.001, 0.01, 0.01];  p_lo = [0, -10, -10];  p_hi = [1, 10, 10]
        else:
            p_init = [0.001, 0.01, 0.01, 0.01];  p_lo = [0, -10, -10, -10];  p_hi = [1, 10, 10, 10]

        q_init = [0.01, 0.01];  q_lo = [0, -10];  q_hi = [1, 10]

        # *** 版本1：原始值量纲为人数，bounds 调整为 [-1, 1] ***
        gamma_init = [0.0001] * n_comp;  gamma_lo = [-1.0] * n_comp;  gamma_hi = [1.0] * n_comp
        delta_init = [0.0001] * n_comp;  delta_lo = [-1.0] * n_comp;  delta_hi = [1.0] * n_comp

        init = p_init + q_init + gamma_init + delta_init + [m_guess]
        lo   = p_lo   + q_lo   + gamma_lo   + delta_lo   + [0.9 * m_guess]
        hi   = p_hi   + q_hi   + gamma_hi   + delta_hi   + [20  * m_guess]

        res = least_squares(residuals_pair, init, bounds=(lo, hi),
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict),
                            method="trf")
        if not res.success:
            return None

        params = res.x
        eps = 1e-6
        n   = len(df)
        k   = len(params)

        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)

        J = []
        for i in range(k):
            p_eps = params.copy();  p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        resid_vec = df[NEW_COL].values - y_pred
        sigma2    = np.sum(resid_vec**2) / (n - k)
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se  = np.sqrt(np.diag(cov))
        except np.linalg.LinAlgError:
            se = np.full(k, np.nan)

        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None

# --------- 加载迁移数据 ----------
def load_migration_data(migration_path, main_df):
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}");  return None, None

    print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
    print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
    print(f"📊 迁移数据行数: {len(df_mig)}")

    date_range = pd.date_range(start=main_df[DATE_COL].min(), end=main_df[DATE_COL].max(), freq='D')
    df_full    = pd.DataFrame({DATE_COL: date_range})
    df_merged  = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')

    inflow_col_mapping = {
        "BTC": "in_from_BTC",
        "Cosmos": "in_from_Cosmos",
        "Solana": "in_from_Solana",
        "TRON": "in_from_TRON",
    }
    outflow_col_mapping = {
        "BTC": "out_to_BTC",
        "Cosmos": "out_to_Cosmos",
        "Solana": "out_to_Solana",
        "TRON": "out_to_TRON",
    }

    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates        = pd.DatetimeIndex(main_df[DATE_COL].values)
    inflow_dict_aligned  = {}
    outflow_dict_aligned = {}

    for coin in COMPETITORS:
        actual_col = inflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            inflow_dict_aligned[coin] = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
            print(f"✅ 成功加载 {coin} 的迁入数据列: {actual_col}")
        else:
            inflow_dict_aligned[coin] = np.zeros(len(main_df))
            print(f"⚠️ 未找到 {coin} 对应的迁入列: {actual_col}")

        actual_col = outflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            outflow_dict_aligned[coin] = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
            print(f"✅ 成功加载 {coin} 的迁出数据列: {actual_col}")
        else:
            outflow_dict_aligned[coin] = np.zeros(len(main_df))
            print(f"⚠️ 未找到 {coin} 对应的迁出列: {actual_col}")

    print("\n📈 迁移数据统计（窗口期内）:")
    print("🔥 版本1方法：inflow 和 outflow 网络效应均使用原始值（不标准化）")
    for coin in COMPETITORS:
        M_in  = inflow_dict_aligned[coin]
        M_out = outflow_dict_aligned[coin]
        nz_in  = np.sum(M_in  > 0)
        nz_out = np.sum(M_out > 0)
        if nz_in > 0 or nz_out > 0:
            print(f"  {coin:20s}:")
            print(f"    迁入: 总数={np.sum(M_in):6.0f}, 非零天数={nz_in:4d}")
            print(f"    迁出: 总数={np.sum(M_out):6.0f}, 非零天数={nz_out:4d}")
        else:
            print(f"  {coin:20s}: 无数据")

    return inflow_dict_aligned, outflow_dict_aligned

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}");  sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    results        = []
    combos_done    = 0
    combos_skipped = 0

    for p_event_col in P_EVENT_LIST:
        for q_event_col in Q_EVENT_LIST:
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + list(PRICE_LAG_COLS)
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失: {missing[:5]}")
                combos_skipped += 1;  continue

            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + list(PRICE_LAG_COLS)].copy()
            df = df.fillna(method="ffill").fillna(0)
            df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()

            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1;  continue

            cum_offset = df[CUM_COL].iloc[0] - df[NEW_COL].iloc[0]
            df[CUM_COL] = df[CUM_COL] - cum_offset
            df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

            inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df)
            if inflow_dict is None or outflow_dict is None:
                print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1;  continue

            for price_col in PRICE_LAG_COLS:
                raw_price = df[price_col].values.astype(float)
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log":    normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp":    normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    print(f"⚠️ price transform error for {price_col}, skipping.");  continue

                for pt_name, price_arr in price_transforms.items():
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            model_tag = (f"P={p_event_col} | Q={q_event_col} | "
                                         f"price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}")
                            print(f"\n→ 拟合: {model_tag}")
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
                            if res is None:
                                print(" ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1;  continue

                            combos_done += 1
                            params = res.x
                            k      = len(params)
                            dN_pred, p_t, q_t = compute_prediction_pair(
                                df, params, price_arr, p_event_col, q_event_col,
                                p_model, q_form, inflow_dict, outflow_dict)

                            metrics = compute_metrics(df[NEW_COL].values, dN_pred, k)

                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma_price", "q0", "beta_q"]
                            for coin in COMPETITORS:
                                param_names.append(f"gamma_in_{coin}")
                            for coin in COMPETITORS:
                                param_names.append(f"delta_out_{coin}")
                            param_names.append("m")

                            row = {
                                "P_event": p_event_col, "Q_event": q_event_col,
                                "price_col": price_col, "price_tf": pt_name,
                                "p_model": p_model, "q_form": q_form,
                                "MAD": metrics["MAD"], "SSE": metrics["SSE"],
                                "MSE": metrics["MSE"], "RMSE": metrics["RMSE"],
                                "R2": metrics["R2"], "Adj_R2": metrics["Adj_R2"],
                                "MAPE": metrics["MAPE"], "WAPE": metrics["WAPE"],
                                "cond": float(getattr(res, "cond", np.nan))
                            }
                            for i, name in enumerate(param_names):
                                row[name]          = float(params[i]) if i < len(params) else np.nan
                                row["se_" + name]  = float(res.se[i])    if hasattr(res, "se")    and i < len(res.se)    else np.nan
                                row["t_"  + name]  = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
                                row["p_"  + name]  = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            results.append(row)

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()