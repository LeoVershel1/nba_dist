import pandas as pd
from schedulizer import schedulizer

def create_schedule_mapping(regular_season_data='nba_reg_szn_24-25.csv', 
                           stadium_distance_data='nba_stadium_distances.csv'):
    """
    Create a schedule mapping for all NBA teams using the schedulizer function.
    
    Args:
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        
    Returns:
        Dictionary mapping team names to their schedule (list of dictionaries, typically 80 games)
    """
    # Get all team names from the regular season data
    season_df = pd.read_csv(regular_season_data)
    
    # Get unique team names from both Visitor/Neutral and Home/Neutral columns
    all_teams = set(season_df['Visitor/Neutral'].unique()) | set(season_df['Home/Neutral'].unique())
    all_teams = sorted(list(all_teams))  # Sort for consistent ordering
    
    # Create schedule mapping
    schedule_mapping = {}
    
    print(f"Creating schedule mappings for {len(all_teams)} teams...")
    
    for team in all_teams:
        try:
            schedule = schedulizer(regular_season_data, stadium_distance_data, team)
            schedule_mapping[team] = schedule
            print(f"  [OK] {team}: {len(schedule)} games")
        except Exception as e:
            print(f"  [ERROR] {team}: Error - {str(e)}")
            schedule_mapping[team] = None
    
    print(f"\nCompleted: {sum(1 for s in schedule_mapping.values() if s is not None)}/{len(all_teams)} teams processed successfully")
    
    return schedule_mapping


def get_team_schedule(schedule_mapping, team_name):
    """
    Get the schedule for a specific team.
    
    Args:
        schedule_mapping: Dictionary returned by create_schedule_mapping()
        team_name: Name of the team
        
    Returns:
        List of dictionaries representing the team's schedule (typically 80 games), or None if not found
    """
    return schedule_mapping.get(team_name)


def get_all_teams(schedule_mapping):
    """
    Get a list of all teams in the schedule mapping.
    
    Args:
        schedule_mapping: Dictionary returned by create_schedule_mapping()
        
    Returns:
        List of team names
    """
    return list(schedule_mapping.keys())


def calculate_average_burden(schedule_mapping=None, 
                            regular_season_data='nba_reg_szn_24-25_scraped.csv',
                            stadium_distance_data='nba_stadium_distances.csv'):
    """
    Calculate the average game_mile_hours_burden for each team.
    
    Args:
        schedule_mapping: Optional dictionary from create_schedule_mapping(). 
                         If None, will create one automatically.
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        
    Returns:
        Dictionary mapping team names to their average game_mile_hours_burden
    """
    # Create schedule mapping if not provided
    if schedule_mapping is None:
        print("Creating schedule mapping...")
        schedule_mapping = create_schedule_mapping(regular_season_data, stadium_distance_data)
    
    # Calculate average burden for each team
    average_burdens = {}
    
    for team, schedule in schedule_mapping.items():
        if schedule is None:
            average_burdens[team] = None
            continue
        
        # Filter out None values (first game has None burden)
        burdens = [game['game_mile_hours_burden'] 
                  for game in schedule 
                  if game['game_mile_hours_burden'] is not None]
        
        if len(burdens) > 0:
            average_burden = sum(burdens) / len(burdens)
            average_burdens[team] = average_burden
        else:
            average_burdens[team] = None
    
    return average_burdens

def calculate_total_burden(schedule_mapping=None, 
                          regular_season_data='nba_reg_szn_24-25_scraped.csv',
                          stadium_distance_data='nba_stadium_distances.csv'):
    """
    Calculate the total (sum) game_mile_hours_burden for each team.
    
    Args:
        schedule_mapping: Optional dictionary from create_schedule_mapping(). 
                         If None, will create one automatically.
        regular_season_data: Path to CSV file with regular season game data
        stadium_distance_data: Path to CSV file with stadium distance matrix
        
    Returns:
        Dictionary mapping team names to their total game_mile_hours_burden
    """
    # Create schedule mapping if not provided
    if schedule_mapping is None:
        print("Creating schedule mapping...")
        schedule_mapping = create_schedule_mapping(regular_season_data, stadium_distance_data)
    
    # Calculate total burden for each team
    total_burdens = {}
    
    for team, schedule in schedule_mapping.items():
        if schedule is None:
            total_burdens[team] = None
            continue
        
        # Filter out None values (first game has None burden)
        burdens = [game['game_mile_hours_burden'] 
                  for game in schedule 
                  if game['game_mile_hours_burden'] is not None]
        
        if len(burdens) > 0:
            total_burden = sum(burdens)
            total_burdens[team] = total_burden
        else:
            total_burdens[team] = None
    
    return total_burdens

# Example usage when run as a script
if __name__ == "__main__":
    # Create schedule mapping for all teams
    team_schedules = create_schedule_mapping('nba_reg_szn_24-25_scraped.csv')
        # Example: Calculate average burdens
    print("\n" + "="*60)
    print("Average Game Mile-Hours Burden by Team:")
    print("="*60)
    average_burdens = calculate_average_burden(team_schedules)
    
    # Sort by burden (highest first) for easier viewing
    sorted_burdens = sorted(
        [(team, burden) for team, burden in average_burdens.items() if burden is not None],
        key=lambda x: x[1],
        reverse=True
    )
    
    for team, burden in sorted_burdens:
        print(f"{team:30s}: {burden:8.2f}")

