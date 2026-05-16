import pandas as pd
import os
import numpy as np # 导入 numpy 以使用 np.nan

# --- Configuration ---
TIMELINE_FILE = '/home/lab0/survival_diffusion_github/Bitcoin_compete/monero_timeline_events_all.csv' 
EVENTS_FILE   = '/home/lab0/survival_diffusion_github/Bitcoin_compete/monero_events_all_2025_12_31.csv'
OUTPUT_FILE   = '/home/lab0/survival_diffusion_github/Bitcoin_compete/monero_events_timeline_unified_all_2025_12_31.csv'

# 定义空邮箱的 SHA-1 哈希值
EMPTY_EMAIL_HASH = 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

# 在原有列基础上添加 actor_email
COMMON_COLUMNS = [
    'event_type', 
    'created_at', 
    'public', 
    'actor_id', 
    'actor_login', 
    'actor_email',    # <-- 新增
    'repository_id', 
    'repository_url',
    'payload',
    'other'
]

def clean_and_replace_empty_hash(df):
    """将 DataFrame 中 actor_email 列的空哈希值替换为 np.nan。"""
    if 'actor_email' in df.columns:
        # 将 actor_email 字段中的空哈希值替换为 np.nan
        df['actor_email'] = df['actor_email'].astype(str).replace(EMPTY_EMAIL_HASH, np.nan)
        print(f"✅ 清洗完成: 已将 {EMPTY_EMAIL_HASH} 替换为 NaN。")
    return df

def merge_github_datasets(timeline_path, events_path, output_path, common_cols):
    print("⏳ Starting data loading...")
    
    # Load dataframes
    try:
        df_timeline = pd.read_csv(timeline_path, low_memory=False)
        df_events   = pd.read_csv(events_path, low_memory=False)
        
        print(f"✅ Loaded Timeline records: {len(df_timeline):,} | Events records: {len(df_events):,}")
    except FileNotFoundError as e:
        print(f"❌ Error: File not found. Check path: {e}")
        return
    except pd.errors.EmptyDataError:
        print("❌ Error: One of the files is empty.")
        return
    
    # --- 关键修正步骤：清洗空邮箱哈希值 ---
    df_timeline = clean_and_replace_empty_hash(df_timeline)
    df_events = clean_and_replace_empty_hash(df_events)
    # ------------------------------------

    # --- Helper function to filter and create missing columns ---
    def filter_and_warn(df, source_name, cols_to_keep):
        df_cols = set(df.columns)
        final_cols = []

        for col in cols_to_keep:
            if col not in df_cols:
                df[col] = pd.NA
                print(f"⚠️ Warning: {source_name} missing column '{col}', created as NULL.")
            final_cols.append(col)

        return df[final_cols]

    # Apply cleaning
    print("⏳ Standardizing schemas...")
    df_timeline_clean = filter_and_warn(df_timeline, "Timeline", common_cols)
    df_events_clean   = filter_and_warn(df_events, "Events", common_cols)
    
    # --- Concatenate vertically ---
    print("⏳ Concatenating datasets...")
    df_unified = pd.concat([df_timeline_clean, df_events_clean], ignore_index=True)

    # Save file
    total_records = len(df_unified)
    df_unified.to_csv(output_path, index=False, encoding='utf-8')

    print(f"✅ Total merged records: {total_records:,}")
    print(f"🎉 Unified dataset saved to: {output_path}")

if __name__ == "__main__":
    merge_github_datasets(TIMELINE_FILE, EVENTS_FILE, OUTPUT_FILE, COMMON_COLUMNS)

# DDL: 2024-12-31
# bitcoin: Loaded Timeline records: 66,018 | Events records: 520,496
# bips: Loaded Timeline records: 1,620 | Events records: 34,411
# eth: Loaded Timeline records: 2,175 | Events records: 235,690
# Litecoin: Loaded Timeline records: 5,142 | Events records: 13,514
# Dogecoin: Loaded Timeline records: 6,682 | Events records: 39,785

# DDL: 2025-12-31
# bitcoin: Loaded Timeline records: 66,018 | Events records: 563,612
# bips: Loaded Timeline records: 1,620 | Events records: 39,331
# eth: Loaded Timeline records: 2,175 | Events records: 249,186
# Litecoin: Loaded Timeline records: 5,142 | Events records: 13,929
# Dogecoin: Loaded Timeline records: 6,682 | Events records: 40,800
