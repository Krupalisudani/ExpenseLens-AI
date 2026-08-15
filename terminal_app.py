"""
terminal_app.py -- ExpenseLens AI (Terminal Mode)
============================================================
A simple command-line interface over the same expense_utils engine
used by the Flask app. Run with:

    python terminal_app.py

Every calculation here matches the browser app exactly, because both
read from the same data/expenses.csv and data/user_data.json files
through the same functions in expense_utils.py.
============================================================
"""

from datetime import datetime

import expense_utils as eu

MENU = """
============================================================
  EXPENSELENS AI -- Terminal Mode
  "Understand your spending. Make smarter financial decisions."
============================================================
 1. Add Expense
 2. View Today's Expenses
 3. View Monthly Summary
 4. View Category Summary
 5. View Savings
 6. Show Spending Insights
 7. AI Spending Prediction
 8. Show Graph
 9. Update Income / Savings Goal
10. Exit
============================================================
"""


def prompt(label, default=None):
    suffix = " [{}]".format(default) if default is not None else ""
    value = input("{}{}: ".format(label, suffix)).strip()
    return value if value else (str(default) if default is not None else "")


def print_header(title):
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


def action_add_expense():
    print_header("Add Expense")
    print("Categories: " + ", ".join(eu.CATEGORIES))
    category = prompt("Category")
    custom_category = None
    if category == "Other":
        custom_category = prompt("Custom Category")
    amount = prompt("Amount")
    date_value = prompt("Date (YYYY-MM-DD, blank = today)")
    description = prompt("Description (optional)")

    success, message = eu.add_expense(date_value, category, amount, description, custom_category)
    print(("\n✔ " if success else "\n✘ ") + message)


def action_today_expenses():
    print_header("Today's Expenses")
    df = eu.load_expenses()
    summary = eu.get_today_summary(df)
    print("Total spent today: ₹{:,.2f} across {} transaction(s)".format(summary["total"], summary["count"]))
    for c in summary["categories"]:
        print("  {}. {:<18} ₹{:>10,.2f}  ({}%)".format(c["rank"], c["category"], c["amount"], c["percentage"]))
    if not summary["categories"]:
        print("  No expenses recorded today.")


def action_monthly_summary():
    print_header("Monthly Summary")
    today = datetime.today()
    year = int(prompt("Year", today.year))
    month = int(prompt("Month (1-12)", today.month))

    df = eu.load_expenses()
    summary = eu.get_month_summary(df, year, month)
    print("\nMonth: {}/{}".format(month, year))
    print("Total spending: ₹{:,.2f}".format(summary["total"]))
    print("Transactions: {}".format(summary["transaction_count"]))
    print("Daily average: ₹{:,.2f}".format(summary["daily_average"]))
    if summary["highest_category"]:
        print("Highest category: {} (₹{:,.2f})".format(
            summary["highest_category"]["category"], summary["highest_category"]["amount"]))
    if summary["lowest_category"]:
        print("Lowest category: {} (₹{:,.2f})".format(
            summary["lowest_category"]["category"], summary["lowest_category"]["amount"]))


def action_category_summary():
    print_header("Category Summary (This Month)")
    today = datetime.today()
    df = eu.load_expenses()
    summary = eu.get_month_summary(df, today.year, today.month)
    if not summary["categories"]:
        print("No expenses recorded this month yet.")
        return
    for c in summary["categories"]:
        print("  {}. {:<18} ₹{:>10,.2f}  ({}%)".format(c["rank"], c["category"], c["amount"], c["percentage"]))


def action_savings():
    print_header("Savings")
    today = datetime.today()
    df = eu.load_expenses()
    user_data = eu.load_user_data()
    savings = eu.get_savings_summary(df, user_data, today.year, today.month)
    print("Monthly Income:     ₹{:,.2f}".format(savings["income"]))
    print("This Month's Spend: ₹{:,.2f}".format(savings["expenses"]))
    print("Remaining Balance:  ₹{:,.2f}".format(savings["remaining"]))
    print("Savings Goal:       ₹{:,.2f}".format(savings["savings_goal"]))
    print("Savings Rate:       {}%".format(savings["savings_pct"]))
    print("Goal Status:        {}".format("On track ✔" if savings["goal_met"] else "Below goal ✘"))


