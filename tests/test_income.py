import unittest
from datetime import date
from income.models import Income
from income.data_handler import add_income, load_income, update_income, delete_income

class TestIncomeLifecycle(unittest.TestCase):
    def setUp(self):
        # Original income entry
        self.original_income = Income(
            date=date.today(),
            name="test_income_lifecycle",
            amount=300.00,
            description="Initial test income",
            is_fixed=True
        )

        # Updated income entry
        self.updated_income = Income(
            date=date.today(),
            name="test_income_lifecycle_updated",
            amount=500.00,
            description="Updated test income",
            is_fixed=True
        )

    def test_income_lifecycle(self):
        # Add income
        add_income(self.original_income)
        df = load_income(True)
        self.assertTrue(any(df["name"] == "test_income_lifecycle"), "Income not added.")

        # Update income
        index = df[df["name"] == "test_income_lifecycle"].index[0]
        update_income(index, self.updated_income)
        df = load_income(True)
        self.assertTrue(any(df["name"] == "test_income_lifecycle_updated"), "Income not updated.")
        self.assertEqual(df.loc[index, "amount"], 500.00)

        # Delete income
        index = df[df["name"] == "test_income_lifecycle_updated"].index[0]
        delete_income(index, True)
        df = load_income(True)
        self.assertFalse(any(df["name"] == "test_income_lifecycle_updated"), "Income not deleted.")

if __name__ == "__main__":
    unittest.main()
