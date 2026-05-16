import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

def get_sig_stars(p):
    if p < 0.01: return "^{***}"
    if p < 0.05: return "^{**}"
    if p < 0.1: return "^{*}"
    return ""

def calculate_correlations(file_path, label, start_date=None, end_date=None):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return f"Error: File {file_path} not found."
    
    df['date'] = pd.to_datetime(df['date'])
    
    if start_date and end_date:
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df = df.loc[mask].copy()
    
    profession_events = ['PushEvent', 'CommitCommentEvent', 'IssuesEvent', 'GollumEvent', 
                         'ReleaseEvent', 'CreateEvent', 'DeleteEvent']
    herding_events = ['ForkEvent', 'WatchEvent', 'PullRequestEvent', 'PullRequestReviewEvent', 
                      'PullRequestReviewCommentEvent', 'IssueCommentEvent']
    
    df['Profession-logic Events'] = df[profession_events].sum(axis=1)
    df['Herding-logic Events'] = df[herding_events].sum(axis=1)
    
    target_vars = profession_events + ['Profession-logic Events'] + \
                  herding_events + ['Herding-logic Events']
    price_var = 'Bitcoin_closing_price' # 记得如果是比特币要改变量名
    
    results = {}
    print(f"\n--- Results for {label} ({start_date} to {end_date}) ---")
    
    for var in target_vars:
        temp_df = df[[var, price_var]].replace([np.inf, -np.inf], np.nan).dropna()
        
        # 核心逻辑：处理常数或数据不足
        if len(temp_df) < 5 or np.std(temp_df[var]) == 0:
            results[var] = "-- & -- & --"
            continue
            
        x, y = temp_df[var].values, temp_df[price_var].values
        
        # 计算三种相关性
        r_p, p_p = pearsonr(x, y)
        r_s, p_s = spearmanr(x, y)
        r_l, p_l = pearsonr(np.log1p(x), np.log1p(y))
        
        # 格式化为 LaTeX 单元格内容
        res_str = f"{r_p:.3f}{get_sig_stars(p_p)} & {r_s:.3f}{get_sig_stars(p_s)} & {r_l:.3f}{get_sig_stars(p_l)}"
        results[var] = res_str
        print(f"{var}: {res_str}")
        
    return results

# 执行计算
file_path = '/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_event_p_q_2025_12_31.csv'

# 分阶段计算
# BTC
p1 = calculate_correlations(file_path, "BTC_First_Peak", '2017-01-01', '2019-01-01')
p2 = calculate_correlations(file_path, "BTC_Second_Peak", '2020-10-01', '2022-12-31')
overall = calculate_correlations(file_path, "BTC_Overall", '2012-03-11', '2025-12-31')

# ETH
# p1 = calculate_correlations(file_path, "ETH_First_Peak", '2017-01-01', '2019-01-01')
# p2 = calculate_correlations(file_path, "ETH_Second_Peak", '2020-10-01', '2022-12-31')
# overall = calculate_correlations(file_path, "ETH_Overall", '2015-08-07', '2025-12-31')

