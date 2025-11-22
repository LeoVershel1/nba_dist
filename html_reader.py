import pandas as pd
import re
from datetime import datetime
import requests
from io import StringIO
from bs4 import BeautifulSoup

def create_stadium_to_team_mapping(csv_file='nba_reg_szn_24-25.csv'):
    """
    Create a dictionary mapping stadium/arena names to home team names.
    
    Args:
        csv_file: Path to the CSV file with game data
        
    Returns:
        Dictionary mapping arena names to team names
    """
    df = pd.read_csv(csv_file)
    
    # Create mapping: for each unique arena, get the most common home team
    stadium_mapping = {}
    
    # Group by arena and get the most common home team for each
    for arena in df['Arena'].unique():
        if pd.isna(arena) or arena == '':
            continue
        
        # Get all home teams for this arena
        arena_games = df[df['Arena'] == arena]
        home_teams = arena_games['Home/Neutral'].value_counts()
        
        if len(home_teams) > 0:
            # Use the most common home team for this arena
            most_common_team = home_teams.index[0]
            stadium_mapping[arena] = most_common_team
    
    return stadium_mapping


def scrape_teamrankings_schedule():
    """
    Scrape NBA schedule data from teamrankings.com
    
    Returns:
        Tuple of (list of DataFrames, raw HTML text)
    """
    url = 'https://www.teamrankings.com/nba/schedules/season/'
    
    # Try using requests first to get HTML, then parse
    try:
        print("Fetching page with requests...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html_text = response.text
        
        # Try different HTML parsers
        parsers = ['html5lib', 'lxml', 'bs4']
        
        for parser in parsers:
            try:
                print(f"Trying parser: {parser}...")
                # Read HTML tables from the response
                tables = pd.read_html(StringIO(html_text), flavor=parser)
                print(f"Found {len(tables)} tables on the page")
                return tables, html_text
            except ImportError:
                print(f"Parser {parser} not available, trying next...")
                continue
            except Exception as e:
                print(f"Error with parser {parser}: {e}")
                continue
        
        # Fallback: try without specifying flavor
        try:
            print("Trying default parser...")
            tables = pd.read_html(StringIO(html_text))
            print(f"Found {len(tables)} tables on the page")
            return tables, html_text
        except Exception as e:
            print(f"Default parser failed: {e}")
            
    except ImportError:
        print("requests library not available. Install with: pip install requests")
    except Exception as e:
        print(f"Error fetching page: {e}")
    
    # Try direct URL access
    try:
        print("Trying direct URL access with pd.read_html...")
        tables = pd.read_html(url)
        print(f"Found {len(tables)} tables on the page")
        return tables, None
    except Exception as e:
        print(f"Direct access failed: {e}")
    
    print("\nAll methods failed. Please install required packages:")
    print("  pip install lxml html5lib beautifulsoup4 requests")
    return [], None


def parse_matchup(matchup_str):
    """
    Parse matchup string like "Houston @ Okla City" into visitor and home teams.
    
    Args:
        matchup_str: String like "Houston @ Okla City" or "Golden State @ LA Lakers"
        
    Returns:
        Tuple of (visitor_team, home_team)
    """
    if ' @ ' not in matchup_str:
        raise ValueError(f"Invalid matchup format: {matchup_str}")
    
    parts = matchup_str.split(' @ ')
    visitor_short = parts[0].strip()
    home_short = parts[1].strip()
    
    # Use the comprehensive matching function
    visitor = match_team_abbreviation(visitor_short)
    home = match_team_abbreviation(home_short)
    
    return visitor, home


def parse_date_header(date_text):
    """
    Parse date text like "Tue Oct 21" into format "Tue, Oct 21, 2024"
    
    Args:
        date_text: Date string like "Tue Oct 21" or "Wed Oct 22"
        
    Returns:
        Formatted date string like "Tue, Oct 21, 2024"
    """
    date_match = re.match(r'(\w+)\s+(\w+)\s+(\d+)', date_text.strip())
    if date_match:
        day_name, month_name, day = date_match.groups()
        # Infer year: Oct-Dec 2024, Jan-Apr 2025
        month_num = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}.get(month_name, 1)
        year = 2024 if month_num >= 10 else 2025
        return f"{day_name}, {month_name} {day}, {year}"
    return None


