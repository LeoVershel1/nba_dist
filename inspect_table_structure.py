"""Better inspection of the table structure"""
import pandas as pd
import requests
from io import StringIO

url = 'https://www.teamrankings.com/nba/schedules/season/'

response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
tables = pd.read_html(StringIO(response.text), flavor='html5lib')

table = tables[0]

print("Table shape:", table.shape)
print("\nUnderstanding: Each row appears to be a game")
print("The multi-level columns have dates at the top level")

# Flatten the multi-level columns to understand better
table.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in table.columns.values]

print("\nFlattened first few column names:")
print(table.columns[:10].tolist())

print("\nFirst 10 rows of actual data:")
# The first column seems to have the matchup
print(table.iloc[:10, :5])

# Let's try to understand: if each row is a game, we need to figure out which date it belongs to
# The column structure suggests dates are in the column names
print("\n\nTrying to extract date from column structure...")
# The original multi-index might help us
original_table = tables[0]
print("Sample of original multi-index columns:")
for i in range(min(5, len(original_table.columns))):
    col = original_table.columns[i]
    print(f"  Column {i}: {col}")
