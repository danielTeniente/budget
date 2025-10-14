import unittest
import app
from datetime import date
from spendings.models import Spending
from spendings.data_handler import load_spendings, add_spending, update_spending, delete_spending

class TestDataHandler(unittest.TestCase):

    def setUp(self):
        # Initial test spending
        self.original_spending = Spending(date(2025, 10, 12), "test_lifecycle", 400.00, "initial", True)
        self.updated_spending = Spending(date(2025, 10, 13), "test_lifecycle_updated", 450.00, "updated", True)

    def test_spending_lifecycle(self):
        # Add spending
        add_spending(self.original_spending)
        df = load_spendings(True)
        self.assertTrue(any(df["name"] == "test_lifecycle"), "Spending not added.")

        # Update spending
        index = df[df["name"] == "test_lifecycle"].index[0]
        update_spending(index, self.updated_spending)
        df = load_spendings(True)
        self.assertTrue(any(df["name"] == "test_lifecycle_updated"), "Spending not updated.")
        self.assertEqual(df.loc[index, "amount"], 450.00)

        # Delete spending
        index = df[df["name"] == "test_lifecycle_updated"].index[0]
        delete_spending(index, True)
        df = load_spendings(True)
        self.assertFalse(any(df["name"] == "test_lifecycle_updated"), "Spending not deleted.")

if __name__ == "__main__":
    unittest.main()