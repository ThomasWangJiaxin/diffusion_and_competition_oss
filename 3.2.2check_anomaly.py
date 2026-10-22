import json
import re
from pathlib import Path

import pandas as pd


# =========================================================
# 1. File paths
# =========================================================
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


# =========================================================
# 2. Event mapping
# =========================================================
TASK_EVENTS = [
    "PushEvent",
    "PullRequestEvent",
    "IssuesEvent",
    "GollumEvent",
    "ReleaseEvent",
    "CreateEvent",
    "DeleteEvent",
]

COMMUNITY_EVENTS = [
    "ForkEvent",
    "WatchEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "CommitCommentEvent",
    "IssueCommentEvent",
    "DiscussionEvent",
]

PLOT_EVENTS = TASK_EVENTS + COMMUNITY_EVENTS

EVENT_GROUP = {
    **{event: "Task-Oriented Activity" for event in TASK_EVENTS},
    **{event: "Community-Signal Activity" for event in COMMUNITY_EVENTS},
}


# =========================================================
# 3. Filtering and inspection rules
# =========================================================
BOT_SUFFIX = re.compile(r"\[bot\]$", re.IGNORECASE)

KNOWN_BOT_LOGINS = {
    "dependabot",
    "dependabot-preview",
    "renovate",
    "renovate-bot",
    "github-actions",
    "github-actions[bot]",
}

ETH_SPAM_START = pd.Timestamp("2017-03-25")
ETH_SPAM_END = pd.Timestamp("2017-03-28")

# An account is classified as a spam account only if it opened
# at least 20 issues during the identified anomaly window.
SPAM_OPEN_THRESHOLD = 20

# These dates are inspected in Excel but are not removed.
CHECK_DATES = pd.to_datetime([
    "2017-04-10",
    "2019-01-26",
    "2019-01-28",
])


# =========================================================
# 4. Helper functions
# =========================================================
def find_column(df, candidates, file_path):
    lower_map = {str(column).lower(): column for column in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]

    raise ValueError(
        f"Cannot find {candidates} in {file_path}. "
        f"Available columns: {list(df.columns)}"
    )


def is_confirmed_bot(login):
    if pd.isna(login):
        return False

    login = str(login).strip().lower()

    return bool(BOT_SUFFIX.search(login)) or login in KNOWN_BOT_LOGINS


def extract_issue_action(payload):
    if pd.isna(payload):
        return None

    try:
        if isinstance(payload, dict):
            return payload.get("action")

        return json.loads(payload).get("action")

    except (json.JSONDecodeError, TypeError, AttributeError):
        return None


def load_price_data(price_path, start_date, end_date):
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
        .drop_duplicates("date", keep="last")
    )

    return price_df[
        (price_df["date"] >= start_date) &
        (price_df["date"] <= end_date)
    ].copy()


def build_spam_candidates(df, project):
    columns = [
        "actor_login",
        "opened_issue_count",
        "first_opened_issue",
        "last_opened_issue",
        "classified_as_spam",
    ]

    if project != "Ethereum":
        return pd.DataFrame(columns=columns), set()

    issue_open_events = df[
        (df["event_type"] == "IssuesEvent") &
        (df["date"].between(ETH_SPAM_START, ETH_SPAM_END)) &
        (df["issue_action"] == "opened") &
        (df["actor_login"].notna())
    ].copy()

    candidates = (
        issue_open_events.groupby("actor_login")
        .agg(
            opened_issue_count=("event_type", "size"),
            first_opened_issue=("created_at", "min"),
            last_opened_issue=("created_at", "max"),
        )
        .reset_index()
        .sort_values("opened_issue_count", ascending=False)
    )

    spam_accounts = set(
        candidates.loc[
            candidates["opened_issue_count"] >= SPAM_OPEN_THRESHOLD,
            "actor_login",
        ].astype(str)
    )

    candidates["classified_as_spam"] = (
        candidates["actor_login"].astype(str).isin(spam_accounts)
    )

    return candidates, spam_accounts


def summarize_excluded_accounts(excluded_events):
    columns = [
        "excluded_reason",
        "actor_login",
        "actor_id",
        "event_count",
        "first_event",
        "last_event",
        "event_types",
    ]

    if excluded_events.empty:
        return pd.DataFrame(columns=columns)

    return (
        excluded_events.groupby(
            ["excluded_reason", "actor_login", "actor_id"],
            dropna=False,
        )
        .agg(
            event_count=("event_type", "size"),
            first_event=("created_at", "min"),
            last_event=("created_at", "max"),
            event_types=(
                "event_type",
                lambda x: ", ".join(sorted(x.astype(str).unique())),
            ),
        )
        .reset_index()
        .sort_values(
            ["excluded_reason", "event_count"],
            ascending=[True, False],
        )
    )


