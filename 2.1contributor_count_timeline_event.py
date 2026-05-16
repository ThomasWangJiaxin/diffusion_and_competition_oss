# import pandas as pd

# # 加载事件数据文件（请替换为你自己的路径）
# df = pd.read_csv("/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_events_timeline_unified_all.csv")

# # 确保 created_at 字段为 datetime 类型
# df["created_at"] = pd.to_datetime(df["created_at"])

# # 1. 统计不重复的 contributor 数量（根据 actor_id 唯一标识）
# unique_contributors = df["actor_login"].nunique()
# print("不重复的贡献者数量:", unique_contributors)

# # 2. 每个开发者在每种行为上的第一次行为记录
# first_events = df.sort_values("created_at").groupby(["actor_login", "event_type"]).first().reset_index()

# # 将 "created_at" 列移动到前三列
# created_at_column = first_events.pop('created_at')  # 移除 'created_at' 列
# first_events.insert(2, 'created_at', created_at_column)  # 将 'created_at' 插入到第三列位置

# # 可选：保存结果
# first_events.to_csv("/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_first_events_by_type_timeline_unified.csv", index=False)
# print("已导出每个开发者每种事件类型的首次行为记录到 dogecoin_first_events_by_type_timeline_unified.csv")

# bitcoin timeline_unified 不重复的贡献者数量: 122558
# bips timeline_unified 不重复的贡献者数量: 16596
# eth timeline_unified 不重复的贡献者数量: 76893
# litecoin imeline_unified 不重复贡献者数量: 10899
# dogecoin imeline_unified 不重复贡献者数量: 21265

# ================================
# 这绝对比纯 login 去重更准确！
# 如果你用 login 去重，你会认为：
# 2013 有 3 个不同开发者（主要为的就是防止这个）
# 但实际上只有 1 个
# 如果你用 actor_id 去重：
# 2013 没有 actor_id，计不出来
# 但我们这个方法可以：
# 利用 2016 年清晰的数据
# 回填 2013 年模糊的数据
# 最大化 contributor 去重准确率

# import pandas as pd

# df = pd.read_csv("/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_events_timeline_unified_all.csv")
# df["created_at"] = pd.to_datetime(df["created_at"])

# # 1. 构建 login → id 的映射（只用有 id 的记录）
# login_id_map = (
#     df[df["actor_id"].notna()][["actor_login", "actor_id"]]
#     .drop_duplicates()
# )

# # 2. 回填历史 login 的 actor_id
# df = df.merge(
#     login_id_map,
#     on="actor_login",
#     how="left",
#     suffixes=("", "_inferred")
# )

# df["actor_id_final"] = df["actor_id"].fillna(df["actor_id_inferred"])

# # 3. 构造稳定 contributor_key（优先 id → fallback login）
# df["contributor_key"] = df["actor_id_final"].fillna(df["actor_login"])

# # 统计不重复 contributor 数量
# print("不重复贡献者数量:", df["contributor_key"].nunique())

# # 计算每个开发者每种事件类型的首次行为
# first_events = df.sort_values("created_at").groupby(
#     ["contributor_key", "event_type"]
# ).first().reset_index()

# first_events.to_csv(
#     "/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_first_events_by_type_timeline_unified.csv",
#     index=False
# )

# bitcoin timeline_unified 不重复的贡献者数量: 121987
# bips timeline_unified 不重复的贡献者数量: 16534
# eth timeline_unified 不重复的贡献者数量: 76383
# litecoin imeline_unified 不重复贡献者数量: 10852
# dogecoin imeline_unified 不重复贡献者数量: 21220


# ================================
# 上面是chatgpt生成的 下面是gemini生成的 可以对比参考
import pandas as pd
import numpy as np
import os
import sys

# --- Configuration ---
FILE_PATH = "/home/lab0/survival_diffusion_github/Bitcoin_compete/monero_events_timeline_unified_all_2025_12_31.csv"
OUTPUT_DIR = "/home/lab0/survival_diffusion_github/Bitcoin_compete"
OUTPUT_FIRST_EVENTS_FILE = "monero_first_events_by_type_timeline_unified_2025_12_31.csv"