def extract_games_with_dates_from_html(html_text):
    """
    Extract games with their associated dates from HTML table.
    The structure is: date header, then multiple game rows under it.
    
    Args:
        html_text: Raw HTML text
        
    Returns:
        List of dictionaries, each with 'date', 'matchup', 'time', 'location'
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    games = []
    current_date = None
    
    # Find the main table
    table = soup.find('table')
    if not table:
        return games
    
    # Find all rows in the table
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all(['th', 'td'])
        if not cells:
            continue
        
        # Get text from all cells
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        first_cell_text = cell_texts[0] if cell_texts else ""
        
        # Check if this row is a date header
        # Date headers might be in the first cell or span multiple cells
        # Look for date pattern in any cell
        date_found = False
        for text in cell_texts:
            date_match = re.match(r'(\w+)\s+(\w+)\s+(\d+)', text)
            if date_match:
                # This is a date header row
                current_date = parse_date_header(text)
                if current_date:
                    print(f"Found date header: {current_date}")
                    date_found = True
                    break
        
        if date_found:
            continue
        
        # Check if this row contains game data
        # Game rows should have: matchup (with @), time, location
        # Skip if we don't have a current date yet
        if not current_date:
            continue
        
        # Try to find matchup, time, and location in the cells
        matchup = ""
        time = ""
        location = ""
        
        # Look for matchup (contains @)
        for text in cell_texts:
            if ' @ ' in text and text not in ['Time', 'Location']:
                matchup = text
                break
        
        # If we found a matchup, try to find time and location
        if matchup:
            # Time is usually in a cell with : and AM/PM
            for text in cell_texts:
                if ':' in text and ('AM' in text.upper() or 'PM' in text.upper()):
                    time = text
                    break
            
            # Location is usually a stadium name (contains Arena, Center, Garden, etc.)
            for text in cell_texts:
                if (text and text != matchup and text != time and 
                    text not in ['Time', 'Location'] and
                    any(word in text for word in ['Arena', 'Center', 'Garden', 'Forum', 'Dome', 'Stadium', 'Fieldhouse', 'Pavilion'])):
                    location = text
                    break
            
            # If we still don't have location, try the last non-empty cell that's not matchup or time
            if not location:
                for text in reversed(cell_texts):
                    if text and text != matchup and text != time and text not in ['Time', 'Location']:
                        location = text
                        break
            
            games.append({
                'date': current_date,
                'matchup': matchup,
                'time': time,
                'location': location
            })
    
    return games


def convert_time_format(time_str):
    """
    Convert time from "7:30 PM" format to "7:30p" format expected by schedulizer.
    
    Args:
        time_str: Time string like "7:30 PM" or "10:00 PM"
        
    Returns:
        Time string in format "7:30p" or "10:00p"
    """
    # Remove extra spaces and convert to lowercase
    time_str = time_str.strip().upper()
    
    # Parse time
    time_match = re.match(r'(\d+):(\d+)\s*(AM|PM)', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = time_match.group(2)
        am_pm = time_match.group(3)
        
        # Convert to lowercase and remove space
        return f"{hour}:{minute}{am_pm.lower()[0]}"
    
    return time_str


def match_team_abbreviation(abbrev):
    """
    Match team abbreviations/short names to full team names.
    Handles various formats and abbreviations.
    """
    # Comprehensive team name mapping
    team_map = {
        # Full names and common variations
        'Oklahoma City Thunder': 'Oklahoma City Thunder',
        'Okla City': 'Oklahoma City Thunder',
        'Oklahoma City': 'Oklahoma City Thunder',
        'OKC': 'Oklahoma City Thunder',
        
        'Los Angeles Lakers': 'Los Angeles Lakers',
        'LA Lakers': 'Los Angeles Lakers',
        'Lakers': 'Los Angeles Lakers',
        'L.A. Lakers': 'Los Angeles Lakers',
        
        'Los Angeles Clippers': 'Los Angeles Clippers',
        'LA Clippers': 'Los Angeles Clippers',
        'Clippers': 'Los Angeles Clippers',
        'L.A. Clippers': 'Los Angeles Clippers',
        
        'Golden State Warriors': 'Golden State Warriors',
        'Golden State': 'Golden State Warriors',
        'Warriors': 'Golden State Warriors',
        'GSW': 'Golden State Warriors',
        
        'New York Knicks': 'New York Knicks',
        'New York': 'New York Knicks',
        'Knicks': 'New York Knicks',
        'NY Knicks': 'New York Knicks',
        
        'Brooklyn Nets': 'Brooklyn Nets',
        'Brooklyn': 'Brooklyn Nets',
        'Nets': 'Brooklyn Nets',
        
        'Houston Rockets': 'Houston Rockets',
        'Houston': 'Houston Rockets',
        'Rockets': 'Houston Rockets',
        
        'Cleveland Cavaliers': 'Cleveland Cavaliers',
        'Cleveland': 'Cleveland Cavaliers',
        'Cavaliers': 'Cleveland Cavaliers',
        'Cavs': 'Cleveland Cavaliers',
        
        'Charlotte Hornets': 'Charlotte Hornets',
        'Charlotte': 'Charlotte Hornets',
        'Hornets': 'Charlotte Hornets',
        
        'Miami Heat': 'Miami Heat',
        'Miami': 'Miami Heat',
        'Heat': 'Miami Heat',
        
        'Orlando Magic': 'Orlando Magic',
        'Orlando': 'Orlando Magic',
        'Magic': 'Orlando Magic',
        
        'Toronto Raptors': 'Toronto Raptors',
        'Toronto': 'Toronto Raptors',
        'Raptors': 'Toronto Raptors',
        
        'Atlanta Hawks': 'Atlanta Hawks',
        'Atlanta': 'Atlanta Hawks',
        'Hawks': 'Atlanta Hawks',
        
        'Philadelphia 76ers': 'Philadelphia 76ers',
        'Philadelphia': 'Philadelphia 76ers',
        '76ers': 'Philadelphia 76ers',
        'Philly': 'Philadelphia 76ers',
        
        'Boston Celtics': 'Boston Celtics',
        'Boston': 'Boston Celtics',
        'Celtics': 'Boston Celtics',
        
        'Detroit Pistons': 'Detroit Pistons',
        'Detroit': 'Detroit Pistons',
        'Pistons': 'Detroit Pistons',
        
        'Chicago Bulls': 'Chicago Bulls',
        'Chicago': 'Chicago Bulls',
        'Bulls': 'Chicago Bulls',
        
        'New Orleans Pelicans': 'New Orleans Pelicans',
        'New Orleans': 'New Orleans Pelicans',
        'Pelicans': 'New Orleans Pelicans',
        'NOLA': 'New Orleans Pelicans',
        
        'Memphis Grizzlies': 'Memphis Grizzlies',
        'Memphis': 'Memphis Grizzlies',
        'Grizzlies': 'Memphis Grizzlies',
        
        'Washington Wizards': 'Washington Wizards',
        'Washington': 'Washington Wizards',
        'Wizards': 'Washington Wizards',
        'Wiz': 'Washington Wizards',
        
        'Milwaukee Bucks': 'Milwaukee Bucks',
        'Milwaukee': 'Milwaukee Bucks',
        'Bucks': 'Milwaukee Bucks',
        
        'Dallas Mavericks': 'Dallas Mavericks',
        'Dallas': 'Dallas Mavericks',
        'Mavericks': 'Dallas Mavericks',
        'Mavs': 'Dallas Mavericks',
        
        'Denver Nuggets': 'Denver Nuggets',
        'Denver': 'Denver Nuggets',
        'Nuggets': 'Denver Nuggets',
        
        'Phoenix Suns': 'Phoenix Suns',
        'Phoenix': 'Phoenix Suns',
        'Suns': 'Phoenix Suns',
        
        'Portland Trail Blazers': 'Portland Trail Blazers',
        'Portland': 'Portland Trail Blazers',
        'Trail Blazers': 'Portland Trail Blazers',
        'Blazers': 'Portland Trail Blazers',
        
        'Sacramento Kings': 'Sacramento Kings',
        'Sacramento': 'Sacramento Kings',
        'Kings': 'Sacramento Kings',
        
        'San Antonio Spurs': 'San Antonio Spurs',
        'San Antonio': 'San Antonio Spurs',
        'Spurs': 'San Antonio Spurs',
        
        'Utah Jazz': 'Utah Jazz',
        'Utah': 'Utah Jazz',
        'Jazz': 'Utah Jazz',
        
        'Minnesota Timberwolves': 'Minnesota Timberwolves',
        'Minnesota': 'Minnesota Timberwolves',
        'Timberwolves': 'Minnesota Timberwolves',
        'Wolves': 'Minnesota Timberwolves',
        
        'Indiana Pacers': 'Indiana Pacers',
        'Indiana': 'Indiana Pacers',
        'Pacers': 'Indiana Pacers',
    }
    
    # Try exact match first
    if abbrev in team_map:
        return team_map[abbrev]
    
    # Try case-insensitive match
    for key, value in team_map.items():
        if key.lower() == abbrev.lower():
            return value
    
    # Try partial match
    abbrev_lower = abbrev.lower()
    for key, value in team_map.items():
        if abbrev_lower in key.lower() or key.lower() in abbrev_lower:
            return value
    
    # If no match, return as-is (might be full name already)
    return abbrev


def process_teamrankings_data(tables, stadium_mapping, html_text=None):
    """
    Process scraped data and convert it to the format expected by schedulizer.
    Uses HTML parsing to correctly associate dates with games.
    The table structure: date header rows, then game rows (matchup, time, location) under each date.
    
    Args:
        tables: List of DataFrames from pd.read_html (may not be used if HTML parsing works)
        stadium_mapping: Dictionary mapping arena names to team names
        html_text: Raw HTML text to extract dates and games
        
    Returns:
        DataFrame in the same format as nba_reg_szn_24-25.csv
    """
    all_games = []
    
    # Use HTML parsing to extract games with their dates
    if html_text:
        print("Extracting games with dates from HTML structure...")
        games_data = extract_games_with_dates_from_html(html_text)
        print(f"Found {len(games_data)} games with dates")
        
        for game_data in games_data:
            matchup = game_data['matchup']
            time_raw = game_data['time']
            location = game_data['location']
            game_date = game_data['date']
            
            # Skip if no valid matchup
            if not matchup or ' @ ' not in matchup:
                continue
            
            # Skip header rows
            if matchup in ['Time', 'Location'] or time_raw in ['Time', 'Location']:
                continue
            
            # Parse matchup to get visitor and home teams
            try:
                visitor, home = parse_matchup(matchup)
            except Exception as e:
                print(f"Warning: Could not parse matchup '{matchup}': {e}")
                continue
            
            # Map stadium to home team (this is critical - stadium tells us the home team)
            if location:
                # Try exact match first
                if location in stadium_mapping:
                    home = stadium_mapping[location]
                else:
                    # Try partial/fuzzy match
                    location_lower = location.lower()
                    for stadium, team in stadium_mapping.items():
                        stadium_lower = stadium.lower()
                        if (location_lower == stadium_lower or 
                            location_lower in stadium_lower or 
                            stadium_lower in location_lower):
                            home = team
                            break
            
            # Convert time format from "7:30 PM" to "7:30p"
            if time_raw and ':' in time_raw:
                time = convert_time_format(time_raw)
            else:
                time = "7:00p"  # Default if time not found
            
            game = {
                'Game Date': game_date,
                'Start (ET)': time,
                'Visitor/Neutral': visitor,
                'Home/Neutral': home,
                'Arena': location,
                'Notes': ''
            }
            
            all_games.append(game)
    else:
        # Fallback to table parsing if HTML not available
        print("Warning: No HTML text provided, using table parsing (dates may be incorrect)")
        if not tables or len(tables) == 0:
            return pd.DataFrame()
        
        table = tables[0]
        for idx, row in table.iterrows():
            if len(row) < 3:
                continue
            
            matchup = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            time_raw = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            location = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            
            if not matchup or ' @ ' not in matchup:
                continue
            
            if matchup in ['Time', 'Location']:
                continue
            
            try:
                visitor, home = parse_matchup(matchup)
            except Exception as e:
                print(f"Warning: Could not parse matchup '{matchup}': {e}")
                continue
            
            if location and location in stadium_mapping:
                home = stadium_mapping[location]
            
            time = convert_time_format(time_raw) if time_raw and ':' in time_raw else "7:00p"
            
            game = {
                'Game Date': "Mon, Jan 1, 2025",  # Placeholder
                'Start (ET)': time,
                'Visitor/Neutral': visitor,
                'Home/Neutral': home,
                'Arena': location,
                'Notes': ''
            }
            
            all_games.append(game)
    
    result_df = pd.DataFrame(all_games)
    print(f"Processed {len(result_df)} games")
    
    # Remove duplicates if any
    result_df = result_df.drop_duplicates(subset=['Game Date', 'Visitor/Neutral', 'Home/Neutral'])
    print(f"After removing duplicates: {len(result_df)} games")
    
    return result_df


def save_schedule_to_csv(processed_data, output_file='nba_reg_szn_24-25_scraped.csv'):
    """
    Save the processed schedule data to a CSV file.
    
    Args:
        processed_data: DataFrame from process_teamrankings_data
        output_file: Path to output CSV file
    """
    if processed_data is not None and len(processed_data) > 0:
        processed_data.to_csv(output_file, index=False)
        print(f"Saved schedule to {output_file}")
        return output_file
    else:
        print("No data to save")
        return None


def create_complete_schedule():
    """
    Main function to create a complete schedule dataset from teamrankings.com
    """
    print("Step 1: Creating stadium-to-team mapping...")
    stadium_mapping = create_stadium_to_team_mapping()
    print(f"Created mapping for {len(stadium_mapping)} stadiums")
    print(f"Sample mappings: {dict(list(stadium_mapping.items())[:5])}")
    
    print("\nStep 2: Scraping data from teamrankings.com...")
    tables, html_text = scrape_teamrankings_schedule()
    
    if not tables:
        print("No tables found. Please check the URL or website structure.")
        return None
    
    print("\nStep 3: Processing scraped data...")
    processed_data = process_teamrankings_data(tables, stadium_mapping, html_text)
    
    if processed_data is not None and len(processed_data) > 0:
        print("\nStep 4: Saving to CSV...")
        output_file = save_schedule_to_csv(processed_data)
        return processed_data, stadium_mapping, output_file
    
    return processed_data, stadium_mapping, None


if __name__ == "__main__":
    # Test the functions
    result = create_complete_schedule()
    
    if result is not None:
        schedule_data, mapping, output_file = result
        if schedule_data is not None and len(schedule_data) > 0:
            print(f"\nSuccessfully processed {len(schedule_data)} games")
            print("\nFirst 5 games:")
            print(schedule_data.head())
            if output_file:
                print(f"\nData saved to: {output_file}")
                print("You can now use this file with the schedulizer function!")
        else:
            print("\nNo games processed. Check the data structure.")
    else:
        print("\nFailed to scrape data. Please check dependencies and try again.")
