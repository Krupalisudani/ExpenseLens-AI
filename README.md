# ExpenseLens AI

**Understand your spending. Make smarter financial decisions.**

ExpenseLens AI is an expense tracking + data analysis + AI-assisted
spending insight tool. It's built with Python, Flask, Pandas, NumPy,
and Scikit-learn -- no database, no generative AI, no complicated
infrastructure. Just clear code solving a real everyday problem:
most people know how much they earn, but not clearly where their
money actually goes.

---

## 1. Problem Statement

At the end of the month, most people can't easily answer:

- Where did most of my money go?
- Which category costs me the most?
- Is my spending increasing or decreasing?
- How much of my income am I actually saving?
- What might I spend next month?

ExpenseLens AI answers these questions directly from the user's own
recorded expenses using Pandas for analysis and a small regression
model for forecasting.

---

## 2. Features

- **Easy expense entry** — category, amount, date, optional description; a
  custom category field for anything outside the predefined list.
- **Edit / delete** any recorded expense.
- **CSV import** — bring in an existing expense history (validated).
- **Dashboard** — income, expenses, remaining balance, savings %, today's
  spending, average daily spending, and highest spending category.
- **Category analysis** — amount, percentage, and rank per category.
- **Monthly / yearly views** with a month-by-month spending trend.
- **Month comparison** — compare any two months and see which categories
  moved the most.
- **Essential vs. Non-Essential** spending split, fully reclassifiable.
- **Spending insights** — plain-language, data-backed observations
  (no language model involved).
- **Potential savings suggestions** — calculated from each category's
  spending vs. its own recent 3-month average.
- **AI Spending Prediction** — Linear Regression, Decision Tree, and
  Random Forest models estimate next month's spending from the user's
  own history, with feature importance and basic evaluation metrics
  (MAE, R²). Clearly labeled as an estimate, not a guarantee.
- **Two interfaces**: a full browser dashboard (Flask) and a terminal
  menu (`terminal_app.py`) that share the exact same logic and data.

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Data | Pandas, NumPy |
| Machine Learning | Scikit-learn (Linear Regression, Decision Tree, Random Forest) |
| Graphs (terminal) | Matplotlib |
| Graphs (browser) | Chart.js (via CDN) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Storage | CSV (`data/expenses.csv`) + JSON (`data/user_data.json`) — **no database** |

---

## 4. How It Works

```
Setup (name, income, savings goal)
        ↓
Add expenses (browser or terminal)
        ↓
Pandas loads & cleans data/expenses.csv
        ↓
Dashboard summarizes: income, expenses, savings, categories
        ↓
Analytics: monthly/yearly views, month comparison,
           essential vs non-essential, insights
        ↓
AI Spending Prediction (Scikit-learn regression on monthly aggregates)
        ↓
Potential savings suggestions
```

Both `app.py` (browser) and `terminal_app.py` (terminal) import all
of their logic from **`expense_utils.py`** — the single shared engine
for data storage, validation, calculations, insights, and the
prediction model. This guarantees both interfaces always agree.

---

## 5. Project Structure

```
ExpenseLensAI/
├── app.py                 Flask web application (routes only)
├── terminal_app.py        Command-line interface
├── expense_utils.py        Shared engine: storage, calculations, ML, insights
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── expenses.csv         Sample/demo expense data (auto-created if missing)
│   └── user_data.json        Name, income, savings goal, category rules
├── templates/
│   ├── index.html            Setup / landing page
│   ├── dashboard.html
│   ├── expenses.html         Add / edit / delete / import
│   ├── analytics.html        Monthly/yearly views, comparison, AI prediction
│   ├── _nav.html              Shared navigation partial
│   └── _flash.html            Shared flash-message partial
└── static/
    ├── style.css              Light, clean, financial-dashboard theme
    └── script.js
```

`expense_utils.py` is the one deliberate addition beyond the minimum
file list, added specifically so `app.py` and `terminal_app.py` never
duplicate business logic.

---

## 6. Installation

```bash
cd ExpenseLensAI
pip install -r requirements.txt
```

Requires Python 3.9+.

---

## 7. Running the Browser App

```bash
python app.py
```

Then open:

```
http://127.0.0.1:5000
```

The first run automatically creates `data/user_data.json` and a
sample `data/expenses.csv` (four months of varied, labeled demo data)
so the dashboard, charts, and AI prediction all have something
meaningful to show immediately.

---

## 8. Running the Terminal App

```bash
python terminal_app.py
```

Menu options: Add Expense, View Today's Expenses, Monthly Summary,
Category Summary, Savings, Spending Insights, AI Spending Prediction,
Show Graph (opens a Matplotlib window), Update Income, Exit.

Both modes read/write the same `data/expenses.csv` and
`data/user_data.json`, so you can switch between them freely.

---

## 9. Sample Data

`data/expenses.csv` ships with four months of **sample/demo data**
(varied categories and amounts, clearly not identical month to month)
so graphs, category analysis, month comparison, and the AI prediction
are all meaningful right after cloning. Replace it with your own data
at any time — either by adding expenses through the app, or by
importing your own CSV from the Expenses page.

---

## 10. The AI / ML Component

**What it is:** three classic Scikit-learn regression models
(Linear Regression, Decision Tree, Random Forest) trained on the
user's own monthly spending history to estimate next month's total
spending.

**Features used:** the month's position in the timeline, the
previous month's total spending, and the number of transactions that
month.

**What it is NOT:** there is no generative AI, no language model, no
neural network, and no claim of understanding natural language. It
is a small, explainable regression problem — the kind of ML any
intermediate Python/Scikit-learn student can fully explain.

**Insufficient data handling:** if fewer than 4 months of expense
history exist, the app shows *"Not enough data yet. Add at least 4
months of expense data to generate a spending estimate."* rather than
training an unreliable model.

---

## 11. Graphs

Every graph answers a specific user question rather than existing for
decoration:

| Question | Graph |
|---|---|
| Where did my money go? | Category pie/doughnut chart |
| How much did I spend each month? | Monthly spending bar chart |
| Is my spending increasing? | Monthly spending line chart |
| What influences the AI estimate? | Feature importance bar chart |
| How much of my income am I spending? | Income vs. Expense vs. Remaining |

Browser charts use Chart.js (CDN); terminal graphs use Matplotlib in
a separate, closable window.

---

## 12. Data Safety

ExpenseLens AI only stores what's needed to analyze spending: date,
category, amount, and an optional description, plus your name, income,
and savings goal. It never asks for or stores bank account numbers,
card numbers, passwords, or UPI credentials.

---

## 13. Future Improvements

- Multi-user support (would require moving beyond flat files)
- Recurring/subscription expense detection
- Budget alerts per category
- Export monthly reports as PDF
- Currency selection beyond ₹

---

## 14. Author / Project Information

ExpenseLens AI is a personal portfolio project demonstrating practical
data analysis and applied machine learning with Python, Pandas, and
Scikit-learn — built to be fully explainable in a technical interview,
not just fully functional.
