import pandas as pd
from metrics import create_schedule_mapping, calculate_total_burden
from analysis import create_BTY_dataframe


def calculate_total_distance(schedule_mapping=None, 
                            regular_season_data='nba_reg_szn_24-25_scraped.csv',
                            stadium_distance_data='nba_stadium_distances.csv'):
    """
    Calculate the total distance traveled for each team.
    
    Args:
        schedule_mapping: Optional dictionary from create_schedule_mapping(). 
                         If None, will create one automatically.
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        
    Returns:
        Dictionary mapping team names to their total distance traveled
    """
    # Create schedule mapping if not provided
    if schedule_mapping is None:
        print("Creating schedule mapping...")
        schedule_mapping = create_schedule_mapping(regular_season_data, stadium_distance_data)
    
    # Calculate total distance for each team
    total_distances = {}
    
    for team, schedule in schedule_mapping.items():
        if schedule is None:
            total_distances[team] = None
            continue
        
        # Filter out None values (first game has None travel_distance)
        distances = [game['travel_distance'] 
                    for game in schedule 
                    if game['travel_distance'] is not None]
        
        if len(distances) > 0:
            total_distance = sum(distances)
            total_distances[team] = total_distance
        else:
            total_distances[team] = None
    
    return total_distances


def normalize_team_name(name):
    """
    Normalize team name to match distance matrix format.
    Handles the typo in the distance matrix (Sacramento vs Sacremento).
    """
    if name == "Sacramento Kings":
        return "Sacremento Kings"
    return name


def calculate_normalized_total_distance(schedule_mapping=None,
                                       regular_season_data='nba_reg_szn_24-25_scraped.csv',
                                       stadium_distance_data='nba_stadium_distances.csv',
                                       bty_dataframe=None):
    """
    Calculate the normalized total distance traveled for each team.
    Normalization is done by dividing total distance by average_yearly_road_trip.
    
    Args:
        schedule_mapping: Optional dictionary from create_schedule_mapping(). 
                         If None, will create one automatically.
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        bty_dataframe: Optional DataFrame from create_BTY_dataframe(). 
                      If None, will create one automatically.
        
    Returns:
        Dictionary mapping team names to their normalized total distance
    """
    # Get total distances
    total_distances = calculate_total_distance(schedule_mapping, regular_season_data, stadium_distance_data)
    
    # Get BTY data if not provided
    if bty_dataframe is None:
        bty_dataframe = create_BTY_dataframe(stadium_distance_data)
    
    # Create a mapping from team name to average_yearly_road_trip
    # Handle team name normalization
    avg_road_trip_map = {}
    for _, row in bty_dataframe.iterrows():
        team_name = row['team']
        avg_road_trip = row['average_yearly_road_trip']
        # Store both normalized and original name
        normalized_name = normalize_team_name(team_name)
        avg_road_trip_map[team_name] = avg_road_trip
        avg_road_trip_map[normalized_name] = avg_road_trip
    
    # Calculate normalized distances
    normalized_distances = {}
    
    for team, total_distance in total_distances.items():
        if total_distance is None:
            normalized_distances[team] = None
            continue
        
        # Try to find average yearly road trip for this team
        # First try the team name as-is, then try normalized version
        avg_road_trip = avg_road_trip_map.get(team)
        if avg_road_trip is None:
            normalized_team = normalize_team_name(team)
            avg_road_trip = avg_road_trip_map.get(normalized_team)
        
        if avg_road_trip is not None and avg_road_trip > 0:
            normalized_distance = total_distance / avg_road_trip
            normalized_distances[team] = normalized_distance
        else:
            normalized_distances[team] = None
    
    return normalized_distances


def calculate_normalized_total_burden(schedule_mapping=None,
                                     regular_season_data='nba_reg_szn_24-25_scraped.csv',
                                     stadium_distance_data='nba_stadium_distances.csv',
                                     bty_dataframe=None):
    """
    Calculate the normalized total mile-hours burden for each team.
    Normalization is done by dividing total burden by average_yearly_road_trip.
    
    Args:
        schedule_mapping: Optional dictionary from create_schedule_mapping(). 
                         If None, will create one automatically.
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        bty_dataframe: Optional DataFrame from create_BTY_dataframe(). 
                      If None, will create one automatically.
        
    Returns:
        Dictionary mapping team names to their normalized total mile-hours burden
    """
    # Get total burdens
    total_burdens = calculate_total_burden(schedule_mapping, regular_season_data, stadium_distance_data)
    
    # Get BTY data if not provided
    if bty_dataframe is None:
        bty_dataframe = create_BTY_dataframe(stadium_distance_data)
    
    # Create a mapping from team name to average_yearly_road_trip
    # Handle team name normalization
    avg_road_trip_map = {}
    for _, row in bty_dataframe.iterrows():
        team_name = row['team']
        avg_road_trip = row['average_yearly_road_trip']
        # Store both normalized and original name
        normalized_name = normalize_team_name(team_name)
        avg_road_trip_map[team_name] = avg_road_trip
        avg_road_trip_map[normalized_name] = avg_road_trip
    
    # Calculate normalized burdens
    normalized_burdens = {}
    
    for team, total_burden in total_burdens.items():
        if total_burden is None:
            normalized_burdens[team] = None
            continue
        
        # Try to find average yearly road trip for this team
        # First try the team name as-is, then try normalized version
        avg_road_trip = avg_road_trip_map.get(team)
        if avg_road_trip is None:
            normalized_team = normalize_team_name(team)
            avg_road_trip = avg_road_trip_map.get(normalized_team)
        
        if avg_road_trip is not None and avg_road_trip > 0:
            normalized_burden = total_burden / avg_road_trip
            normalized_burdens[team] = normalized_burden
        else:
            normalized_burdens[team] = None
    
    return normalized_burdens


# Example usage when run as a script
if __name__ == "__main__":
    # Create schedule mapping for all teams
    team_schedules = create_schedule_mapping('nba_reg_szn_24-25_scraped.csv')
    
    # Get BTY data
    bty_data = create_BTY_dataframe("nba_stadium_distances.csv")
    
    # Calculate normalized total distances
    print("\n" + "="*60)
    print("Normalized Total Distance by Team:")
    print("(Total Distance / Average Yearly Road Trip)")
    print("="*60)
    normalized_distances = calculate_normalized_total_distance(
        schedule_mapping=team_schedules, 
        bty_dataframe=bty_data
    )
    
    # Sort by normalized distance (highest first) for easier viewing
    sorted_distances = sorted(
        [(team, dist) for team, dist in normalized_distances.items() if dist is not None],
        key=lambda x: x[1],
        reverse=True
    )
    
    for team, dist in sorted_distances:
        print(f"{team:30s}: {dist:8.4f}")
    
    # Calculate normalized total burdens
    print("\n" + "="*60)
    print("Normalized Total Mile-Hours Burden by Team:")
    print("(Total Burden / Average Yearly Road Trip)")
    print("="*60)
    normalized_burdens = calculate_normalized_total_burden(
        schedule_mapping=team_schedules, 
        bty_dataframe=bty_data
    )
    
    # Sort by normalized burden (highest first) for easier viewing
    sorted_burdens = sorted(
        [(team, burden) for team, burden in normalized_burdens.items() if burden is not None],
        key=lambda x: x[1],
        reverse=True
    )
    
    for team, burden in sorted_burdens:
        print(f"{team:30s}: {burden:8.4f}")