def resolve_actor_identity(df, show_mapping_sample=True):
    """
    通过 Login 和 Email 映射回填 ID，加入 login→多email 冲突处理。
    """

    print("\n=== 步骤 1: 清理字段 ===")
    df['actor_id'] = df['actor_id'].astype(str).str.replace(r'(\.0$)', '', regex=True)
    df['actor_id'] = df['actor_id'].replace(['nan', 'None', '', '0'], np.nan)
    df['actor_login'] = df['actor_login'].astype(str).replace(['nan', 'None', ''], np.nan)
    df['actor_email'] = df['actor_email'].astype(str).replace(['nan', 'None', '', '0'], np.nan)

    # ==== 初始缺失 ID ====
    initial_missing = df['actor_id'].isna().sum()
    print(f"🔍 初始缺失 actor_id 数量：{initial_missing:,}")

    # ==== 登录名与邮箱多对多关系检查（仅用于统计） ====
    df_2015 = df[df['created_at'] < "2015-01-01"]
    login_email_counts = df_2015.groupby('actor_login')['actor_email'].nunique(dropna=True)
    logins_with_multiple_emails = login_email_counts[login_email_counts > 1]
    email_login_counts = df_2015.groupby('actor_email')['actor_login'].nunique(dropna=True)
    emails_with_multiple_logins = email_login_counts[email_login_counts > 1]

    print("\n=== 2015 年以前登录名与邮箱多对多关系 ===")
    print(f"📌 login 对应多个 email 的数量：{len(logins_with_multiple_emails):,}")
    print(f"📌 email 对应多个 login 的数量：{len(emails_with_multiple_logins):,}")

    # 1. Login → ID 映射（不限年份，只要同时存在 ID 和 login）
    id_known_df = df.dropna(subset=['actor_id', 'actor_login'])
    login_to_id_map = id_known_df.set_index('actor_login')['actor_id'].to_dict()

    # 🔹 新增冲突处理：标记 login→多email 的 login
    conflicted_logins = set(logins_with_multiple_emails.index)

    # 2. Email → ID 映射（不限年份，只要同时存在 ID 和 email）
    email_known_df = df.dropna(subset=['actor_id', 'actor_email'])
    email_to_id_map = email_known_df.set_index('actor_email')['actor_id'].to_dict()

    if show_mapping_sample:
        print("\n📌 Login → ID 映射样例（前 5 条）：")
        print(dict(list(login_to_id_map.items())[:5]))
        print("\n📌 Email → ID 映射样例（前 5 条）：")
        print(dict(list(email_to_id_map.items())[:5]))

    # 3. login → ID 冲突诊断
    login_id_counts = id_known_df.groupby('actor_login')['actor_id'].nunique()
    conflicting_logins_global = login_id_counts[login_id_counts > 1].index.tolist()
    if conflicting_logins_global:
        print(f"\n⚠️ 警告: 发现 {len(conflicting_logins_global)} 个 login 对应多个 actor_id（严重数据污染）")
    else:
        print("✅ 未发现 login → ID 污染")

    # 4. 第一轮：login 回填 ID（跳过 login→多email 的冲突记录） 🔹
    missing_before_login = df['actor_id'].isna()
    mask_valid_login = df['actor_login'].notna() & (~df['actor_login'].isin(conflicted_logins))
    fill_mask = missing_before_login & mask_valid_login

    df.loc[fill_mask, 'actor_id'] = df.loc[fill_mask, 'actor_login'].map(login_to_id_map)
    missing_after_login = df['actor_id'].isna().sum()
    filled_by_login = missing_before_login.sum() - missing_after_login
    print(f"\n🔧 通过 Login 回填成功（跳过冲突 login）：{filled_by_login:,} 条")

    # 5. 第二轮：email 回填 ID
    missing_before_email = df['actor_id'].isna()
    df.loc[missing_before_email, 'actor_id'] = df.loc[missing_before_email, 'actor_email'].map(email_to_id_map)
    missing_after_email = df['actor_id'].isna().sum()
    filled_by_email = missing_before_email.sum() - missing_after_email
    print(f"🔧 通过 Email 回填成功：{filled_by_email:,} 条")

    # 6. 仍无法回填
    final_unresolved = df['actor_id'].isna().sum()
    print(f"⛔ 最终无法回填 actor_id：{final_unresolved:,}")

    # ============================================================
    # === 2015年前 & 2015年后 actor_id / login 组合统计 + 缺失时间范围 ===
    # ============================================================

    def summarize_period(data, label):
        missing_id = data['actor_id'].isna()
        missing_login = data['actor_login'].isna()
        a = (missing_id & ~missing_login).sum()   # 缺ID 有login
        b = (missing_id & missing_login).sum()    # 缺ID 缺login
        c = (~missing_id & missing_login).sum()   # 有ID 缺login
        d = (~missing_id & ~missing_login).sum()  # ID+login 都有
        print(f"\n--- {label} ---")
        print(f"缺 ID 但有 login：{a:,}")
        print(f"缺 ID 且无 login：{b:,}")
        if b > 0:
            unresolved_dates = data[missing_id & missing_login]['created_at']
            print(f"⚠️ 缺 ID 且无 login 的时间范围: {unresolved_dates.min()} ~ {unresolved_dates.max()}")
        print(f"有 ID 但缺 login：{c:,}")
        print(f"ID 和 login 均存在：{d:,}")
        return a, b, c, d

    df_2015_before = df[df['created_at'] < "2015-01-01"]
    df_2015_after  = df[df['created_at'] >= "2015-01-01"]
    summarize_period(df_2015_before, "2015 年之前")
    summarize_period(df_2015_after,  "2015 年之后")

    # 7. stable_actor_id
    df['stable_actor_id'] = df['actor_id'].combine_first(df['actor_login'])
    print("✅ 已生成 stable_actor_id")

    # 8. stable_actor_id 使用 login 填充数量
    stable_id_from_login_count = df[df['actor_id'].isna()]['stable_actor_id'].count()
    print(f"📌 最终使用 login 作为 stable_actor_id 的数量：{stable_id_from_login_count:,}")

    # 9. login 更改导致的重命名用户
    id_login_counts = id_known_df.groupby('actor_id')['actor_login'].nunique()
    renamed_users = id_login_counts[id_login_counts > 1].count()
    print(f"🔍 login 重命名用户数量：{renamed_users:,}")

    # --- 总结 ---
    print("\n=== ID 回填统计总结 ===")
    print(f"📌 初始缺失 actor_id：{initial_missing:,}")
    print(f"📌 Login 回填成功：{filled_by_login:,}")
    print(f"📌 Email 回填成功：{filled_by_email:,}")
    print(f"📌 最终无法回填：{final_unresolved:,}")
    print(f"📌 最终使用 login 作为稳定ID：{stable_id_from_login_count:,}")
    print(f"📌 login→多email（2015年前）：{len(logins_with_multiple_emails):,}")
    print(f"📌 email→多login（2015年前）：{len(emails_with_multiple_logins):,}")
    print("=====================================\n")

    return df

