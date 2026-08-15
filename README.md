# ExpenseLens AI

ExpenseLens AI is a personal expense tracking and financial insights tool built with Python, Flask, Pandas, NumPy, and Scikit-learn.

It helps users record their daily expenses, understand their spending patterns, compare monthly expenses, track savings, and estimate future spending using basic machine learning.

## Features

- Add, edit, and delete daily expenses
- Custom expense categories
- Track income, expenses, balance, and savings percentage
- Category-wise and monthly expense analysis
- Monthly and yearly spending trends
- Compare expenses between different months
- Essential vs. non-essential expense analysis
- Data-based spending insights and saving suggestions
- AI-based next-month spending estimation
- Browser dashboard with interactive charts
- Terminal interface with Matplotlib graphs
- CSV-based storage without a database

## Machine Learning

The project uses Scikit-learn to estimate next month's total spending from the user's previous monthly expense history.

Models used:

- Linear Regression
- Decision Tree Regression
- Random Forest Regression

The system also provides basic evaluation metrics and feature importance to make the prediction understandable.

## Technology Stack

- Python
- Flask
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- HTML5
- CSS3
- JavaScript
- Chart.js
- CSV and JSON

## Project Structure

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
