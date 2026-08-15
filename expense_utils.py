"""
expense_utils.py
============================================================
ExpenseLens AI -- shared core engine.

This module is intentionally the ONE place where all data storage,
calculations, insights, and the AI prediction logic live. Both
app.py (the Flask browser app) and terminal_app.py (the command-line
app) import from here, so the two interfaces never duplicate logic
and always produce identical numbers.

Data storage is deliberately simple, per project scope:
    - data/expenses.csv   -> every recorded expense (Pandas reads/writes it)
    - data/user_data.json -> name, income, savings goal, category rules

No database is used. No SQLite, no SQLAlchemy.
============================================================
"""

import os
import json
import uuid
from datetime import datetime

import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# ------------------------------------------------------------------
# PATHS & CONSTANTS
# ------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.csv")
USER_FILE = os.path.join(DATA_DIR, "user_data.json")

EXPENSE_COLUMNS = ["id", "date", "category", "amount", "description"]

CATEGORIES = [
    "Food", "Groceries", "Milk", "Vegetables", "Transport", "Shopping",
    "Entertainment", "Bills", "Education", "Healthcare", "Mobile/Internet",
    "Rent", "Travel", "Personal Care", "Subscriptions", "Other",
]

# Default essential / non-essential classification. The user can
# override any of these from the Analytics page.
DEFAULT_CLASSIFICATION = {
    "Food": "Essential",
    "Groceries": "Essential",
    "Milk": "Essential",
    "Vegetables": "Essential",
    "Transport": "Essential",
    "Rent": "Essential",
    "Healthcare": "Essential",
    "Bills": "Essential",
    "Education": "Essential",
    "Mobile/Internet": "Essential",
    "Shopping": "Non-Essential",
    "Entertainment": "Non-Essential",
    "Subscriptions": "Non-Essential",
    "Personal Care": "Non-Essential",
    "Travel": "Non-Essential",
    "Other": "Non-Essential",
}

MIN_MONTHS_FOR_PREDICTION = 3


# ------------------------------------------------------------------
# FILE SETUP
# ------------------------------------------------------------------

