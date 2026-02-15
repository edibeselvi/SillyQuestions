import pandas as pd

try:
    df = pd.read_excel('./model_evaluation_report.xlsx')
    print("Columns:", df.columns.tolist())
    print("First 5 rows:")
    print(df.head())
except Exception as e:
    print(f"Error reading Excel file: {e}")