# --- 主执行逻辑 ---
try:
    df = pd.read_csv(FILE_PATH, low_memory=False)
    df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')

    df = resolve_actor_identity(df)
    print("✅ 已完成身份解析，创建 stable_actor_id 字段。")

    unique_contributors = df["stable_actor_id"].nunique()
    print(f"\n✅ 基于稳定 ID 的不重复贡献者数量: {unique_contributors:,}")

    df_sorted = df.sort_values("created_at")
    first_events = df_sorted.groupby(["stable_actor_id", "event_type"]).first().reset_index()
    created_at_column = first_events.pop('created_at')
    first_events.insert(2, 'created_at', created_at_column)

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FIRST_EVENTS_FILE)
    first_events.to_csv(output_path, index=False)
    print(f"\n🎉 已导出每个开发者每种事件类型的首次行为记录到 {output_path}")

except FileNotFoundError:
    print(f"❌ 文件未找到，请检查路径: {FILE_PATH}")
except Exception as e:
    print(f"❌ 发生错误: {e}")


# 结果：
# bitcoin timeline_unified 不重复的贡献者数量: 121987
# （1）发现 121 个 actor_login 对应多个 actor_id。这些是数据污染点。
# --- 冲突 Login 列表 ---
# 0v3rl0w, 10xcryptodevforks, 1440000bytes, 1x0, 2gab, 6b1b7b2f918035592d04a3a29cbc46bb, 78bash, Ahr-i, AmirSheikhmagomedov, Aniamon, AnshulKanwar, BitcoinP0S, BitcoinStaking, DATSEC, EricksonAlmario, InnoScorpio, JKPROP, JKSTNK, MippsCoin, NullFunctor, OldMiR, PrinceKK300188, QuaTaC, RedD0tZer0, RedDotZer0, Ronald-Cifuentes, Sitao, TanishShinde, TechieForFun, Tyquan, WONSUNGJUN, WillWammer, YevgenMuza, Zer0Python, alexNeto, andmeics, arnonhongklay, arthurx07, b17c01n, barrydeen, bitrub, blz-ea, bohruz, brandenocon, canioque, cashviar, choonsiong, cornpleb, dasrecord, diogorsergio, dogefoodcoin, dylxc, emilioheinz, erolDemirhan, fbarikzehi, gaoshengyu, gclwsn, gioelecerati, hardincorporated, inyahe, iwoskerlonne, jennafleischer, jonathan-matheus, juscilan, jvztech, kborovik, lagentiti, leejongyoung, lochacoin, lvvvl, m31271n, magic-moment, mahmoudsaeed, marcopiedravenegas, markub3327, martinmorando, mateusz-klatt, mathsCode, mathscode, matrixgram, max-block, mcccs, mfurkandemir, miguelnischor, mohsanabbas, mpiedrav, ndalliard, nonasoumy, nonmadden, ntilotta, ntilotta2, r01922044, ralphacker, rhyshighrise, rndvec, robertmarshallxyz, rofrnnds, rrlamichhane, saleh-mir, scorpionts3, selvendiranj, shakeelrao, shazgames, starwels, supar3, talentumtuum, tengiszuchi, tonytan30, tortuvshin, twepl, user1687569, utoyvo, v008, vim88, wau, whoiszr, winnard, wudio2010, xingkaichun, zhangxiangliang, zoltan-konder
# （2）发现 678 个 Actor ID 对应多个 Login (重命名用户)。
# --- 重命名用户 ID 列表及其 Login 数量 ---
# ID: 1000077 -> 共 2 个 Login: sdgoh, sd5k
# ID: 10016923 -> 共 2 个 Login: audioburn, onyxc
# ID: 10080035 -> 共 2 个 Login: StijnToemen, StijnBTC
# ID: 10108832 -> 共 2 个 Login: MrKimi, kimichowmein
# ID: 10110245 -> 共 2 个 Login: Gamecrafter, ifvictr
# ID: 101140728 -> 共 2 个 Login: Davidgould187, Dglocalwhitegoods
# ID: 101607407 -> 共 2 个 Login: shisll, veilovv
# ID: 101708359 -> 共 2 个 Login: Layer2Labs, AreaLayer
# ID: 101912712 -> 共 2 个 Login: Zliced13, FlawlessCasual17
# ID: 10231183 -> 共 2 个 Login: Dipakkumar07, dipaksavaliya
# ... 还有 668 个重命名用户未显示。
# ------------------------------------------

