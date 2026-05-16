#!/usr/bin/env python3
"""
对四个 merged CSV 分别计算每个消融模型相对于 Ours（M8.4）的
F-statistic 和 p-value，插入到 WAPE 列之后。

k 根据模型组件直接硬编码：
  k = 3(base: p0,q0,m) + price(α) + p_event(β_p) + q_event(β_q)
      + in_flow(γ×J) + out_flow(δ×J)
"""
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import f as f_dist

ABLATION_DIR = Path("/home/lab0/survival_diffusion_github/ablation_study")

MERGED_FILES = [
    "merged_btc_20172019.csv",
    "merged_btc_20202022.csv",
    "merged_eth_20172019.csv",
    "merged_eth_20202023.csv",
]

# 样本量 n（窗口天数）
N_MAP = {
    "merged_btc_20172019.csv": 731,   # 2017-01-01 ~ 2019-01-01
    "merged_btc_20202022.csv": 732,   # 2020-10-01 ~ 2022-10-01
    "merged_eth_20172019.csv": 731,   # 2017-01-01 ~ 2019-01-01
    "merged_eth_20202023.csv": 824,   # 2020-10-01 ~ 2023-01-01
}

# 竞争者数量 J
J_MAP = {
    "merged_btc_20172019.csv": 15,  # 9 internal + 6 external
    "merged_btc_20202022.csv": 14,  # 6 internal + 8 external
    "merged_eth_20172019.csv":  4,  # 1 internal + 3 external
    "merged_eth_20202023.csv": 20,  # 11 internal + 9 external
}

# 各模型组件标记：(price, p_event, q_event, in_flow, out_flow)
MODEL_COMPONENTS = {
    "M1.1": (0, 0, 0, 0, 0),
    "M1.2": (0, 0, 0, 1, 0),
    "M1.3": (0, 0, 0, 0, 1),
    "M1.4": (0, 0, 0, 1, 1),
    "M2.1": (0, 0, 1, 0, 0),
    "M2.2": (0, 0, 1, 1, 0),
    "M2.3": (0, 0, 1, 0, 1),
    "M2.4": (0, 0, 1, 1, 1),
    "M3.1": (1, 0, 0, 0, 0),
    "M3.2": (1, 0, 0, 1, 0),
    "M3.3": (1, 0, 0, 0, 1),
    "M3.4": (1, 0, 0, 1, 1),
    "M4.1": (1, 0, 1, 0, 0),
    "M4.2": (1, 0, 1, 1, 0),
    "M4.3": (1, 0, 1, 0, 1),
    "M4.4": (1, 0, 1, 1, 1),
    "M5.1": (0, 1, 0, 0, 0),
    "M5.2": (0, 1, 0, 1, 0),
    "M5.3": (0, 1, 0, 0, 1),
    "M5.4": (0, 1, 0, 1, 1),
    "M6.1": (0, 1, 1, 0, 0),
    "M6.2": (0, 1, 1, 1, 0),
    "M6.3": (0, 1, 1, 0, 1),
    "M6.4": (0, 1, 1, 1, 1),
    "M7.1": (1, 1, 0, 0, 0),
    "M7.2": (1, 1, 0, 1, 0),
    "M7.3": (1, 1, 0, 0, 1),
    "M7.4": (1, 1, 0, 1, 1),
    "M8.1": (1, 1, 1, 0, 0),
    "M8.2": (1, 1, 1, 1, 0),
    "M8.3": (1, 1, 1, 0, 1),
    "M8.4": (1, 1, 1, 1, 1),
    "Ours": (1, 1, 1, 1, 1),
}

PROPOSED_ALIASES = {"M8.4", "Ours", "ours"}

def get_k(model_name: str, J: int):
    comp = MODEL_COMPONENTS.get(str(model_name).strip())
    if comp is None:
        return None
    price, p_ev, q_ev, in_f, out_f = comp
    return 3 + price + p_ev + q_ev + in_f * J + out_f * J

def compute_ftest(sse_r, k_r, sse_u, k_u, n):
    try:
        df1 = k_u - k_r
        df2 = n - k_u
        if df1 <= 0 or df2 <= 0 or sse_u <= 0:
            return np.nan, np.nan
        if sse_r < sse_u:
            return np.nan, np.nan
        F = ((sse_r - sse_u) / df1) / (sse_u / df2)
        p = 1 - f_dist.cdf(F, df1, df2)
        return float(F), float(p)
    except Exception:
        return np.nan, np.nan

def process_file(csv_path: Path, n: int, J: int):
    print(f"\n{'='*65}")
    print(f"📄 {csv_path.name}  (n={n}, J={J})")

    df = pd.read_csv(csv_path)

    for col in ["model", "SSE", "WAPE"]:
        if col not in df.columns:
            print(f"  ⚠️  缺少列 '{col}'，跳过。")
            return

    # 找 proposed model 行
    mask_u = df["model"].astype(str).str.strip().isin(PROPOSED_ALIASES)
    if mask_u.sum() == 0:
        print(f"  ⚠️  未找到 proposed model 行，跳过。")
        return

    row_u  = df[mask_u].iloc[0]
    sse_u  = float(row_u["SSE"])
    k_u    = get_k(str(row_u["model"]).strip(), J)

    if k_u is None:
        print(f"  ⚠️  无法获取 proposed model k，跳过。")
        return

    print(f"  Proposed: SSE={sse_u:.4f}, k_U={k_u}")

    f_stats, p_vals = [], []

    for _, row in df.iterrows():
        model_name = str(row["model"]).strip()

        if model_name in PROPOSED_ALIASES:
            f_stats.append(np.nan)
            p_vals.append(np.nan)
            continue

        k_r = get_k(model_name, J)
        if k_r is None:
            print(f"  ⚠️  未知模型 '{model_name}'，填 NaN")
            f_stats.append(np.nan)
            p_vals.append(np.nan)
            continue

        try:
            sse_r = float(row["SSE"])
        except Exception:
            f_stats.append(np.nan)
            p_vals.append(np.nan)
            continue

        F, p = compute_ftest(sse_r, k_r, sse_u, k_u, n)
        f_stats.append(F)
        p_vals.append(p)

        sig = ("***" if (not np.isnan(p) and p < 0.001) else
               "**"  if (not np.isnan(p) and p < 0.01)  else
               "*"   if (not np.isnan(p) and p < 0.05)  else "n.s.")
        print(f"  {model_name:6s}: k_R={k_r:2d}  SSE_R={sse_r:12.2f}  "
              f"F={F:10.3f}  p={p:.3e}  {sig}")

    # 插入到 WAPE 之后
    wape_idx = df.columns.get_loc("WAPE")
    df.insert(wape_idx + 1, "F_statistic1", f_stats)
    df.insert(wape_idx + 2, "p_value1",     p_vals)

    df.to_csv(csv_path, index=False)
    print(f"  ✅ 已保存: {csv_path.name}")

def main():
    for fname in MERGED_FILES:
        fpath = ABLATION_DIR / fname
        if not fpath.exists():
            print(f"⚠️  文件不存在，跳过: {fname}")
            continue
        process_file(fpath, N_MAP[fname], J_MAP[fname])

    print("\n✅ 全部处理完成。")

if __name__ == "__main__":
    main()