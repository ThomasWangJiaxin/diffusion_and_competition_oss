import pandas as pd
from scipy.stats import pearsonr

# 读取数据
dev_data = pd.read_csv('/home/lab0/survival_diffusion_github/eth_first_actor_count.csv')  # 开发者数据
price_data = pd.read_csv('/home/lab0/survival_diffusion_github/price_eth_20162025.csv')  # 比特币价格数据

# 确保日期格式一致（可选：如果格式不一致，可先转换）
dev_data['date'] = pd.to_datetime(dev_data['date'])
price_data['Date'] = pd.to_datetime(price_data['Date'])

# 按 date=Date 合并（内连接）
merged_data = pd.merge(dev_data, price_data, left_on='date', right_on='Date', how='inner')

# 选择需要的列
data = merged_data[['date', 'new_developers', 'cum_users', 'Price', 'Change %']]

# 检查合并后的数据
print(data.head())

combinations = [
    ('Price', 'new_developers'),
    ('Price', 'cum_users'),
    ('Change %', 'new_developers'),
    ('Change %', 'cum_users')
]
for x, y in combinations:
    corr, p_value = pearsonr(data[x], data[y])
    print(f"{x} 与 {y} 的相关系数: {corr:.4f}, p 值: {p_value:.4f}")