def summarize_check_dates(raw_df):
    check_events = raw_df[
        raw_df["date"].isin(CHECK_DATES) &
        raw_df["event_type"].isin(TASK_EVENTS)
    ].copy()

    event_type_summary = (
        check_events.groupby(
            ["date", "event_type", "issue_action"],
            dropna=False,
        )
        .size()
        .reset_index(name="event_count")
        .sort_values(
            ["date", "event_count"],
            ascending=[True, False],
        )
    )

    account_summary = (
        check_events.groupby(
            [
                "date",
                "event_type",
                "issue_action",
                "actor_login",
                "actor_id",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="event_count")
        .sort_values(
            ["date", "event_count"],
            ascending=[True, False],
        )
    )

    return event_type_summary, account_summary


# =========================================================
# 5. Process each focal project
# =========================================================
def process_project(project, event_path, price_path):
    required_columns = {
        "event_type",
        "created_at",
        "actor_id",
        "actor_login",
        "payload",
    }

    df = pd.read_csv(
        event_path,
        low_memory=False,
        usecols=lambda column: column in required_columns,
    )

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{project} is missing columns: {sorted(missing_columns)}"
        )

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce",
        format="mixed",
    )

    df = df.dropna(subset=["created_at", "event_type"]).copy()
    df["date"] = df["created_at"].dt.normalize()
    df["issue_action"] = df["payload"].map(extract_issue_action)

    df["is_confirmed_bot"] = df["actor_login"].map(is_confirmed_bot)

    spam_candidates, spam_accounts = build_spam_candidates(
        df,
        project,
    )

    # Only remove activity from accounts classified as spam,
    # and only during the identified March 2017 anomaly window.
    is_eth_spam_account_event = (
        (project == "Ethereum") &
        (df["date"].between(ETH_SPAM_START, ETH_SPAM_END)) &
        (df["actor_login"].astype(str).isin(spam_accounts))
    )

    df["excluded_reason"] = ""

    df.loc[
        df["is_confirmed_bot"],
        "excluded_reason",
    ] = "confirmed_bot"

    df.loc[
        is_eth_spam_account_event & ~df["is_confirmed_bot"],
        "excluded_reason",
    ] = "ethereum_issue_spam_account"

    df.loc[
        is_eth_spam_account_event & df["is_confirmed_bot"],
        "excluded_reason",
    ] = "confirmed_bot;ethereum_issue_spam_account"

    excluded_events = df[df["excluded_reason"] != ""].copy()
    retained_events = df[df["excluded_reason"] == ""].copy()

    excluded_accounts = summarize_excluded_accounts(excluded_events)

    check_event_types, check_accounts = summarize_check_dates(df)

    plot_events = retained_events[
        retained_events["event_type"].isin(PLOT_EVENTS)
    ].copy()

    start_date = df["date"].min()
    end_date = df["date"].max()

    all_dates = pd.DataFrame({
        "date": pd.date_range(start_date, end_date, freq="D")
    })

    daily_event_types = (
        plot_events.groupby(["date", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=PLOT_EVENTS, fill_value=0)
        .reset_index()
    )

    daily_plot = all_dates.merge(
        daily_event_types,
        on="date",
        how="left",
    )

    daily_plot[PLOT_EVENTS] = (
        daily_plot[PLOT_EVENTS]
        .fillna(0)
        .astype(int)
    )

    daily_plot["task_oriented_events"] = (
        daily_plot[TASK_EVENTS].sum(axis=1)
    )

    daily_plot["community_signal_events"] = (
        daily_plot[COMMUNITY_EVENTS].sum(axis=1)
    )

    daily_plot["total_mapped_events"] = (
        daily_plot[PLOT_EVENTS].sum(axis=1)
    )

    price_df = load_price_data(price_path, start_date, end_date)

    daily_plot = daily_plot.merge(
        price_df,
        on="date",
        how="left",
    )

    chart1_input = daily_plot[
        [
            "date",
            "community_signal_events",
            "task_oriented_events",
            "closing_price",
        ]
    ].copy()

    chart1_input.columns = [
        "Date",
        "Community-Signal Events",
        "Task-Oriented Events",
        f"{project} Closing Price (USD)",
    ]

    event_totals = (
        plot_events.groupby("event_type")
        .size()
        .reindex(PLOT_EVENTS, fill_value=0)
        .rename("event_count")
        .reset_index()
    )

    event_totals = event_totals[
        event_totals["event_count"] > 0
    ].copy()

    event_totals["activity_measure"] = (
        event_totals["event_type"].map(EVENT_GROUP)
    )

    event_totals["share_percent"] = (
        event_totals["event_count"] /
        event_totals["event_count"].sum() * 100
    )

    pie_input = event_totals[
        ["event_type", "event_count"]
    ].copy()

    bot_events_removed = int(df["is_confirmed_bot"].sum())

    spam_events_removed = int(
        (is_eth_spam_account_event & ~df["is_confirmed_bot"]).sum()
    )

    summary = {
        "project": project,
        "raw_events": len(df),
        "confirmed_bot_events_removed": bot_events_removed,
        "spam_accounts_removed": len(spam_accounts),
        "spam_account_events_removed": spam_events_removed,
        "total_events_removed": len(excluded_events),
        "remaining_events": len(retained_events),
        "events_used_in_figures": len(plot_events),
        "missing_actor_login": int(df["actor_login"].isna().sum()),
    }

    print(f"\n{'=' * 72}")
    print(project)
    print(pd.DataFrame([summary]).to_string(index=False))

    return {
        "chart1_input": chart1_input,
        "daily_plot": daily_plot,
        "pie_input": pie_input,
        "event_totals": event_totals,
        "spam_candidates": spam_candidates,
        "excluded_accounts": excluded_accounts,
        "check_event_types": check_event_types,
        "check_accounts": check_accounts,
        "summary": summary,
    }


# =========================================================
# 6. Run processing
# =========================================================
btc = process_project("Bitcoin", BTC_EVENTS, BTC_PRICE)
eth = process_project("Ethereum", ETH_EVENTS, ETH_PRICE)

summary_df = pd.DataFrame([
    btc["summary"],
    eth["summary"],
])


# =========================================================
# 7. Export Excel workbook
# =========================================================
with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl",
    date_format="yyyy-mm-dd",
    datetime_format="yyyy-mm-dd",
) as writer:

    btc["chart1_input"].to_excel(
        writer,
        sheet_name="BTC_chart1_input",
        index=False,
    )

    eth["chart1_input"].to_excel(
        writer,
        sheet_name="ETH_chart1_input",
        index=False,
    )

    btc["pie_input"].to_excel(
        writer,
        sheet_name="BTC_pie_input",
        index=False,
    )

    eth["pie_input"].to_excel(
        writer,
        sheet_name="ETH_pie_input",
        index=False,
    )

    btc["daily_plot"].to_excel(
        writer,
        sheet_name="BTC_daily_plot",
        index=False,
    )

    eth["daily_plot"].to_excel(
        writer,
        sheet_name="ETH_daily_plot",
        index=False,
    )

    btc["event_totals"].to_excel(
        writer,
        sheet_name="BTC_event_totals",
        index=False,
    )

    eth["event_totals"].to_excel(
        writer,
        sheet_name="ETH_event_totals",
        index=False,
    )

    summary_df.to_excel(
        writer,
        sheet_name="Exclusion_summary",
        index=False,
    )

    eth["spam_candidates"].to_excel(
        writer,
        sheet_name="ETH_spam_candidates",
        index=False,
    )

    btc["excluded_accounts"].to_excel(
        writer,
        sheet_name="BTC_excluded_accounts",
        index=False,
    )

    eth["excluded_accounts"].to_excel(
        writer,
        sheet_name="ETH_excluded_accounts",
        index=False,
    )

    btc["check_event_types"].to_excel(
        writer,
        sheet_name="BTC_check_event_types",
        index=False,
    )

    eth["check_event_types"].to_excel(
        writer,
        sheet_name="ETH_check_event_types",
        index=False,
    )

    btc["check_accounts"].to_excel(
        writer,
        sheet_name="BTC_check_accounts",
        index=False,
    )

    eth["check_accounts"].to_excel(
        writer,
        sheet_name="ETH_check_accounts",
        index=False,
    )

    for worksheet in writer.book.worksheets:
        worksheet.freeze_panes = "A2"

print(f"\nSaved: {OUTPUT_FILE}")
print("\nFinal exclusion summary:")
print(summary_df.to_string(index=False))