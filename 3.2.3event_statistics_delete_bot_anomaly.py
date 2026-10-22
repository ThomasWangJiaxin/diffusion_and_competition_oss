# 这版会删除：显式 bot、2017-03-25 至 28 日的高频开 issue 垃圾账号，以及 kara1abe 和 lelikalf 的异常 issue 活动；保留 2017-04-10 的真实关闭操作和 2019-01-28 holiman 的维护清理。
import json
import re
from pathlib import Path

import pandas as pd


# =============================================================================
# Configuration
# =============================================================================

BTC_EVENTS = Path(
    "/home/lab0/survival_diffusion_github/Bitcoin/"
    "bitcoin_events_timeline_unified_all_2025_12_31.csv"
)
ETH_EVENTS = Path(
    "/home/lab0/survival_diffusion_github/Ethereum/"
    "eth_events_timeline_unified_all_2025_12_31.csv"
)

BTC_PRICE = Path(
    "/home/lab0/survival_diffusion_github/price_correlation/"
    "price_bitcoin_20102025.csv"
)
ETH_PRICE = Path(
    "/home/lab0/survival_diffusion_github/price_correlation/"
    "price_eth_20152025.csv"
)

OUTPUT_FILE = Path(
    "/home/lab0/survival_diffusion_github/price_correlation/"
    "btc_eth_event_plot_inputs_no_bots_2025_12_31.xlsx"
)

BTC_START = pd.Timestamp("2011-02-12")
ETH_START = pd.Timestamp("2013-12-26")
END_DATE = pd.Timestamp("2025-12-31")

TASK_EVENTS = {
    "PushEvent",
    "PullRequestEvent",
    "IssuesEvent",
    "GollumEvent",
    "ReleaseEvent",
    "CreateEvent",
    "DeleteEvent",
}

COMMUNITY_EVENTS = {
    "ForkEvent",
    "WatchEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "CommitCommentEvent",
    "IssueCommentEvent",
    "DiscussionEvent",
}

BOT_SUFFIX = re.compile(r"\[bot\]$", re.IGNORECASE)

KNOWN_BOT_LOGINS = {
    "dependabot",
    "dependabot-preview",
    "renovate",
    "renovate-bot",
    "github-actions",
    "github-actions[bot]",
}

# Coordinated Ethereum issue-opening burst, March 2017.
ETH_SPAM_START = pd.Timestamp("2017-03-25")
ETH_SPAM_END = pd.Timestamp("2017-03-28")
SPAM_OPEN_THRESHOLD = 20

# Additional account-day anomalies. These remove only the suspicious account
# activity, preserving normal maintainer activity on the same dates.
ADDITIONAL_ETH_SPAM_EVENTS = {
    ("2017-04-10", "kara1abe"),
    ("2019-01-26", "lelikalf"),
}


# =============================================================================
# Helpers
# =============================================================================

def find_column(df, candidates, source_name):
    """Return the first matching column name, ignoring case."""
    lookup = {str(col).strip().lower(): col for col in df.columns}

    for candidate in candidates:
        matched = lookup.get(candidate.lower())
        if matched is not None:
            return matched

    raise ValueError(
        f"Could not find one of {candidates} in {source_name}. "
        f"Available columns: {list(df.columns)}"
    )


def extract_issue_action(payload):
    """Extract an IssuesEvent action from a JSON or string payload."""
    if pd.isna(payload):
        return None

    if isinstance(payload, dict):
        return payload.get("action")

    text = str(payload).strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed.get("action")
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(
        r"""["']?action["']?\s*[:=]\s*["']?([A-Za-z_]+)""",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).lower() if match else None


def load_price_data(price_path, start_date, end_date):
    """Load daily closing prices and align them to the requested date range."""
    price_df = pd.read_csv(price_path, low_memory=False)

    date_col = find_column(
        price_df,
        ["date", "timestamp", "time"],
        price_path,
    )
    close_col = find_column(
        price_df,
        ["close"],
        price_path,
    )

    price_df = price_df[[date_col, close_col]].copy()
    price_df.columns = ["date", "closing_price"]

    price_df["date"] = pd.to_datetime(
        price_df["date"],
        errors="coerce",
        format="mixed",
    ).dt.normalize()

    price_df["closing_price"] = pd.to_numeric(
        price_df["closing_price"],
        errors="coerce",
    )

    price_df = (
        price_df.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates(subset="date", keep="last")
    )

    calendar = pd.DataFrame(
        {"date": pd.date_range(start_date, end_date, freq="D")}
    )

    price_df = calendar.merge(price_df, on="date", how="left")
    price_df["closing_price"] = (
        price_df["closing_price"].ffill().bfill()
    )

    return price_df