# bitcoin 2025-12-31
# === 步骤 1: 清理字段 ===
# 🔍 初始缺失 actor_id 数量：66,018

# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：25
# 📌 email 对应多个 login 的数量：11

# 📌 Login → ID 映射样例（前 5 条）：
# {'Zorlin': '1369772', 'SoCoCpp': '6132807', 'luke-jr': '1095675', 'cossacksson': '6298754', 'Hu-Hsiang-Pin': '6785030'}

# 📌 Email → ID 映射样例（前 5 条）：
# {}

# ⚠️ 警告: 发现 128 个 login 对应多个 actor_id（严重数据污染）

# 🔧 通过 Login 回填成功（跳过冲突 login）：45,549 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：20,469

# --- 2015 年之前 ---
# 缺 ID 但有 login：13,880
# 缺 ID 且无 login：6,589
# ⚠️ 缺 ID 且无 login 的时间范围: 2011-02-12 00:34:35 ~ 2013-03-24 20:41:13
# 有 ID 但缺 login：0
# ID 和 login 均存在：45,534

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：563,627
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：13,880
# 🔍 login 重命名用户数量：740

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：66,018
# 📌 Login 回填成功：45,549
# 📌 Email 回填成功：0
# 📌 最终无法回填：20,469
# 📌 最终使用 login 作为稳定ID：13,880
# 📌 login→多email（2015年前）：25
# 📌 email→多login（2015年前）：11
# =====================================

