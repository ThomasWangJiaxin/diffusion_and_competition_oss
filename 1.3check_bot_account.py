from pathlib import Path
import re
import pandas as pd

DATASETS = {
    "Bitcoin": Path(
        "/home/lab0/survival_diffusion_github/Bitcoin/"
        "bitcoin_events_timeline_unified_all_2025_12_31.csv"
    ),
    "Ethereum": Path(
        "/home/lab0/survival_diffusion_github/Ethereum/"
        "eth_events_timeline_unified_all_2025_12_31.csv"
    ),
}

OUTPUT_DIR = Path("/home/lab0/survival_diffusion_github/bot_check")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Exact GitHub bot-account convention and common automation accounts.
CONFIRMED_BOT_PATTERN = re.compile(r"\[bot\]$", re.IGNORECASE)
LIKELY_BOT_PATTERN = re.compile(
    r"(?:^|[-_])bot(?:$|[-_])|"
    r"dependabot|renovate|github-actions|"
    r"codecov|coveralls|snyk|semantic-release|"
    r"allcontributors|stale",
    re.IGNORECASE,
)


def classify_actor(login):
    if pd.isna(login) or not str(login).strip():
        return None

    login = str(login).strip()

    if CONFIRMED_BOT_PATTERN.search(login):
        return "confirmed_[bot]_account"

    if LIKELY_BOT_PATTERN.search(login):
        return "likely_bot_name"

    return None


def check_bot_events(project, file_path):
    if not file_path.exists():
        print(f"[Missing] {project}: {file_path}")
        return None

    df = pd.read_csv(
        file_path,
        low_memory=False,
        usecols=lambda col: col in {
            "event_type",
            "created_at",
            "actor_id",
            "actor_login",
            "actor_email",
            "repository_id",
            "repository_url",
        },
    )

    if "actor_login" not in df.columns:
        raise ValueError(f"{project} has no actor_login column.")

    df["bot_flag"] = df["actor_login"].map(classify_actor)
    bot_events = df[df["bot_flag"].notna()].copy()

    total_events = len(df)
    total_bot_events = len(bot_events)
    total_accounts = bot_events["actor_login"].nunique()

    account_summary = (
        bot_events.groupby(["actor_login", "bot_flag"], dropna=False)
        .agg(
            event_count=("actor_login", "size"),
            first_event=("created_at", "min"),
            last_event=("created_at", "max"),
            event_types=(
                "event_type",
                lambda x: ", ".join(sorted(x.dropna().astype(str).unique())),
            ),
            actor_ids=(
                "actor_id",
                lambda x: ", ".join(
                    sorted(x.dropna().astype(str).unique())[:10]
                ),
            ),
        )
        .reset_index()
        .sort_values(["bot_flag", "event_count"], ascending=[True, False])
    )

    event_type_summary = (
        bot_events.groupby(["bot_flag", "event_type"], dropna=False)
        .size()
        .reset_index(name="event_count")
        .sort_values(["bot_flag", "event_count"], ascending=[True, False])
    )

    account_summary.to_csv(
        OUTPUT_DIR / f"{project.lower()}_bot_accounts.csv",
        index=False,
        encoding="utf-8",
    )
    event_type_summary.to_csv(
        OUTPUT_DIR / f"{project.lower()}_bot_event_types.csv",
        index=False,
        encoding="utf-8",
    )
    bot_events.to_csv(
        OUTPUT_DIR / f"{project.lower()}_suspected_bot_events.csv",
        index=False,
        encoding="utf-8",
    )

    print(f"\n{project}")
    print(f"  Total events: {total_events:,}")
    print(f"  Suspected bot events: {total_bot_events:,} "
          f"({total_bot_events / total_events:.2%})")
    print(f"  Suspected bot accounts: {total_accounts:,}")
    print(account_summary.head(20).to_string(index=False))

    return {
        "project": project,
        "total_events": total_events,
        "suspected_bot_events": total_bot_events,
        "suspected_bot_share": total_bot_events / total_events,
        "suspected_bot_accounts": total_accounts,
    }


results = []
for project, path in DATASETS.items():
    result = check_bot_events(project, path)
    if result is not None:
        results.append(result)

pd.DataFrame(results).to_csv(
    OUTPUT_DIR / "bot_check_summary.csv",
    index=False,
    encoding="utf-8",
)

print(f"\nResults saved to: {OUTPUT_DIR}")