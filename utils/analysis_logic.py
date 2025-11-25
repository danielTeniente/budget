import pandas as pd
from datetime import datetime

def get_available_years(df: pd.DataFrame) -> list[int]:
    """Extracts unique years from the dataframe sorted descending."""
    if df.empty or 'date' not in df.columns:
        return [datetime.now().year]
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
        
    years = sorted(df['date'].dt.year.unique(), reverse=True)
    return years if years else [datetime.now().year]

def filter_data_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Returns a copy of the dataframe filtered by the specified year."""
    if df.empty:
        return df
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
        
    return df[df['date'].dt.year == year].copy()

def get_monthly_frequent_items(df_year: pd.DataFrame, month_num: int):
    """
    Filters data by month, finds items purchased > 1 time, 
    and returns the data ready for plotting + the sorted order of items.
    
    Returns:
        tuple: (filtered_df, sorted_display_names)
    """
    if df_year.empty:
        return pd.DataFrame(), []

    # 1. Filter by specific month
    df_month = df_year[df_year['date'].dt.month == month_num].copy()
    
    if df_month.empty:
        return pd.DataFrame(), []

    # 2. Normalize names for counting
    df_month['clean_name'] = df_month['name'].astype(str).str.lower().str.strip()

    # 3. Count frequencies
    name_counts = df_month['clean_name'].value_counts()
    
    # 4. Filter: Keep only > 1
    frequent_series = name_counts[name_counts > 1]
    
    if frequent_series.empty:
        return pd.DataFrame(), []

    # 5. Get sorting order (Most frequent first)
    sorted_clean_names = frequent_series.index.tolist()
    
    # 6. Filter original rows to keep only frequent items
    result_df = df_month[df_month['clean_name'].isin(sorted_clean_names)].copy()
    
    # 7. Add Display Name column
    result_df['Display Name'] = result_df['clean_name'].str.title()
    
    # Create list of display names in the correct sorted order for the chart axis
    sorted_display_names = [name.title() for name in sorted_clean_names]
    
    # Return data and the summary table for tooltips/metrics if needed
    return result_df, sorted_display_names

def get_yearly_top_expenses(df_year: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the top 5 largest expenses for each month in the given dataframe.
    """
    if df_year.empty:
        return pd.DataFrame()

    df_calc = df_year.copy()
    df_calc['Month Name'] = df_calc['date'].dt.month_name()
    df_calc['Month Num'] = df_calc['date'].dt.month

    # Group by month and get top 5 largest amounts
    top_5_df = (
        df_calc.groupby('Month Num', group_keys=False)
        .apply(lambda x: x.nlargest(5, 'amount'))
        .sort_values(['Month Num', 'amount'], ascending=[True, True])
    )
    
    return top_5_df