def ensure_data_files():
    """Create the data folder, user_data.json, and a sample expenses.csv
    the first time the application runs, so nothing crashes on a fresh
    checkout and the user has realistic demo data to explore."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USER_FILE):
        save_user_data({
            "name": "Demo User",
            "monthly_income": 30000,
            "savings_goal": 5000,
            "category_classification": DEFAULT_CLASSIFICATION.copy(),
            "setup_complete": False,
        })

    if not os.path.exists(EXPENSES_FILE):
        _write_sample_expenses()


def _write_sample_expenses():
    """Generate a few months of realistic, varied SAMPLE/DEMO expense data
    so graphs, category analysis, month comparison, and the AI prediction
    all have something meaningful to work with immediately."""
    sample_rows = []
    rng = np.random.default_rng(42)

    month_plans = [
        # (year, month, scale) -- scale nudges overall spending up/down
        (2026, 1, 1.00),
        (2026, 2, 1.08),
        (2026, 3, 0.95),
        (2026, 4, 1.15),
    ]

    category_base = {
        "Food": 100, "Groceries": 180, "Milk": 40, "Vegetables": 90,
        "Transport": 70, "Shopping": 250, "Entertainment": 120,
        "Bills": 400, "Education": 150, "Healthcare": 90,
        "Mobile/Internet": 60, "Rent": 900, "Travel": 200,
        "Personal Care": 80, "Subscriptions": 45,
    }

    expense_id = 1
    for year, month, scale in month_plans:
        days_in_month = 28 if month == 2 else 30
        for day in range(1, days_in_month + 1, 2):  # every other day, keeps sample data compact
            n_entries = rng.integers(1, 3)
            for _ in range(n_entries):
                category = rng.choice(list(category_base.keys()))
                base = category_base[category]
                amount = round(max(10, rng.normal(base, base * 0.35)) * scale, 2)
                sample_rows.append({
                    "id": expense_id,
                    "date": "{:04d}-{:02d}-{:02d}".format(year, month, day),
                    "category": category,
                    "amount": amount,
                    "description": "Sample {} expense".format(category.lower()),
                })
                expense_id += 1

    df = pd.DataFrame(sample_rows, columns=EXPENSE_COLUMNS)
    df.to_csv(EXPENSES_FILE, index=False)


# ------------------------------------------------------------------
# USER DATA (JSON)
# ------------------------------------------------------------------

def load_user_data():
    ensure_data_files()
    try:
        with open(USER_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {
            "name": "Demo User", "monthly_income": 30000, "savings_goal": 5000,
            "category_classification": DEFAULT_CLASSIFICATION.copy(), "setup_complete": False,
        }
    data.setdefault("category_classification", DEFAULT_CLASSIFICATION.copy())
    return data


def save_user_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)


def update_income(monthly_income, savings_goal=None, name=None):
    data = load_user_data()
    data["monthly_income"] = monthly_income
    if savings_goal is not None:
        data["savings_goal"] = savings_goal
    if name:
        data["name"] = name
    data["setup_complete"] = True
    save_user_data(data)
    return data


def update_classification(category, classification):
    """Let the user reclassify a category as Essential / Non-Essential."""
    data = load_user_data()
    data["category_classification"][category] = classification
    save_user_data(data)
    return data


# ------------------------------------------------------------------
# EXPENSE DATA (CSV)
# ------------------------------------------------------------------

def load_expenses():
    """Load expenses.csv into a clean, typed DataFrame. Never crashes --
    returns an empty (but correctly shaped) DataFrame on any problem."""
    ensure_data_files()
    try:
        df = pd.read_csv(EXPENSES_FILE)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=EXPENSE_COLUMNS)

    for col in EXPENSE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount", "category"])
    df["description"] = df["description"].fillna("")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    # Repair any missing/duplicate ids so edit/delete always work reliably
    if df["id"].isnull().any() or df["id"].duplicated().any():
        df = df.reset_index(drop=True)
        df["id"] = range(1, len(df) + 1)
        save_expenses(df)

    df["id"] = df["id"].astype(int)
    return df.sort_values("date").reset_index(drop=True)


def save_expenses(df):
    os.makedirs(DATA_DIR, exist_ok=True)
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(EXPENSES_FILE, index=False, columns=EXPENSE_COLUMNS)


def _next_id(df):
    if df.empty:
        return 1
    return int(df["id"].max()) + 1


# ------------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------------

def validate_amount(value):
    """Return (float_amount, error_message_or_None)."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None, "Amount must be a valid number."
    if amount <= 0:
        return None, "Amount must be greater than zero."
    if amount > 10_000_000:
        return None, "Amount seems unrealistically large. Please check the value."
    return round(amount, 2), None


def validate_date(value):
    """Return (datetime_or_None, error_message_or_None)."""
    if not value:
        return datetime.today(), None
    try:
        parsed = pd.to_datetime(value)
        return parsed, None
    except (ValueError, TypeError):
        return None, "Please enter a valid date."


def validate_category(category, custom_category=None):
    """Return (final_category_string, error_message_or_None)."""
    if category not in CATEGORIES:
        return None, "Please select a valid category."
    if category == "Other":
        custom = (custom_category or "").strip()
        if not custom:
            return None, "Please enter a custom category name for 'Other'."
        return custom.title(), None
    return category, None


# ------------------------------------------------------------------
# EXPENSE CRUD
# ------------------------------------------------------------------

