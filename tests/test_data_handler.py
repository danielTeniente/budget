import unittest
from datetime import date, datetime
from expenses.models import Expenses
from expenses.data_handler import load_expenses, add_expenses, update_expenses, delete_expenses, load_expenses_by_month
from unittest.mock import patch, MagicMock
import pandas as pd

class TestDataHandler(unittest.TestCase):

    def setUp(self):
        # Initial test expenses
        self.original_expenses = Expenses(date(2025, 10, 12), "test_lifecycle", 400.00, "initial", True)
        self.updated_expenses = Expenses(date(2025, 10, 13), "test_lifecycle_updated", 450.00, "updated", True)

    def test_expenses_lifecycle(self):
        # Add expenses
        add_expenses(self.original_expenses)
        df = load_expenses(True)
        self.assertTrue(any(df["name"] == "test_lifecycle"), "expenses not added.")

        # Update expenses
        index = df[df["name"] == "test_lifecycle"].index[0]
        update_expenses(index, self.updated_expenses)
        df = load_expenses(True)
        self.assertTrue(any(df["name"] == "test_lifecycle_updated"), "expenses not updated.")
        self.assertEqual(df.loc[index, "amount"], 450.00)

        # Delete expenses
        index = df[df["name"] == "test_lifecycle_updated"].index[0]
        delete_expenses(index, True)
        df = load_expenses(True)
        self.assertFalse(any(df["name"] == "test_lifecycle_updated"), "expenses not deleted.")

class TestLoadexpensesByMonth(unittest.TestCase):

    @patch("expenses.data_handler.pd.read_csv")
    def test_filter_by_month_and_year(self, mock_read_csv):
        # Create mock data
        data = {
            "date": pd.to_datetime(["2025-10-01", "2025-10-15", "2025-09-30", "2024-10-01"]),
            "name": ["Rent", "Groceries", "Utilities", "Subscription"],
            "amount": [1000, 150, 200, 50],
            "description": ["Monthly rent", "Weekly groceries", "Electric bill", "Streaming"]
        }
        df = pd.DataFrame(data)
        mock_read_csv.return_value = df

        # Filter for October 2025
        result = load_expenses_by_month(is_fixed=True, date_filter=datetime(2025, 10, 1))

        # Should return only the two entries from October 2025
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result["date"].dt.month == 10))
        self.assertTrue(all(result["date"].dt.year == 2025))

    @patch("expenses.data_handler.pd.read_csv", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_read_csv):
        result = load_expenses_by_month(is_fixed=False, date_filter=datetime(2025, 10, 1))
        self.assertTrue(result.empty)
        self.assertListEqual(list(result.columns), ["date", "name", "amount", "description"])

if __name__ == "__main__":
    unittest.main()

