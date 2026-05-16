import pandas as pd
from scipy.stats import pearsonr

# 读取数据
try:
    user_stats = pd.read_csv('/home/lab0/survival_diffusion_github/eth_first_user_type_stats.csv')
    price_data = pd.read_csv('/home/lab0/survival_diffusion_github/price_eth_20162025.csv')
except FileNotFoundError as e:
    print(f"Error: CSV file not found. Please check file paths. {e}")
    exit(1)

# 确保日期格式一致
user_stats['date'] = pd.to_datetime(user_stats['date'])
price_data['Date'] = pd.to_datetime(price_data['Date'])

# 合并数据
merged_data = pd.merge(user_stats, price_data, left_on='date', right_on='Date', how='inner')

# 调试：检查 Change % 的数据类型和前几行
print("Initial dtype of 'Change %':", merged_data['Change %'].dtype)
print("Sample of 'Change %':\n", merged_data['Change %'].head())

# 处理 Change % 列
if merged_data['Change %'].dtype == 'object':  # 如果是字符串类型
    merged_data['Change %'] = merged_data['Change %'].str.rstrip('%').astype(float) / 100
else:  # 如果已经是数值类型
    # 假设已经去除了 % 且为小数（例如 -0.0105），否则需要手动调整
    merged_data['Change %'] = pd.to_numeric(merged_data['Change %'], errors='coerce') / 100

# 确保所有用户统计列是数值型
user_columns = ['new_core_dev', 'new_observer', 'new_periph_contrib', 
                'cum_core_dev', 'cum_periph_contrib', 'cum_observer']
for col in user_columns:
    merged_data[col] = pd.to_numeric(merged_data[col], errors='coerce')

# 检查缺失值
if merged_data.isnull().any().any():
    print("Warning: Missing values detected. Filling with 0.")
    merged_data.fillna(0, inplace=True)

# 相关性分析
for user_type in user_columns:
    corr_price, p_price = pearsonr(merged_data[user_type], merged_data['Price'])
    print(f"{user_type} 与 Price 的相关系数: {corr_price:.4f}, p 值: {p_price:.4f}")
    
    corr_change, p_change = pearsonr(merged_data[user_type], merged_data['Change %'])
    print(f"{user_type} 与 Change % 的相关系数: {corr_change:.4f}, p 值: {p_change:.4f}")
    print("-" * 50)