"""Test script to better understand date extraction from HTML"""
import pandas as pd
import requests
from io import StringIO
from bs4 import BeautifulSoup
import re

url = 'https://www.teamrankings.com/nba/schedules/season/'

response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
html_text = response.text

soup = BeautifulSoup(html_text, 'html.parser')

# Find the table
table = soup.find('table')
if table:
    # Find all header rows
    thead = table.find('thead')
    if thead:
        rows = thead.find_all('tr')
        print("Header rows found:", len(rows))
        for i, row in enumerate(rows):
            print(f"\nHeader row {i}:")
            cells = row.find_all(['th', 'td'])
            dates = []
            for j, cell in enumerate(cells[:20]):  # First 20 cells
                text = cell.get_text(strip=True)
                if text and not text in ['Time', 'Location']:
                    print(f"  Cell {j}: {text}")
                    # Check if it's a date
                    if re.match(r'\w+\s+\w+\s+\d+', text):
                        dates.append(text)
            if dates:
                print(f"  Dates found: {dates[:5]}")

