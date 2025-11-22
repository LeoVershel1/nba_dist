"""
Simple test script to inspect the HTML table structure from teamrankings.com
This will help us understand the data format before writing the parsing functions.
"""
import pandas as pd
import requests
from io import StringIO

url = 'https://www.teamrankings.com/nba/schedules/season/'

print("Fetching page...")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    print(f"Successfully fetched page ({len(response.text)} characters)\n")
    
    # Try to read tables
    # Save raw HTML for manual inspection
    with open('raw_html_output.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved raw HTML to 'raw_html_output.html' for manual inspection\n")
    
    print("Attempting to parse HTML tables...")
    # Try multiple methods
    tables = None
    for method in ['html5lib', 'lxml', None]:
        try:
            if method:
                print(f"Trying with {method} parser...")
                tables = pd.read_html(StringIO(response.text), flavor=method)
            else:
                print("Trying default parser...")
                tables = pd.read_html(StringIO(response.text))
            break
        except ImportError:
            print(f"{method} not available, trying next...")
            continue
        except Exception as e:
            print(f"Failed with {method}: {e}")
            continue
    
    if tables:
        print(f"Found {len(tables)} tables\n")
        
        # Display information about each table
        for i, table in enumerate(tables):
            print(f"=" * 80)
            print(f"TABLE {i}")
            print(f"=" * 80)
            print(f"Shape: {table.shape}")
            print(f"Columns: {list(table.columns)}")
            print(f"\nFirst few rows:")
            print(table.head(10))
            print(f"\nData types:")
            print(table.dtypes)
            print("\n")
            
            # Save to CSV for easier inspection
            filename = f"table_{i}_inspection.csv"
            table.to_csv(filename, index=False)
            print(f"Saved to {filename}\n")
    else:
        print("No tables found. Error parsing tables.")
        print("\nTrying to install lxml/html5lib might help:")
        print("  pip install lxml html5lib")
        
except ImportError:
    print("requests library not installed")
    print("Install with: pip install requests")
except Exception as e:
    print(f"Error: {e}")