def build_spam_candidates(df):
    """
    Identify high-frequency issue-opening accounts during the March 2017 burst.
    Candidate accounts must open at least SPAM_OPEN_THRESHOLD issues in the period.
    """
    march_issues = df[
        (df["date"].between(ETH_SPAM_START, ETH_SPAM_END))
        & (df["event_type"] == "IssuesEvent")
        & (df["issue_action"].str.lower() == "opened")
        & (~df["is_confirmed_bot"])
        & (df["actor_login"].notna())
    ].copy()

    account_counts = (
        march_issues.groupby("actor_login")
        .size()
        .reset_index(name="opened_issues")
        .sort_values("opened_issues", ascending=False)
    )

    spam_accounts = set(
        account_counts.loc[
            account_counts["opened_issues"] >= SPAM_OPEN_THRESHOLD,
            "actor_login",
        ]
        .astype(str)
        .tolist()
    )

    return spam_accounts, account_counts


def classify_activity(event_type):
    if event_type in TASK_EVENTS:
        return "Task-Oriented Events"
    if event_type in COMMUNITY_EVENTS:
        return "Community-Signal Events"
    return None


# =============================================================================
# Project Processing
# =============================================================================

def process_project(project, events_path, price_path, start_date):
    print("\n" + "=" * 80)
    print(project)
    print(f"Source: {events_path}")

    df = pd.read_csv(events_path, low_memory=False)

    created_col = find_column(
        df,
        ["created_at", "created at"],
        events_path,
    )
    event_col = find_column(
        df,
        ["event_type", "event type", "type"],
        events_path,
    )
    actor_login_col = find_column(
        df,
        ["actor_login", "actor login", "login"],
        events_path,
    )

    actor_id_col = None
    payload_col = None

    try:
        actor_id_col = find_column(
            df,
            ["actor_id", "actor id"],
            events_path,
        )
    except ValueError:
        pass

    try:
        payload_col = find_column(
            df,
            ["payload"],
            events_path,
        )
    except ValueError:
        pass

    df = df.copy()
    df["date"] = pd.to_datetime(
        df[created_col],
        errors="coerce",
        format="mixed",
    ).dt.normalize()

    df["event_type"] = df[event_col].astype(str)
    df["actor_login"] = df[actor_login_col].astype("string").str.strip()

    if actor_id_col is not None:
        df["actor_id"] = df[actor_id_col]
    else:
        df["actor_id"] = pd.NA

    df = df[
        df["date"].notna()
        & (df["date"] >= start_date)
        & (df["date"] <= END_DATE)
    ].copy()

    if payload_col is not None:
        df["issue_action"] = df[payload_col].apply(extract_issue_action)
    else:
        df["issue_action"] = pd.NA

    df["is_confirmed_bot"] = (
        df["actor_login"]
        .fillna("")
        .str.lower()
        .apply(
            lambda login: (
                bool(BOT_SUFFIX.search(login))
                or login in KNOWN_BOT_LOGINS
            )
        )
    )

    spam_accounts = set()
    spam_account_counts = pd.DataFrame(
        columns=["actor_login", "opened_issues"]
    )

    if project == "Ethereum":
        spam_accounts, spam_account_counts = build_spam_candidates(df)

    is_march_spam_account_event = (
        (project == "Ethereum")
        & (df["date"].between(ETH_SPAM_START, ETH_SPAM_END))
        & (df["actor_login"].fillna("").astype(str).isin(spam_accounts))
    )

    additional_spam_pairs = pd.MultiIndex.from_tuples(
        ADDITIONAL_ETH_SPAM_EVENTS,
        names=["date_str", "actor_login"],
    )

    observed_pairs = pd.MultiIndex.from_arrays(
        [
            df["date"].dt.strftime("%Y-%m-%d"),
            df["actor_login"].fillna("").astype(str),
        ],
        names=["date_str", "actor_login"],
    )

    is_additional_spam_account_event = (
        (project == "Ethereum")
        & observed_pairs.isin(additional_spam_pairs)
    )

    df["is_spam_account_event"] = (
        is_march_spam_account_event
        | is_additional_spam_account_event
    )

    df["excluded_reason"] = pd.NA
    df.loc[
        df["is_confirmed_bot"],
        "excluded_reason",
    ] = "confirmed_bot"

    df.loc[
        (~df["is_confirmed_bot"]) & df["is_spam_account_event"],
        "excluded_reason",
    ] = "ethereum_issue_spam_account"

    clean_df = df[df["excluded_reason"].isna()].copy()

    clean_df["activity_measure"] = clean_df["event_type"].apply(
        classify_activity
    )

    figure_df = clean_df[
        clean_df["activity_measure"].notna()
    ].copy()

    calendar = pd.DataFrame(
        {"date": pd.date_range(start_date, END_DATE, freq="D")}
    )

    daily_activity = (
        figure_df.groupby(["date", "activity_measure"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[
            "Community-Signal Events",
            "Task-Oriented Events",
        ], fill_value=0)
        .reset_index()
    )

    daily_activity = calendar.merge(
        daily_activity,
        on="date",
        how="left",
    ).fillna({
        "Community-Signal Events": 0,
        "Task-Oriented Events": 0,
    })

    daily_activity[
        ["Community-Signal Events", "Task-Oriented Events"]
    ] = daily_activity[
        ["Community-Signal Events", "Task-Oriented Events"]
    ].astype(int)

    price_df = load_price_data(price_path, start_date, END_DATE)

    chart_input = daily_activity.merge(
        price_df,
        on="date",
        how="left",
    )

    chart_input = chart_input.rename(columns={
        "date": "Date",
        "closing_price": "Closing Price (USD)",
    })

    event_totals = (
        figure_df.groupby("event_type")
        .size()
        .reset_index(name="Event Count")
        .rename(columns={"event_type": "Event Type"})
        .sort_values("Event Count", ascending=False)
        .reset_index(drop=True)
    )

    excluded_accounts = (
        df[df["excluded_reason"].notna()]
        .groupby(["excluded_reason", "actor_login", "actor_id"])
        .agg(
            event_count=("event_type", "size"),
            first_event=("date", "min"),
            last_event=("date", "max"),
            event_types=(
                "event_type",
                lambda x: ", ".join(sorted(set(x))),
            ),
        )
        .reset_index()
        .sort_values(
            ["excluded_reason", "event_count"],
            ascending=[True, False],
        )
    )

    summary = pd.DataFrame([{
        "project": project,
        "raw_events": len(df),
        "confirmed_bot_events_removed": int(
            df["is_confirmed_bot"].sum()
        ),
        "march_spam_accounts_removed": len(spam_accounts),
        "march_or_additional_spam_events_removed": int(
            (
                df["is_spam_account_event"]
                & ~df["is_confirmed_bot"]
            ).sum()
        ),
        "total_events_removed": int(
            df["excluded_reason"].notna().sum()
        ),
        "remaining_events": len(clean_df),
        "events_used_in_figures": len(figure_df),
        "missing_actor_login": int(df["actor_login"].isna().sum()),
    }])

    print(summary.to_string(index=False))

    if project == "Ethereum":
        print("\nMarch 2017 high-frequency issue-opening accounts:")
        print(spam_account_counts.head(40).to_string(index=False))

        print("\nAdditional date-specific exclusions:")
        print(
            pd.DataFrame(
                sorted(ADDITIONAL_ETH_SPAM_EVENTS),
                columns=["date", "actor_login"],
            ).to_string(index=False)
        )

    return (
        chart_input,
        event_totals,
        daily_activity,
        excluded_accounts,
        spam_account_counts,
        summary,
    )


# =============================================================================
# Run and Export
# =============================================================================

btc_chart, btc_totals, btc_daily, btc_excluded, btc_spam, btc_summary = (
    process_project(
        "Bitcoin",
        BTC_EVENTS,
        BTC_PRICE,
        BTC_START,
    )
)

eth_chart, eth_totals, eth_daily, eth_excluded, eth_spam, eth_summary = (
    process_project(
        "Ethereum",
        ETH_EVENTS,
        ETH_PRICE,
        ETH_START,
    )
)

summary_df = pd.concat(
    [btc_summary, eth_summary],
    ignore_index=True,
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl",
    datetime_format="yyyy-mm-dd",
) as writer:
    btc_chart.to_excel(
        writer,
        sheet_name="BTC_chart1_input",
        index=False,
    )
    eth_chart.to_excel(
        writer,
        sheet_name="ETH_chart1_input",
        index=False,
    )

    btc_totals.to_excel(
        writer,
        sheet_name="BTC_pie_input",
        index=False,
    )
    eth_totals.to_excel(
        writer,
        sheet_name="ETH_pie_input",
        index=False,
    )

    btc_daily.to_excel(
        writer,
        sheet_name="BTC_daily_activity",
        index=False,
    )
    eth_daily.to_excel(
        writer,
        sheet_name="ETH_daily_activity",
        index=False,
    )

    summary_df.to_excel(
        writer,
        sheet_name="Exclusion_summary",
        index=False,
    )

    btc_excluded.to_excel(
        writer,
        sheet_name="BTC_excluded_accounts",
        index=False,
    )
    eth_excluded.to_excel(
        writer,
        sheet_name="ETH_excluded_accounts",
        index=False,
    )

    eth_spam.to_excel(
        writer,
        sheet_name="ETH_march_spam_candidates",
        index=False,
    )

print("\nSaved:")
print(OUTPUT_FILE)

print("\nFinal exclusion summary:")
print(summary_df.to_string(index=False))