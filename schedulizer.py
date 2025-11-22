#   Input: regular season data csv, stadium distance data csv, team name
#   Note: Works with both the original nba_reg_szn_24-25.csv and the scraped nba_reg_szn_24-25_scraped.csv

#   Output: List of dictionaries (typically 82 games per team) with the following keys:
#    - team: team name (the team the dictionary belongs to)
#    - gameindex: 1-N (where N is the number of games found)
#    - game_datetime: datetime object of when the game is being played
#    - previous_game_datetime: datetime object of when the previous game was played
#    - opponent: opponent team name
#    - location: home vs. away
#    - where_played: the name of the team that owns the stadium the game is being played at -- NOT ARENA IN REGULAR SEASON DATASET, IGNORE ARENA COLUMN IN REGULAR SEASON DATASET, USE TEAM NAME OF THE HOME TEAM SO WE CAN MATCH WITH DISTANCE MATRIX
#    - previous_where_played: the name of the team that owned the stadium the previous game was played at (None for first game)
#    - travel_distance: the distance between where_played and previous_where_played, calculated using the distance matrix (None for first game)
#    - travel_hours: the raw number of hours betwen game_datetime and previous_game_datetime (None for first game)
#    - game_mile_hours_burden: travel_distance / travel_hours (None for first game)

# INTERNATIONAL GAMES - NEED TO HANDLE DIFFERENTLY
# "Sat, Nov 2, 2024",9:30p,Miami Heat,Washington Wizards,Mexico City Arena,
# "Thu, Jan 23, 2025",2:00p,San Antonio Spurs,Indiana Pacers,AccorHotels Arena,
# "Sat, Jan 25, 2025",12:00p,Indiana Pacers,San Antonio Spurs,AccorHotels Arena,

# mexico city arena: [19.496309°N, 99.175429°W]
# accorhotels arena: [48.8386° N, 2.3785° E]

import pandas as pd
from datetime import datetime
import re
from geopy.distance import geodesic