def action_insights():
    print_header("Spending Insights")
    df = eu.load_expenses()
    user_data = eu.load_user_data()
    for insight in eu.generate_insights(df, user_data):
        print("  • " + insight)

    suggestions = eu.generate_saving_suggestions(df)
    if suggestions:
        print("\nPotential Savings:")
        for s in suggestions:
            print("  • " + s["message"])
    else:
        print("\nNo unusual spending detected this month.")


def action_prediction():
    print_header("AI Spending Prediction")
    df = eu.load_expenses()
    result = eu.predict_next_month(df)
    if not result["available"]:
        print(result["message"])
        return

    print("Based on {} months of history:\n".format(result["months_used"]))
    print("{:<20}{:>15}{:>12}{:>10}".format("Model", "Prediction", "MAE", "R2"))
    for r in result["model_results"]:
        r2_display = r["r2"] if r["r2"] is not None else "N/A"
        print("{:<20}{:>15,.2f}{:>12,.2f}{:>10}".format(r["model"], r["prediction"], r["mae"], r2_display))

    print("\nAverage estimate across models: ₹{:,.2f}".format(result["average_estimate"]))
    print("Best-fitting model: {} (₹{:,.2f})".format(result["best_model"], result["best_prediction"]))

    if result["feature_importance"]:
        print("\nFactors influencing the estimate:")
        for f in result["feature_importance"]:
            print("  • {} ({}%)".format(f["feature"], f["importance"]))

    print("\nNote: " + result["note"])


def action_graph():
    print_header("Show Graph")
    print("1. Category Pie Chart (This Month)")
    print("2. Monthly Spending Trend (Bar Chart)")
    print("3. Income vs Expense vs Remaining")
    choice = prompt("Choose a graph", "1")

    df = eu.load_expenses()
    today = datetime.today()

    if choice == "1":
        month_df = df[(df["date"].dt.year == today.year) & (df["date"].dt.month == today.month)]
        eu.plot_category_pie(month_df, title="Spending by Category ({})".format(today.strftime("%B %Y")))
    elif choice == "2":
        year = int(prompt("Year", today.year))
        eu.plot_monthly_trend(df, year)
    elif choice == "3":
        user_data = eu.load_user_data()
        eu.plot_income_vs_expense(df, user_data, today.year, today.month)
    else:
        print("Invalid choice.")


def action_update_income():
    print_header("Update Income / Savings Goal")
    user_data = eu.load_user_data()
    print("Previous income:       ₹{:,.2f}".format(float(user_data.get("monthly_income", 0))))
    print("Previous savings goal: ₹{:,.2f}".format(float(user_data.get("savings_goal", 0))))

    income_raw = prompt("New Monthly Income", user_data.get("monthly_income"))
    goal_raw = prompt("New Savings Goal", user_data.get("savings_goal"))

    income, income_error = eu.validate_amount(income_raw)
    if income_error:
        print("✘ " + income_error)
        return
    goal, goal_error = eu.validate_amount(goal_raw)
    if goal_error:
        print("✘ " + goal_error)
        return

    eu.update_income(income, goal)
    print("✔ Income and savings goal updated. New income: ₹{:,.2f}".format(income))


def main():
    eu.ensure_data_files()
    print(MENU)
    while True:
        choice = input("Select an option (1-10): ").strip()

        try:
            if choice == "1":
                action_add_expense()
            elif choice == "2":
                action_today_expenses()
            elif choice == "3":
                action_monthly_summary()
            elif choice == "4":
                action_category_summary()
            elif choice == "5":
                action_savings()
            elif choice == "6":
                action_insights()
            elif choice == "7":
                action_prediction()
            elif choice == "8":
                action_graph()
            elif choice == "9":
                action_update_income()
            elif choice == "10":
                print("\nThank you for using ExpenseLens AI. Goodbye!")
                break
            else:
                print("Invalid option. Please choose a number from 1 to 10.")
        except KeyboardInterrupt:
            print("\n\nExiting ExpenseLens AI. Goodbye!")
            break
        except Exception as exc:
            print("\n✘ Something went wrong: {}".format(str(exc)[:150]))

        print(MENU)


if __name__ == "__main__":
    main()