def add_expense(date_value, category, amount_value, description="", custom_category=None):
    """Validate and append a new expense. Returns (success, message)."""
    final_category, cat_error = validate_category(category, custom_category)
    if cat_error:
        return False, cat_error

    amount, amount_error = validate_amount(amount_value)
    if amount_error:
        return False, amount_error

    date_parsed, date_error = validate_date(date_value)
    if date_error:
        return False, date_error

    df = load_expenses()
    new_row = {
        "id": _next_id(df),
        "date": date_parsed,
        "category": final_category,
        "amount": amount,
        "description": (description or "").strip()[:200],
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_expenses(df)

    # Make sure new custom categories get a default classification
    user_data = load_user_data()
    if final_category not in user_data["category_classification"]:
        user_data["category_classification"][final_category] = "Non-Essential"
        save_user_data(user_data)

    return True, "Expense added successfully."


def edit_expense(expense_id, date_value, category, amount_value, description="", custom_category=None):
    """Validate and update an existing expense by id. Returns (success, message)."""
    final_category, cat_error = validate_category(category, custom_category)
    if cat_error:
        return False, cat_error

    amount, amount_error = validate_amount(amount_value)
    if amount_error:
        return False, amount_error

    date_parsed, date_error = validate_date(date_value)
    if date_error:
        return False, date_error

    df = load_expenses()
    if expense_id not in df["id"].values:
        return False, "Expense not found. It may have already been deleted."

    idx = df.index[df["id"] == expense_id][0]
    df.loc[idx, "date"] = date_parsed
    df.loc[idx, "category"] = final_category
    df.loc[idx, "amount"] = amount
    df.loc[idx, "description"] = (description or "").strip()[:200]
    save_expenses(df)
    return True, "Expense updated successfully."


def delete_expense(expense_id):
    df = load_expenses()
    if expense_id not in df["id"].values:
        return False, "Expense not found. It may have already been deleted."
    df = df[df["id"] != expense_id]
    save_expenses(df)
    return True, "Expense deleted successfully."


def import_csv(filepath):
    """
    Import expenses from an uploaded CSV. Required columns: date, category,
    amount. 'description' is optional. Returns (success_count, error_message).
    Invalid individual rows are skipped rather than failing the whole import.
    """
    try:
        incoming = pd.read_csv(filepath)
    except Exception:
        return 0, "The uploaded file could not be read as a valid CSV."

    incoming.columns = [c.strip().lower() for c in incoming.columns]
    required = {"date", "category", "amount"}
    if not required.issubset(set(incoming.columns)):
        missing = required - set(incoming.columns)
        return 0, "The CSV is missing required column(s): {}.".format(", ".join(sorted(missing)))

    if "description" not in incoming.columns:
        incoming["description"] = ""

    df = load_expenses()
    added = 0
    for _, row in incoming.iterrows():
        amount, amount_error = validate_amount(row.get("amount"))
        date_parsed, date_error = validate_date(row.get("date"))
        category_raw = str(row.get("category", "")).strip()
        if amount_error or date_error or not category_raw:
            continue  # skip invalid rows rather than aborting the whole import

        new_row = {
            "id": _next_id(df),
            "date": date_parsed,
            "category": category_raw.title(),
            "amount": amount,
            "description": str(row.get("description", "") or "")[:200],
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        added += 1

    if added == 0:
        return 0, "No valid rows were found in the uploaded CSV."

    save_expenses(df)

    user_data = load_user_data()
    for cat in df["category"].unique():
        if cat not in user_data["category_classification"]:
            user_data["category_classification"][cat] = "Non-Essential"
    save_user_data(user_data)

    return added, None


# ------------------------------------------------------------------
# SUMMARIES & CALCULATIONS
# ------------------------------------------------------------------

def get_today_summary(df):
    today = pd.Timestamp(datetime.today().date())
    today_df = df[df["date"] == today]
    return {
        "total": round(float(today_df["amount"].sum()), 2),
        "count": int(len(today_df)),
        "categories": _category_breakdown(today_df),
    }


def _category_breakdown(df):
    """Category totals + percentages, sorted highest spend first."""
    if df.empty:
        return []
    total = df["amount"].sum()
    grouped = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    breakdown = []
    for rank, (category, amount) in enumerate(grouped.items(), start=1):
        breakdown.append({
            "rank": rank,
            "category": category,
            "amount": round(float(amount), 2),
            "percentage": round(float(amount / total * 100), 1) if total else 0,
        })
    return breakdown


def get_month_summary(df, year, month):
    month_df = df[(df["date"].dt.year == year) & (df["date"].dt.month == month)]
    total = round(float(month_df["amount"].sum()), 2)
    days_elapsed = month_df["date"].dt.day.nunique() or 1
    breakdown = _category_breakdown(month_df)

    return {
        "year": year,
        "month": month,
        "total": total,
        "transaction_count": int(len(month_df)),
        "categories": breakdown,
        "daily_average": round(total / days_elapsed, 2),
        "highest_category": breakdown[0] if breakdown else None,
        "lowest_category": breakdown[-1] if breakdown else None,
    }


def get_year_summary(df, year):
    year_df = df[df["date"].dt.year == year]
    monthly_totals = []
    for month in range(1, 13):
        month_total = float(year_df[year_df["date"].dt.month == month]["amount"].sum())
        monthly_totals.append({"month": month, "total": round(month_total, 2)})

    non_zero = [m for m in monthly_totals if m["total"] > 0]
    highest_month = max(non_zero, key=lambda m: m["total"]) if non_zero else None
    lowest_month = min(non_zero, key=lambda m: m["total"]) if non_zero else None

    return {
        "year": year,
        "total": round(float(year_df["amount"].sum()), 2),
        "monthly_totals": monthly_totals,
        "highest_month": highest_month,
        "lowest_month": lowest_month,
    }


def compare_months(df, year1, month1, year2, month2):
    """Compare two calendar months and highlight which categories moved the most."""
    m1 = get_month_summary(df, year1, month1)
    m2 = get_month_summary(df, year2, month2)

    increase = round(m2["total"] - m1["total"], 2)
    percentage = round((increase / m1["total"] * 100), 1) if m1["total"] else 0

    cat1 = {c["category"]: c["amount"] for c in m1["categories"]}
    cat2 = {c["category"]: c["amount"] for c in m2["categories"]}
    all_categories = set(cat1) | set(cat2)

    deltas = []
    for cat in all_categories:
        delta = round(cat2.get(cat, 0) - cat1.get(cat, 0), 2)
        if delta != 0:
            deltas.append({"category": cat, "delta": delta})
    deltas.sort(key=lambda d: abs(d["delta"]), reverse=True)

    return {
        "month1": m1, "month2": m2,
        "increase": increase, "percentage": percentage,
        "category_deltas": deltas[:8],
    }


def essential_vs_nonessential(df, classification_map):
    if df.empty:
        return {"essential": 0, "non_essential": 0, "essential_pct": 0, "non_essential_pct": 0}

    df = df.copy()
    df["classification"] = df["category"].map(lambda c: classification_map.get(c, "Non-Essential"))
    total = df["amount"].sum()
    essential = float(df[df["classification"] == "Essential"]["amount"].sum())
    non_essential = float(df[df["classification"] == "Non-Essential"]["amount"].sum())

    return {
        "essential": round(essential, 2),
        "non_essential": round(non_essential, 2),
        "essential_pct": round(essential / total * 100, 1) if total else 0,
        "non_essential_pct": round(non_essential / total * 100, 1) if total else 0,
    }


def get_savings_summary(df, user_data, year, month):
    income = float(user_data.get("monthly_income", 0) or 0)
    savings_goal = float(user_data.get("savings_goal", 0) or 0)
    month_summary = get_month_summary(df, year, month)
    expenses = month_summary["total"]
    remaining = round(income - expenses, 2)
    savings_pct = round((remaining / income * 100), 1) if income else 0

    return {
        "income": income,
        "expenses": expenses,
        "remaining": remaining,
        "savings_goal": savings_goal,
        "savings_pct": savings_pct,
        "goal_met": remaining >= savings_goal,
    }


# ------------------------------------------------------------------
# INSIGHTS & SAVING SUGGESTIONS (plain data-driven text, no LLM)
# ------------------------------------------------------------------

def generate_insights(df, user_data):
    """Turn calculated numbers into simple, human-readable sentences."""
    insights = []
    if df.empty:
        return ["Add some expenses to start seeing personalized insights."]

    now = datetime.today()
    this_month = get_month_summary(df, now.year, now.month)
    savings = get_savings_summary(df, user_data, now.year, now.month)

    if this_month["highest_category"]:
        top = this_month["highest_category"]
        insights.append(
            "You spent the most on {} this month (₹{:,.0f}, {}% of total spending).".format(
                top["category"], top["amount"], top["percentage"]
            )
        )

    prev_year, prev_month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
    prev_summary = get_month_summary(df, prev_year, prev_month)
    if prev_summary["total"] > 0:
        change = this_month["total"] - prev_summary["total"]
        pct = round(change / prev_summary["total"] * 100, 1)
        direction = "increased" if change > 0 else "decreased"
        insights.append(
            "Your spending {} by {}% compared with last month.".format(direction, abs(pct))
        )

    if savings["income"] > 0:
        insights.append(
            "Your current savings rate is {}% of your income this month.".format(savings["savings_pct"])
        )

    food_categories = [c for c in this_month["categories"] if c["category"] in ("Food", "Groceries")]
    if food_categories and this_month["total"] > 0:
        food_total = sum(c["amount"] for c in food_categories)
        food_pct = round(food_total / this_month["total"] * 100, 1)
        insights.append("Food and Groceries together represent {}% of your total expenses this month.".format(food_pct))

    return insights


def generate_saving_suggestions(df, reduction_pct=0.12):
    """
    Compare this month's category spending against the trailing 3-month
    average per category. Where a category is unusually high, suggest a
    potential saving if the user reduced it by `reduction_pct`.
    """
    if df.empty:
        return []

    now = datetime.today()
    this_month = get_month_summary(df, now.year, now.month)
    this_cats = {c["category"]: c["amount"] for c in this_month["categories"]}

    cutoff = pd.Timestamp(now) - pd.DateOffset(months=3)
    recent_df = df[(df["date"] < pd.Timestamp(now.year, now.month, 1)) & (df["date"] >= cutoff)]

    suggestions = []
    for category, amount in this_cats.items():
        history = recent_df[recent_df["category"] == category]["amount"].sum()
        months_seen = recent_df[recent_df["category"] == category]["date"].dt.to_period("M").nunique()
        avg = (history / months_seen) if months_seen else 0

        if avg > 0 and amount > avg * 1.15:
            potential_saving = round(amount * reduction_pct, 2)
            suggestions.append({
                "category": category,
                "current_amount": amount,
                "average_amount": round(avg, 2),
                "reduction_pct": int(reduction_pct * 100),
                "potential_saving": potential_saving,
                "message": (
                    "You spent ₹{:,.0f} on {} this month, above your recent average of ₹{:,.0f}. "
                    "Reducing this category by {}% could save approximately ₹{:,.0f}."
                ).format(amount, category, avg, int(reduction_pct * 100), potential_saving),
            })

    suggestions.sort(key=lambda s: s["potential_saving"], reverse=True)
    return suggestions[:5]


# ------------------------------------------------------------------
# AI SPENDING PREDICTION (regression on monthly aggregates)
# ------------------------------------------------------------------

def _build_monthly_features(df):
    """
    Aggregate raw expenses into one row per calendar month:
    month_index, total spending, transaction count, and previous
    month's spending (the strongest predictor of next month's spending).
    """
    monthly = (
        df.assign(period=df["date"].dt.to_period("M"))
        .groupby("period")
        .agg(total=("amount", "sum"), transactions=("amount", "count"))
        .sort_index()
        .reset_index()
    )
    monthly["month_index"] = range(len(monthly))
    monthly["prev_month_total"] = monthly["total"].shift(1)
    monthly = monthly.dropna(subset=["prev_month_total"])
    return monthly


def predict_next_month(df):
    """
    Estimate next month's total spending using simple regression models
    trained on the user's own monthly history. Returns a dictionary that
    the UI can render directly, or an 'available: False' message if
    there isn't enough historical data yet.
    """
    if df.empty:
        return {"available": False, "message": "Add some expenses to generate a prediction."}

    monthly = _build_monthly_features(df)

    if len(monthly) < MIN_MONTHS_FOR_PREDICTION:
        return {
            "available": False,
            "message": "Not enough data yet. Add at least {} months of expense data "
                        "to generate a spending estimate.".format(MIN_MONTHS_FOR_PREDICTION + 1),
        }

    feature_cols = ["month_index", "prev_month_total", "transactions"]
    X = monthly[feature_cols].values
    y = monthly["total"].values

    next_month_index = monthly["month_index"].max() + 1
    next_prev_total = monthly["total"].iloc[-1]
    next_transactions = round(monthly["transactions"].mean())
    X_next = np.array([[next_month_index, next_prev_total, next_transactions]])

    models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=42, max_depth=3),
        "Random Forest": RandomForestRegressor(random_state=42, n_estimators=100, max_depth=4),
    }

    model_results = []
    feature_importance = None
    best_model_name = None
    best_prediction = None

    for name, model in models.items():
        try:
            model.fit(X, y)
            prediction = float(model.predict(X_next)[0])
            in_sample_pred = model.predict(X)
            mae = float(mean_absolute_error(y, in_sample_pred))
            r2 = float(r2_score(y, in_sample_pred)) if len(y) > 2 else None

            model_results.append({
                "model": name,
                "prediction": round(max(0, prediction), 2),
                "mae": round(mae, 2),
                "r2": round(r2, 3) if r2 is not None else None,
            })

            if name == "Random Forest" and hasattr(model, "feature_importances_"):
                pairs = sorted(zip(feature_cols, model.feature_importances_), key=lambda p: p[1], reverse=True)
                feature_importance = [
                    {"feature": _friendly_feature_name(f), "importance": round(float(v) * 100, 1)}
                    for f, v in pairs
                ]
        except Exception:
            continue

    if not model_results:
        return {"available": False, "message": "The prediction could not be generated for this dataset."}

    # Average across models for a stable headline estimate; also surface the single best (lowest MAE) model.
    average_estimate = round(sum(r["prediction"] for r in model_results) / len(model_results), 2)
    best = min(model_results, key=lambda r: r["mae"])

    return {
        "available": True,
        "months_used": len(monthly),
        "model_results": model_results,
        "average_estimate": average_estimate,
        "best_model": best["model"],
        "best_prediction": best["prediction"],
        "feature_importance": feature_importance,
        "note": "This is a data-driven estimate based on your own spending history, "
                "not a guarantee. More historical data will improve accuracy over time.",
    }


