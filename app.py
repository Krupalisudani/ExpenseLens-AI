"""
app.py -- ExpenseLens AI (Browser Mode)
============================================================
"Understand your spending. Make smarter financial decisions."

A Flask web interface over the shared expense_utils engine. This
file is intentionally thin: every calculation, validation rule, and
prediction lives in expense_utils.py so the browser app and the
terminal app (terminal_app.py) always agree on the numbers.

No database. No SQLite. Data lives in data/expenses.csv and
data/user_data.json, both read/written through Pandas / json.
============================================================
"""

import os
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash
)
from werkzeug.utils import secure_filename

import expense_utils as eu

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_TMP_DIR = os.path.join(BASE_DIR, "data", "_tmp_uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("EXPENSELENS_SECRET_KEY", "dev-secret-key-change-in-production")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

eu.ensure_data_files()
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def parse_year_month(request_args, default_today=True):
    """Read ?year=&month= from query params, defaulting to the current month."""
    today = datetime.today()
    try:
        year = int(request_args.get("year", today.year))
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request_args.get("month", today.month))
    except (TypeError, ValueError):
        month = today.month
    month = min(max(month, 1), 12)
    return year, month


# ------------------------------------------------------------------
# ROUTES: SETUP
# ------------------------------------------------------------------

@app.route("/")
def index():
    user_data = eu.load_user_data()
    return render_template("index.html", user=user_data)


@app.route("/setup", methods=["POST"])
def setup():
    name = request.form.get("name", "").strip()[:40] or "User"
    income_raw = request.form.get("monthly_income", "0")
    goal_raw = request.form.get("savings_goal", "0")

    income, income_error = eu.validate_amount(income_raw)
    if income_error:
        flash("Monthly income: {}".format(income_error), "error")
        return redirect(url_for("index"))

    goal = 0.0
    if goal_raw.strip():
        goal, goal_error = eu.validate_amount(goal_raw)
        if goal_error:
            flash("Savings goal: {}".format(goal_error), "error")
            return redirect(url_for("index"))

    eu.update_income(income, goal, name)
    flash("Welcome, {}! Your profile has been saved.".format(name), "success")
    return redirect(url_for("dashboard"))


# ------------------------------------------------------------------
# ROUTES: DASHBOARD
# ------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    user_data = eu.load_user_data()
    df = eu.load_expenses()
    today = datetime.today()

    today_summary = eu.get_today_summary(df)
    month_summary = eu.get_month_summary(df, today.year, today.month)
    savings = eu.get_savings_summary(df, user_data, today.year, today.month)
    insights = eu.generate_insights(df, user_data)

    return render_template(
        "dashboard.html",
        user=user_data,
        today_summary=today_summary,
        month_summary=month_summary,
        savings=savings,
        insights=insights,
        has_data=not df.empty,
        current_month_name=today.strftime("%B %Y"),
    )


@app.route("/update_settings", methods=["POST"])
def update_settings():
    income_raw = request.form.get("monthly_income", "0")
    goal_raw = request.form.get("savings_goal", "0")
    name = request.form.get("name", "").strip()[:40]

    income, income_error = eu.validate_amount(income_raw)
    if income_error:
        flash("Monthly income: {}".format(income_error), "error")
        return redirect(request.referrer or url_for("dashboard"))

    goal = 0.0
    if goal_raw.strip():
        goal, goal_error = eu.validate_amount(goal_raw)
        if goal_error:
            flash("Savings goal: {}".format(goal_error), "error")
            return redirect(request.referrer or url_for("dashboard"))

    eu.update_income(income, goal, name if name else None)
    flash("Settings updated successfully.", "success")
    return redirect(request.referrer or url_for("dashboard"))


# ------------------------------------------------------------------
# ROUTES: EXPENSES (VIEW / ADD / EDIT / DELETE / IMPORT)
# ------------------------------------------------------------------

@app.route("/expenses")
def expenses_page():
    df = eu.load_expenses()
    records = df.sort_values("date", ascending=False).copy()
    records["date_str"] = records["date"].dt.strftime("%Y-%m-%d")
    expense_list = records.to_dict(orient="records")

    return render_template(
        "expenses.html",
        expenses=expense_list,
        categories=eu.CATEGORIES,
        today=datetime.today().strftime("%Y-%m-%d"),
        has_data=not df.empty,
    )