# ✅ 已完成身份解析，创建 stable_actor_id 字段。
# ✅ 基于稳定 ID 的不重复贡献者数量: 129,032

# bips timeline_unified 不重复的贡献者数量: 16534
# （1）发现 9 个 actor_login 对应多个 actor_id。这些是数据污染点。
# --- 冲突 Login 列表 ---
# 0xpwn, 1440000bytes, JKPROP, MattLongCT, b17c01n, bitrub, guinness1974, mcccs, starwels
# （2）发现 72 个 Actor ID 对应多个 Login (重命名用户)。
# --- 重命名用户 ID 列表及其 Login 数量 ---
# ID: 100856592 -> 共 2 个 Login: jugganautz, devilshyt
# ID: 102320249 -> 共 2 个 Login: xorizon, rustaceanrob
# ID: 104945 -> 共 2 个 Login: runn1ng, karel-3d
# ID: 1063656 -> 共 2 个 Login: jonnynewbs, jnewbery
# ID: 1066583 -> 共 2 个 Login: AtheistOfFail, WriteCodeEveryday
# ID: 1130872 -> 共 2 个 Login: wbinns, wbnns
# ID: 118510103 -> 共 2 个 Login: jiyoontbd, jiyoonie9
# ID: 124597058 -> 共 2 个 Login: Dragankamil6, KamPuc86zg
# ID: 12795842 -> 共 2 个 Login: YAGAMITAICHI, KonanHYM
# ID: 1313145 -> 共 2 个 Login: FATYU, HugePages
# ... 还有 62 个重命名用户未显示。
# ------------------------------------------

# bips 2025-12-31
# === 步骤 1: 清理字段 ===
# 🔍 初始缺失 actor_id 数量：1,620

# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：0
# 📌 email 对应多个 login 的数量：0

# 📌 Login → ID 映射样例（前 5 条）：
# {'milovanhbk': '901165', 'fanquake': '863730', 'superisaac': '12558', 'R32': '6825113', 'byrongibson': '275081'}

# 📌 Email → ID 映射样例（前 5 条）：
# {}

# ⚠️ 警告: 发现 10 个 login 对应多个 actor_id（严重数据污染）

# 🔧 通过 Login 回填成功（跳过冲突 login）：1,026 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：594

# --- 2015 年之前 ---
# 缺 ID 但有 login：594
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：1,026

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：39,331
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：594
# 🔍 login 重命名用户数量：79

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：1,620
# 📌 Login 回填成功：1,026
# 📌 Email 回填成功：0
# 📌 最终无法回填：594
# 📌 最终使用 login 作为稳定ID：594
# 📌 login→多email（2015年前）：0
# 📌 email→多login（2015年前）：0
# =====================================

# ✅ 已完成身份解析，创建 stable_actor_id 字段。

# ✅ 基于稳定 ID 的不重复贡献者数量: 17,601


