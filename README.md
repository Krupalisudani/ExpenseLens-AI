# ExpenseLens AI

> **Understand your expenses. Discover where your money goes. Make smarter financial decisions.**

ExpenseLens AI is a Python-based expense tracking and financial insights tool that helps users record, analyze, and understand their daily expenses.

It combines **Pandas, NumPy, and Scikit-learn** to analyze spending patterns and estimate future monthly expenses using basic machine learning.

---

## 🚀 Features

- Add, edit, and delete daily expenses
- Organize expenses by customizable categories
- Track income, expenses, balance, and savings
- View daily, monthly, and yearly spending
- Compare spending across different months
- Analyze essential vs. non-essential expenses
- View interactive spending charts and trends
- Get data-based spending insights and savings suggestions
- Predict next month's spending using Machine Learning
- Use the application through both **Web Browser and Terminal**

---

## 🤖 Machine Learning

ExpenseLens AI uses three Scikit-learn regression models:

- Linear Regression
- Decision Tree
- Random Forest

The models use the user's previous monthly spending data to estimate future spending.

The project also provides basic model evaluation and feature-importance information to make the prediction easier to understand.

> Predictions are estimates based on historical data and are not financial advice.

---

## 📊 Useful Visualizations

The application provides graphs that help users understand:

- Where their money goes
- Monthly spending trends
- Income vs. expenses
- Spending by category
- Factors influencing the ML prediction

---

## 🛠️ Tech Stack

**Programming:** Python

**Data Analysis:** Pandas, NumPy

**Machine Learning:** Scikit-learn

**Backend:** Flask

**Frontend:** HTML, CSS, JavaScript

**Visualization:** Matplotlib, Chart.js

**Storage:** CSV and JSON

---

## 📁 Project Structure

```text
ExpenseLensAI/
├── app.py
├── terminal_app.py
├── expense_utils.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
├── templates/
└── static/