@app.route("/expenses/add", methods=["POST"])
def add_expense_route():
    success, message = eu.add_expense(
        date_value=request.form.get("date", ""),
        category=request.form.get("category", ""),
        amount_value=request.form.get("amount", ""),
        description=request.form.get("description", ""),
        custom_category=request.form.get("custom_category", ""),
    )
    flash(message, "success" if success else "error")
    return redirect(url_for("expenses_page"))


@app.route("/expenses/edit/<int:expense_id>", methods=["POST"])
def edit_expense_route(expense_id):
    success, message = eu.edit_expense(
        expense_id=expense_id,
        date_value=request.form.get("date", ""),
        category=request.form.get("category", ""),
        amount_value=request.form.get("amount", ""),
        description=request.form.get("description", ""),
        custom_category=request.form.get("custom_category", ""),
    )
    flash(message, "success" if success else "error")
    return redirect(url_for("expenses_page"))


@app.route("/expenses/delete/<int:expense_id>", methods=["POST"])
def delete_expense_route(expense_id):
    success, message = eu.delete_expense(expense_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("expenses_page"))


@app.route("/expenses/import", methods=["POST"])
def import_expenses_route():
    if "csv_file" not in request.files or request.files["csv_file"].filename == "":
        flash("Please choose a CSV file to import.", "error")
        return redirect(url_for("expenses_page"))

    file = request.files["csv_file"]
    if not file.filename.lower().endswith(".csv"):
        flash("Only .csv files can be imported.", "error")
        return redirect(url_for("expenses_page"))

    safe_name = secure_filename(file.filename)
    tmp_path = os.path.join(UPLOAD_TMP_DIR, safe_name)
    try:
        file.save(tmp_path)
        added_count, error = eu.import_csv(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if error:
        flash(error, "error")
    else:
        flash("Imported {} expense record(s) successfully.".format(added_count), "success")
    return redirect(url_for("expenses_page"))


# ------------------------------------------------------------------
# ROUTES: ANALYTICS
# ------------------------------------------------------------------

@app.route("/analytics")
def analytics_page():
    df = eu.load_expenses()
    user_data = eu.load_user_data()
    view = request.args.get("view", "monthly")
    year, month = parse_year_month(request.args)

    month_summary = eu.get_month_summary(df, year, month) if not df.empty else None
    year_summary = eu.get_year_summary(df, year) if not df.empty else None
    essential_split = eu.essential_vs_nonessential(df, user_data["category_classification"])
    insights = eu.generate_insights(df, user_data)
    suggestions = eu.generate_saving_suggestions(df)
    prediction = eu.predict_next_month(df)

    comparison = None
    c_year1 = request.args.get("c_year1")
    c_month1 = request.args.get("c_month1")
    c_year2 = request.args.get("c_year2")
    c_month2 = request.args.get("c_month2")
    if c_year1 and c_month1 and c_year2 and c_month2 and not df.empty:
        try:
            comparison = eu.compare_months(
                df, int(c_year1), int(c_month1), int(c_year2), int(c_month2)
            )
        except (ValueError, TypeError):
            flash("Please choose valid months to compare.", "error")

    return render_template(
        "analytics.html",
        view=view,
        year=year,
        month=month,
        month_summary=month_summary,
        year_summary=year_summary,
        essential_split=essential_split,
        insights=insights,
        suggestions=suggestions,
        prediction=prediction,
        comparison=comparison,
        classification_map=user_data["category_classification"],
        categories=sorted(user_data["category_classification"].keys()),
        has_data=not df.empty,
        month_names=[datetime(2000, m, 1).strftime("%B") for m in range(1, 13)],
    )


@app.route("/analytics/classify", methods=["POST"])
def classify_category_route():
    category = request.form.get("category", "")
    classification = request.form.get("classification", "")
    if classification not in ("Essential", "Non-Essential"):
        flash("Please choose a valid classification.", "error")
        return redirect(url_for("analytics_page"))

    eu.update_classification(category, classification)
    flash("'{}' classified as {}.".format(category, classification), "success")
    return redirect(url_for("analytics_page"))


# ------------------------------------------------------------------
# ERROR HANDLERS -- never leak raw tracebacks to the user
# ------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return render_template("index.html", user=eu.load_user_data()), 404


@app.errorhandler(413)
def file_too_large(_e):
    flash("The uploaded file is too large. Maximum size is 5 MB.", "error")
    return redirect(url_for("expenses_page"))


@app.errorhandler(500)
def server_error(_e):
    flash("Something went wrong while processing your request. Please try again.", "error")
    return redirect(url_for("dashboard"))


# ------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