# eth timeline_unified 不重复的贡献者数量: 76383
# （1）发现 40 个 actor_login 对应多个 actor_id。这些是数据污染点。
# --- 冲突 Login 列表 ---
# 0xEther, 0xsiddharthks, Ahr-i, AmirSheikhmagomedov, ChainSafe, CultureSupport, JaimeeNye, Number16BusShelter, aoxc, brunogbarros, bsjung, cashviar, ethereumsocial, evilpapa, fbarikzehi, feathereum, hunjixin, husone, jostgrant, jpclark, lazaridiscom, lnogue, maycoin, mfurkandemir, miselkrstovic, muzykantov, mykhpl, nlat31, nonasoumy, nonmadden, ntilotta, nurazhar, oleksiivelychko, orcun-cc, rndvec, rusengurkan7, sdu-net, shogoorg, stay-focused, zhuliting
# （2）发现 538 个 Actor ID 对应多个 Login (重命名用户)。
# --- 重命名用户 ID 列表及其 Login 数量 ---
# ID: 10010900 -> 共 2 个 Login: sch00lb0y, balajijinnah
# ID: 100542195 -> 共 2 个 Login: MattyIc333, abc0xmattyic333
# ID: 101599447 -> 共 2 个 Login: zoey-t, zt-9
# ID: 102128367 -> 共 2 个 Login: satrustark, 333satoru
# ID: 102652401 -> 共 2 个 Login: slutterog, ripoff2
# ID: 10308253 -> 共 2 个 Login: junhsieh, junxie6
# ID: 10343662 -> 共 2 个 Login: ruchern, ruchern-chong
# ID: 104084666 -> 共 2 个 Login: anderssonvivi, vivi365
# ID: 10431418 -> 共 2 个 Login: funnyphd, Hypnotised1
# ID: 10458544 -> 共 2 个 Login: GuangshanWen, mountainswen
# ... 还有 528 个重命名用户未显示。
# ---------------------

# eth 2025-12-31
# === 步骤 1: 清理字段 ===
# 🔍 初始缺失 actor_id 数量：2,175

# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：2
# 📌 email 对应多个 login 的数量：0

# 📌 Login → ID 映射样例（前 5 条）：
# {'naolduga': '10269249', 'Gustav-Simonsson': '293096', 'obscuren': '6264126', 'amiller': '71644', 'F1LT3R': '1218446'}

# 📌 Email → ID 映射样例（前 5 条）：
# {}

# ⚠️ 警告: 发现 42 个 login 对应多个 actor_id（严重数据污染）

# 🔧 通过 Login 回填成功（跳过冲突 login）：1,669 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：506

# --- 2015 年之前 ---
# 缺 ID 但有 login：506
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：1,669

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：249,186
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：506
# 🔍 login 重命名用户数量：568

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：2,175
# 📌 Login 回填成功：1,669
# 📌 Email 回填成功：0
# 📌 最终无法回填：506
# 📌 最终使用 login 作为稳定ID：506
# 📌 login→多email（2015年前）：2
# 📌 email→多login（2015年前）：0
# =====================================

# ✅ 已完成身份解析，创建 stable_actor_id 字段。

# ✅ 基于稳定 ID 的不重复贡献者数量: 79,763

# Litecoin timeline_unified 不重复的贡献者数量: 10852
# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：6
# 📌 email 对应多个 login 的数量：1
# 📌 Login → ID 映射样例（前 5 条）：
# {'wekuiz': '9837698', 'mtkliema': '5452993', 'highonquack': '10382230', 'itsacezon': '1902481', 'JimmyThompson': '653864'}
# 📌 Email → ID 映射样例（前 5 条）：
# ⚠️ 警告: 发现 8 个 login 对应多个 actor_id（严重数据污染）
# 🔧 通过 Login 回填成功（跳过冲突 login）：1,031 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：4,111

# --- 2015 年之前 ---
# 缺 ID 但有 login：4,111
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：1,031

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：13,514
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：4,111
# 🔍 login 重命名用户数量：51

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：5,142
# 📌 Login 回填成功：1,031
# 📌 Email 回填成功：0
# 📌 最终无法回填：4,111
# 📌 最终使用 login 作为稳定ID：4,111
# 📌 login→多email（2015年前）：6
# 📌 email→多login（2015年前）：1
# =====================================

# litecoin 2025_12_31
# === 步骤 1: 清理字段 ===
# 🔍 初始缺失 actor_id 数量：5,142

# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：6
# 📌 email 对应多个 login 的数量：1

