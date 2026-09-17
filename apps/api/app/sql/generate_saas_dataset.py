"""Generates the deterministic SaaS product-analytics practice dataset used
by Phase 6 (Statistics/Experimentation/Business/Product Analytics) exercises
and the funnel/cohort/A-B-test tools.

Usage:
    uv run --project apps/api python -m app.sql.generate_saas_dataset

Writes CSV files to data/sample/saas_product/. Deterministic (fixed random
seed) so every fresh checkout produces byte-identical data — Python/SQL
exercise hidden tests in content/exercises/*.yaml depend on this exact data.

Grain of each table (see also database/seeds/sql_tables.yaml):
    users                  1 row = 1 signed-up user
    events                 1 row = 1 product event (signup/activation/
                           engagement/upgrade), with the user's own
                           signup_date denormalized onto every row so a
                           single-table cohort-retention query works
                           without a join (see app/dataset_hub/
                           product_analytics_engine.py)
    subscriptions          1 row = 1 paid subscription (0 or 1 per user)
    experiment_assignments 1 row = 1 user's assignment to one experiment

Funnel modeled per user: signup -> activated -> engaged -> upgraded, with
channel-dependent conversion so segmentation exercises have a real signal.
Monthly engagement events recur with a per-month "stays active" hazard,
producing a realistic decaying cohort-retention curve rather than a flat
one. Two experiments are baked in with known, deterministic outcomes:
"checkout_redesign" (a real, shippable uplift) and "onboarding_email" (a
small, statistically-ambiguous effect) — both by design, for exercises that
ask the learner to tell the difference.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260601
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTPUT_DIR = REPO_ROOT / "data" / "sample" / "saas_product"

DATASET_START = date(2024, 7, 1)
DATASET_END = date(2026, 2, 1)
DATASET_DAYS = (DATASET_END - DATASET_START).days

N_USERS = 3000

CHANNELS = ["organic", "paid_search", "paid_social", "referral", "content"]
CHANNEL_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]
# Each channel's own activation rate — deliberately different so
# segmentation-by-channel exercises have a real signal to find.
CHANNEL_ACTIVATION_RATE = {
    "organic": 0.78,
    "paid_search": 0.62,
    "paid_social": 0.55,
    "referral": 0.82,
    "content": 0.70,
}
COUNTRIES = ["US", "UK", "DE", "IN", "BR", "CA", "AU"]
COUNTRY_WEIGHTS = [0.35, 0.15, 0.12, 0.15, 0.08, 0.08, 0.07]
PLANS = ["starter", "pro", "enterprise"]
PLAN_WEIGHTS = [0.55, 0.35, 0.10]
PLAN_MRR = {"starter": 29.0, "pro": 99.0, "enterprise": 299.0}

ENGAGED_RATE = 0.55  # share of activated users who go on to engage
UPGRADE_RATE = 0.28  # share of engaged users who upgrade to paid
MONTHLY_STAY_ACTIVE_HAZARD = 0.62  # chance an engaged user is still active in the *next* month
MONTHLY_CHURN_HAZARD = 0.06  # chance a paying subscriber churns in any given active month


def _random_date(start: date, days: int) -> date:
    return start + timedelta(days=random.randint(0, max(days, 0)))


def _weighted_choice(options: list[str], weights: list[float]) -> str:
    return random.choices(options, weights=weights, k=1)[0]


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate() -> dict[str, int]:
    random.seed(SEED)

    users: list[dict] = []
    events: list[dict] = []
    subscriptions: list[dict] = []

    # Signups skew later in the window (mild growth trend: day index biased
    # toward the end via sqrt of a uniform draw) so MoM/QoQ growth exercises
    # have a real upward trend to read, not flat noise.
    for user_id in range(1, N_USERS + 1):
        day_offset = int((random.random() ** 0.6) * DATASET_DAYS)
        signup_date = DATASET_START + timedelta(days=day_offset)
        channel = _weighted_choice(CHANNELS, CHANNEL_WEIGHTS)
        country = _weighted_choice(COUNTRIES, COUNTRY_WEIGHTS)
        users.append(
            {
                "user_id": user_id,
                "signup_date": signup_date.isoformat(),
                "acquisition_channel": channel,
                "country": country,
            }
        )

        events.append(
            {
                "user_id": user_id,
                "signup_date": signup_date.isoformat(),
                "event_name": "signup",
                "event_timestamp": signup_date.isoformat(),
            }
        )

        activated = random.random() < CHANNEL_ACTIVATION_RATE[channel]
        if not activated:
            continue
        activation_date = signup_date + timedelta(days=random.randint(0, 3))
        events.append(
            {
                "user_id": user_id,
                "signup_date": signup_date.isoformat(),
                "event_name": "activated",
                "event_timestamp": activation_date.isoformat(),
            }
        )

        engaged = random.random() < ENGAGED_RATE
        if not engaged:
            continue

        # Recurring monthly engagement, decaying via a "stay active" hazard
        # each month — this is what produces a realistic retention curve.
        month = 0
        engaged_this_month = True
        upgrade_month: int | None = None
        while engaged_this_month and signup_date + timedelta(days=30 * month) < DATASET_END:
            event_date = signup_date + timedelta(days=30 * month + random.randint(0, 10))
            if event_date >= DATASET_END:
                break
            events.append(
                {
                    "user_id": user_id,
                    "signup_date": signup_date.isoformat(),
                    "event_name": "engaged",
                    "event_timestamp": event_date.isoformat(),
                }
            )
            if upgrade_month is None and random.random() < UPGRADE_RATE / 3:
                upgrade_month = month
                events.append(
                    {
                        "user_id": user_id,
                        "signup_date": signup_date.isoformat(),
                        "event_name": "upgraded",
                        "event_timestamp": event_date.isoformat(),
                    }
                )
            month += 1
            engaged_this_month = random.random() < MONTHLY_STAY_ACTIVE_HAZARD

        if upgrade_month is not None:
            plan = _weighted_choice(PLANS, PLAN_WEIGHTS)
            start_date = signup_date + timedelta(days=30 * upgrade_month + 5)
            mrr = PLAN_MRR[plan]
            status = "active"
            end_date = None
            active_months_remaining = (DATASET_END - start_date).days // 30
            for _ in range(active_months_remaining):
                if random.random() < MONTHLY_CHURN_HAZARD:
                    status = "churned"
                    churn_offset = random.randint(1, 29)
                    break
            if status == "churned":
                days_active = 30 * random.randint(1, max(active_months_remaining, 1)) + churn_offset
                end_date = min(
                    start_date + timedelta(days=days_active),
                    DATASET_END - timedelta(days=1),
                )
            subscriptions.append(
                {
                    "subscription_id": len(subscriptions) + 1,
                    "user_id": user_id,
                    "plan": plan,
                    "mrr": mrr,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat() if end_date else "",
                    "status": status,
                }
            )

    # --- Experiments ------------------------------------------------------
    # checkout_redesign: a real, meaningful uplift (~10% -> ~12.5% conversion).
    # onboarding_email: a small, likely-underpowered effect (~30% -> ~31%).
    experiment_assignments: list[dict] = []
    eligible_users = [u["user_id"] for u in users]
    random.shuffle(eligible_users)

    def _assign_experiment(
        name: str, participants: list[int], base_rate: float, treatment_rate: float
    ) -> None:
        for i, uid in enumerate(participants):
            variant = "treatment" if i % 2 == 0 else "control"
            rate = treatment_rate if variant == "treatment" else base_rate
            converted = random.random() < rate
            experiment_assignments.append(
                {
                    "experiment_id": name,
                    "user_id": uid,
                    "variant": variant,
                    "assigned_at": _random_date(DATASET_START, DATASET_DAYS).isoformat(),
                    "converted": int(converted),
                }
            )

    _assign_experiment("checkout_redesign", eligible_users[:2000], base_rate=0.10, treatment_rate=0.125)
    _assign_experiment(
        "onboarding_email",
        eligible_users[2000:4000] or eligible_users[:2000],
        base_rate=0.30,
        treatment_rate=0.31,
    )

    _write_csv(
        OUTPUT_DIR / "users.csv", users, ["user_id", "signup_date", "acquisition_channel", "country"]
    )
    _write_csv(
        OUTPUT_DIR / "events.csv",
        events,
        ["user_id", "signup_date", "event_name", "event_timestamp"],
    )
    _write_csv(
        OUTPUT_DIR / "subscriptions.csv",
        subscriptions,
        ["subscription_id", "user_id", "plan", "mrr", "start_date", "end_date", "status"],
    )
    _write_csv(
        OUTPUT_DIR / "experiment_assignments.csv",
        experiment_assignments,
        ["experiment_id", "user_id", "variant", "assigned_at", "converted"],
    )

    return {
        "users": len(users),
        "events": len(events),
        "subscriptions": len(subscriptions),
        "experiment_assignments": len(experiment_assignments),
    }


if __name__ == "__main__":
    counts = generate()
    for table, count in counts.items():
        print(f"{table}: {count} rows")
    print(f"\nWritten to {OUTPUT_DIR}")
