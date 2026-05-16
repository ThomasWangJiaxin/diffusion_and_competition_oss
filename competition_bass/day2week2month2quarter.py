#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
aggregate_to_periods_vfinal_en.py

Converts a daily dataset into weekly, monthly, and quarterly aggregates.
- Weekly date: "YYYY-MM-DD - YYYY-MM-DD"
- Monthly date: "YYYY-MM"
- Quarterly date: "YYYY-QN"
- Keeps original column order (except for added price-related stats)
"""

import pandas as pd
import numpy as np
from pathlib import Path

INPUT_CSV = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev_day_timeline_event_all.csv"
OUT_WEEKLY = "BTC_BCH_ETHdev_weekly_timeline_event_all.csv"
OUT_MONTHLY = "BTC_BCH_ETHdev_monthly_timeline_event_all.csv"
OUT_QUARTERLY = "BTC_BCH_ETHdev_quarterly_timeline_event_all.csv"


# ==========================================================
# Helper functions
# ==========================================================
def detect_prefixes(df, date_col="date"):
    cols = [c for c in df.columns if c != date_col]
    prefixes = set()
    for c in cols:
        parts = c.split("_")
        if len(parts) >= 2:
            prefixes.add(parts[0])
    return sorted(prefixes)

def columns_for_prefix(df, prefix):
    cols = [c for c in df.columns if c.startswith(prefix + "_")]
    mapping = {"new": [], "cum": [], "price": [], "events": []}
    for c in cols:
        if c.endswith("_new_developers"):
            mapping["new"].append(c)
        elif c.endswith("_cum_users"):
            mapping["cum"].append(c)
        elif c.endswith("_price"):
            mapping["price"].append(c)
        elif "_event" in c:
            mapping["events"].append(c)
    return mapping


# ==========================================================
# Aggregation logic
# ==========================================================
def aggregate_period(group, prefix, mapping):
    """Return Series: aggregated results per prefix"""
    res = {}

    # 1) new_developers → sum
    for col in mapping["new"]:
        res[col] = group[col].sum()

    # 2) event-related columns → sum
    for col in mapping["events"]:
        res[col] = group[col].sum()

    # 3) cumulative users → last value
    for col in mapping["cum"]:
        res[col] = group[col].iloc[-1]

    # 4) price → multi-stat columns
    for col in mapping["price"]:
        s = group[col].dropna().astype(float)
        if s.empty:
            vals = {f"{col}_{k}": np.nan for k in [
                "first","last","mean","std","pct_change_total",
                "mean_daily_return","std_daily_return","mean_abs_daily_return"
            ]}
        else:
            first, last = s.iloc[0], s.iloc[-1]
            meanp, stdp = s.mean(), s.std(ddof=0)
            daily_ret = s.pct_change().dropna()
            vals = {
                f"{col}_first": first,
                f"{col}_last": last,
                f"{col}_mean": meanp,
                f"{col}_std": stdp,
                f"{col}_pct_change_total": (last-first)/first if first != 0 else np.nan,
                f"{col}_mean_daily_return": daily_ret.mean() if not daily_ret.empty else np.nan,
                f"{col}_std_daily_return": daily_ret.std(ddof=0) if not daily_ret.empty else np.nan,
                f"{col}_mean_abs_daily_return": daily_ret.abs().mean() if not daily_ret.empty else np.nan
            }
        res.update(vals)
    return pd.Series(res)


# ==========================================================
# Main aggregation function
# ==========================================================
def aggregate_dataframe(df, period_type="W"):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    prefixes = detect_prefixes(df)

    # Define time grouping
    if period_type == "W":
        df["period_start"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="d")
        df["period_end"] = df["period_start"] + pd.to_timedelta(6, unit="d")
        group_key = df["period_start"]
    elif period_type == "M":
        df["period_start"] = df["date"].dt.to_period("M").dt.to_timestamp()
        df["period_end"] = (df["period_start"] + pd.offsets.MonthEnd(0))
        group_key = df["period_start"]
    elif period_type == "Q":
        df["period_start"] = df["date"].dt.to_period("Q").dt.to_timestamp()
        df["period_end"] = (df["period_start"] + pd.offsets.QuarterEnd(0))
        group_key = df["period_start"]
    else:
        raise ValueError("period_type must be 'W', 'M', or 'Q'")

    groups = df.groupby(group_key)
    result_list = []

    for start, g in groups:
        end = g["period_end"].iloc[-1]
        if period_type == "W":
            date_label = f"{start.strftime('%Y-%m-%d')} - {end.strftime('%Y-%m-%d')}"
        elif period_type == "M":
            date_label = f"{start.strftime('%Y-%m')}"
        elif period_type == "Q":
            q = ((start.month - 1)//3) + 1
            date_label = f"{start.year}-Q{q}"

        row = {"date": date_label}
        for prefix in prefixes:
            mapping = columns_for_prefix(df, prefix)
            s = aggregate_period(g, prefix, mapping)
            row.update(s.to_dict())
        result_list.append(row)

    result = pd.DataFrame(result_list)

    # Keep original column order
    orig_cols = list(df.columns)
    orig_cols = [c for c in orig_cols if c not in ["period_start","period_end"]]
    final_cols = ["date"]

    for c in orig_cols:
        if c == "date":
            continue
        final_cols.append(c)
        if c.endswith("_price"):
            final_cols.extend([
                f"{c}_first",
                f"{c}_last",
                f"{c}_mean",
                f"{c}_std",
                f"{c}_pct_change_total",
                f"{c}_mean_daily_return",
                f"{c}_std_daily_return",
                f"{c}_mean_abs_daily_return"
            ])

    # Append any new columns that might not be in original order
    extra_cols = [c for c in result.columns if c not in final_cols]
    final_cols += extra_cols
    result = result.reindex(columns=final_cols)

    return result


# ==========================================================
# Run the script
# ==========================================================
def main():
    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    weekly = aggregate_dataframe(df, "W")
    weekly.to_csv(OUT_WEEKLY, index=False)
    print(f"✅ Saved weekly → {OUT_WEEKLY}")

    monthly = aggregate_dataframe(df, "M")
    monthly.to_csv(OUT_MONTHLY, index=False)
    print(f"✅ Saved monthly → {OUT_MONTHLY}")

    quarterly = aggregate_dataframe(df, "Q")
    quarterly.to_csv(OUT_QUARTERLY, index=False)
    print(f"✅ Saved quarterly → {OUT_QUARTERLY}")


if __name__ == "__main__":
    main()