# 📌 Login → ID 映射样例（前 5 条）：
# {'wekuiz': '9837698', 'mtkliema': '5452993', 'highonquack': '10382230', 'itsacezon': '1902481', 'JimmyThompson': '653864'}

# 📌 Email → ID 映射样例（前 5 条）：
# {}

# ⚠️ 警告: 发现 8 个 login 对应多个 actor_id（严重数据污染）

# 🔧 通过 Login 回填成功（跳过冲突 login）：1,031 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：4,111

# --- 2015 年之前 ---
# 缺 ID 但有 login：4,111
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：1,031

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：13,929
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：4,111
# 🔍 login 重命名用户数量：55

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：5,142
# 📌 Login 回填成功：1,031
# 📌 Email 回填成功：0
# 📌 最终无法回填：4,111
# 📌 最终使用 login 作为稳定ID：4,111
# 📌 login→多email（2015年前）：6
# 📌 email→多login（2015年前）：1
# =====================================

# ✅ 已完成身份解析，创建 stable_actor_id 字段。

# ✅ 基于稳定 ID 的不重复贡献者数量: 11,115



# dogecoin timeline_unified 不重复的贡献者数量: 21221
# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：8
# 📌 email 对应多个 login 的数量：2
# 📌 Login → ID 映射样例（前 5 条）：
# {'johnathanmartin': '6856083', 'langerhans': '5160000', 'benhc123': '4144334', 'cashmonei': '10371561', 'rnicoll': '3513077'}
# 📌 Email → ID 映射样例（前 5 条）：
# ⚠️ 警告: 发现 8 个 login 对应多个 actor_id（严重数据污染）
# 🔧 通过 Login 回填成功（跳过冲突 login）：2,283 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：4,399

# --- 2015 年之前 ---
# 缺 ID 但有 login：4,399
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：2,283

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：39,785
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：4,399
# 🔍 login 重命名用户数量：55

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：6,682
# 📌 Login 回填成功：2,283
# 📌 Email 回填成功：0
# 📌 最终无法回填：4,399
# 📌 最终使用 login 作为稳定ID：4,399
# 📌 login→多email（2015年前）：8
# 📌 email→多login（2015年前）：2
# =====================================

# dogecoin 2025_12_31
# === 步骤 1: 清理字段 ===
# 🔍 初始缺失 actor_id 数量：6,682

# === 2015 年以前登录名与邮箱多对多关系 ===
# 📌 login 对应多个 email 的数量：8
# 📌 email 对应多个 login 的数量：2

# 📌 Login → ID 映射样例（前 5 条）：
# {'johnathanmartin': '6856083', 'langerhans': '5160000', 'benhc123': '4144334', 'cashmonei': '10371561', 'rnicoll': '3513077'}

# 📌 Email → ID 映射样例（前 5 条）：
# {}

# ⚠️ 警告: 发现 8 个 login 对应多个 actor_id（严重数据污染）

# 🔧 通过 Login 回填成功（跳过冲突 login）：2,283 条
# 🔧 通过 Email 回填成功：0 条
# ⛔ 最终无法回填 actor_id：4,399

# --- 2015 年之前 ---
# 缺 ID 但有 login：4,399
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：2,283

# --- 2015 年之后 ---
# 缺 ID 但有 login：0
# 缺 ID 且无 login：0
# 有 ID 但缺 login：0
# ID 和 login 均存在：40,800
# ✅ 已生成 stable_actor_id
# 📌 最终使用 login 作为 stable_actor_id 的数量：4,399
# 🔍 login 重命名用户数量：61

# === ID 回填统计总结 ===
# 📌 初始缺失 actor_id：6,682
# 📌 Login 回填成功：2,283
# 📌 Email 回填成功：0
# 📌 最终无法回填：4,399
# 📌 最终使用 login 作为稳定ID：4,399
# 📌 login→多email（2015年前）：8
# 📌 email→多login（2015年前）：2
# =====================================

# ✅ 已完成身份解析，创建 stable_actor_id 字段。

# ✅ 基于稳定 ID 的不重复贡献者数量: 21,774