def _friendly_feature_name(name):
    mapping = {
        "month_index": "Time trend (month number)",
        "prev_month_total": "Previous month's spending",
        "transactions": "Number of transactions",
    }
    return mapping.get(name, name)


# ------------------------------------------------------------------
# MATPLOTLIB GRAPHS (used by terminal_app.py)
# ------------------------------------------------------------------

def plot_category_pie(df, title="Spending by Category"):
    import matplotlib.pyplot as plt
    breakdown = _category_breakdown(df)
    if not breakdown:
        print("No expense data available to plot.")
        return
    labels = [b["category"] for b in breakdown]
    values = [b["amount"] for b in breakdown]
    plt.figure(figsize=(7, 7))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_monthly_trend(df, year, title=None):
    import matplotlib.pyplot as plt
    summary = get_year_summary(df, year)
    months = [m["month"] for m in summary["monthly_totals"]]
    totals = [m["total"] for m in summary["monthly_totals"]]
    month_names = [datetime(2000, m, 1).strftime("%b") for m in months]

    plt.figure(figsize=(9, 5))
    plt.bar(month_names, totals, color="#4C6EF5")
    plt.title(title or "Monthly Spending Trend ({})".format(year))
    plt.ylabel("Amount Spent")
    plt.xlabel("Month")
    plt.tight_layout()
    plt.show()


def plot_income_vs_expense(df, user_data, year, month):
    import matplotlib.pyplot as plt
    savings = get_savings_summary(df, user_data, year, month)
    labels = ["Income", "Expenses", "Remaining"]
    values = [savings["income"], savings["expenses"], max(0, savings["remaining"])]
    colors = ["#2f9e44", "#e8590c", "#4C6EF5"]

    plt.figure(figsize=(7, 5))
    plt.bar(labels, values, color=colors)
    plt.title("Income vs Expense vs Remaining ({}/{})".format(month, year))
    plt.ylabel("Amount")
    plt.tight_layout()
    plt.show()
