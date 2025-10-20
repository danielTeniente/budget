# Personal Budget Tracker
This is a project to have a personal budget tracker that 
helps to manage income and expenses effectively.

I used csv files to store the data and Python to process it. You need to create the data folder. The files will be created automatically when you add the first income or expense.

## Features
* Add income and expenses
* View summary of budget
* Add expenses in different currencies, specifically, I wanted to add sets of expenses in EUR and have them converted to USD automatically.
* Clustering: the fixed clustering works well over non-fixed expenses, but I kept the no supervised clustering to see if there were any hidden patterns in the expenses. You need to add the fixed categories in a file called expense_topics.json in the data folder.

## Execution
To run the application, use the following command:
```
streamlit run app.py
```