def schedulizer(regular_season_data, stadium_distance_data, team_name):
    """
    Schedulizer function to create a list of dictionaries (typically 82 games per team) with above keys.
    
    Args:
        regular_season_data: Path to CSV file with regular season game data (e.g., 'nba_reg_szn_24-25_scraped.csv')
        stadium_distance_data: Path to CSV file with stadium distance matrix
        team_name: Name of the team to analyze
        
    Returns:
        List of dictionaries, one for each game (typically 82 games per team)
    """
    # International arena coordinates
    INTERNATIONAL_ARENAS = {
        'Mexico City Arena': (19.496309, -99.175429),
        'AccorHotels Arena': (48.8386, 2.3785)
    }
    
    # Read the regular season data
    season_df = pd.read_csv(regular_season_data)
    
    # Read the distance matrix
    distance_df = pd.read_csv(stadium_distance_data, index_col=0)
    
    # Read stadium coordinates for NBA teams
    stadiums_df = pd.read_csv('nba_stadiums.csv')
    team_coords = dict(zip(stadiums_df['Team'], 
                          zip(stadiums_df['Lat'], stadiums_df['Long'])))
    
    # Normalize team names for coordinate lookup (handle typo)
    def normalize_team_name_for_coords(name):
        """Normalize team name to match stadiums CSV"""
        if name == "Sacramento Kings":
            return "Sacremento Kings"
        return name
    
    # Filter games where the team is either visitor or home
    team_games = season_df[
        (season_df['Visitor/Neutral'] == team_name) | 
        (season_df['Home/Neutral'] == team_name)
    ].copy()
    
    # Add a column to track if game is at international venue
    team_games['is_international'] = team_games['Arena'].isin(INTERNATIONAL_ARENAS.keys())
    
    # Parse date and time to create datetime objects
    def parse_datetime(date_str, time_str):
        """Parse date and time strings into datetime object"""
        # Parse date (format: "Tue, Oct 22, 2024")
        date_match = re.match(r'(\w+),\s+(\w+)\s+(\d+),\s+(\d+)', date_str)
        if not date_match:
            raise ValueError(f"Could not parse date: {date_str}")
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        month = month_map[date_match.group(2)]
        day = int(date_match.group(3))
        year = int(date_match.group(4))
        
        # Parse time (format: "7:30p" or "10:00p" or "12:00p")
        time_match = re.match(r'(\d+):(\d+)([ap])', time_str)
        if not time_match:
            raise ValueError(f"Could not parse time: {time_str}")
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        am_pm = time_match.group(3)
        
        # Convert to 24-hour format
        if am_pm == 'p' and hour != 12:
            hour += 12
        elif am_pm == 'a' and hour == 12:
            hour = 0
        
        # Create datetime object (assuming Eastern Time)
        return datetime(year, month, day, hour, minute)
    
    # Create datetime column
    team_games['game_datetime'] = team_games.apply(
        lambda row: parse_datetime(row['Game Date'], row['Start (ET)']), 
        axis=1
    )
    
    # Sort by datetime
    team_games = team_games.sort_values('game_datetime').reset_index(drop=True)
    
    # Note: The dataset should have 82 games per team, but we'll process whatever games are available
    if len(team_games) == 0:
        raise ValueError(f"No games found for {team_name}")
    elif len(team_games) < 82:
        print(f"Warning: {team_name} has only {len(team_games)} games (expected 82)")
    
    # Create list of dictionaries
    game_list = []
    
    for idx, row in team_games.iterrows():
        # Determine if home or away
        is_home = row['Home/Neutral'] == team_name
        location = 'home' if is_home else 'away'
        
        # Get opponent
        opponent = row['Home/Neutral'] if not is_home else row['Visitor/Neutral']
        
        # Get where_played (always the home team's name)
        where_played = row['Home/Neutral']
        
        # Get game datetime
        game_dt = row['game_datetime']
        
        # For first game, set previous values to None
        if idx == 0:
            game_dict = {
                'team': team_name,
                'gameindex': idx + 1,
                'game_datetime': game_dt,
                'previous_game_datetime': None,
                'opponent': opponent,
                'location': location,
                'where_played': where_played,
                'previous_where_played': None,
                'travel_distance': None,
                'travel_hours': None,
                'game_mile_hours_burden': None
            }
        else:
            # Get previous game info
            prev_row = team_games.iloc[idx - 1]
            prev_game_dt = prev_row['game_datetime']
            prev_where_played = prev_row['Home/Neutral']
            
            # Calculate travel hours
            time_diff = game_dt - prev_game_dt
            travel_hours = time_diff.total_seconds() / 3600.0
            
            # Calculate travel distance
            # Check if current or previous game is at international venue
            prev_is_international = prev_row['is_international']
            curr_is_international = row['is_international']
            
            def get_coordinates(team_name, arena_name, is_intl):
                """Get coordinates for a location (team or international arena)"""
                if is_intl:
                    return INTERNATIONAL_ARENAS[arena_name]
                else:
                    normalized_name = normalize_team_name_for_coords(team_name)
                    if normalized_name in team_coords:
                        return team_coords[normalized_name]
                    else:
                        raise ValueError(f"Could not find coordinates for team: {team_name}")
            
            # Calculate distance using geodesic if either game is international
            if prev_is_international or curr_is_international:
                prev_arena = prev_row['Arena']
                curr_arena = row['Arena']
                
                prev_coords = get_coordinates(prev_where_played, prev_arena, prev_is_international)
                curr_coords = get_coordinates(where_played, curr_arena, curr_is_international)
                
                # Calculate distance in miles using geodesic
                travel_distance = geodesic(prev_coords, curr_coords).miles
            else:
                # Use distance matrix for regular NBA venues
                def normalize_team_name(name):
                    """Normalize team name to match distance matrix"""
                    # Handle the typo in the distance matrix
                    if name == "Sacramento Kings":
                        return "Sacremento Kings"
                    return name
                
                prev_where_played_normalized = normalize_team_name(prev_where_played)
                where_played_normalized = normalize_team_name(where_played)
                
                try:
                    travel_distance = float(distance_df.loc[prev_where_played_normalized, where_played_normalized])
                    # If same location, distance should be 0
                    if prev_where_played == where_played:
                        travel_distance = 0.0
                except (KeyError, ValueError):
                    # If can't find or convert, set to 0 (same location or error)
                    travel_distance = 0.0
            
            # Calculate game_mile_hours_burden
            if travel_hours > 0:
                game_mile_hours_burden = travel_distance / travel_hours
            else:
                game_mile_hours_burden = None
            
            game_dict = {
                'team': team_name,
                'gameindex': idx + 1,
                'game_datetime': game_dt,
                'previous_game_datetime': prev_game_dt,
                'opponent': opponent,
                'location': location,
                'where_played': where_played,
                'previous_where_played': prev_where_played,
                'travel_distance': travel_distance,
                'travel_hours': travel_hours,
                'game_mile_hours_burden': game_mile_hours_burden
            }
        
        game_list.append(game_dict)
    
    return game_list




