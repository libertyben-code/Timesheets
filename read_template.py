import pandas as pd

# Read the Excel template
try:
    df = pd.read_excel('Trame timesheet.xlsx')
    print("Columns:")
    print(df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"\nData types:")
    print(df.dtypes)
except Exception as e:
    print(f"Error reading file: {e}")