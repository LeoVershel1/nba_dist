"""
Visualization script for showing cumulative burden over time.
Shows total burden (y-axis) vs game number (x-axis) for NBA teams.

The visualization allows you to 'watch' the total burden increase over time.
Sections with steeper increases represent more difficult schedules (higher
travel burden per game), while flatter sections indicate easier stretches.
"""

import matplotlib.pyplot as plt
import numpy as np
from metrics import create_schedule_mapping, get_team_schedule, get_all_teams


def calculate_cumulative_burden(schedule):
    """
    Calculate cumulative burden for each game in a team's schedule.
    
    Args:
        schedule: List of game dictionaries from schedulizer
        
    Returns:
        Tuple of (game_numbers, cumulative_burdens) as numpy arrays
    """
    if schedule is None:
        return None, None
    
    game_numbers = []
    cumulative_burdens = []
    running_total = 0.0
    
    for game in schedule:
        game_index = game['gameindex']
        burden = game['game_mile_hours_burden']
        
        # Skip first game (burden is None)
        if burden is not None:
            running_total += burden
        
        game_numbers.append(game_index)
        cumulative_burdens.append(running_total)
    
    return np.array(game_numbers), np.array(cumulative_burdens)


def plot_team_burden(team_name, schedule_mapping=None, 
                     regular_season_data='nba_reg_szn_24-25_scraped.csv',
                     stadium_distance_data='nba_stadium_distances.csv',
                     save_path=None, show_plot=True):
    """
    Plot cumulative burden over time for a single team.
    
    Args:
        team_name: Name of the team to visualize
        schedule_mapping: Optional pre-computed schedule mapping
        regular_season_data: Path to regular season CSV
        stadium_distance_data: Path to stadium distance CSV
        save_path: Optional path to save the plot (e.g., 'lakers_burden.png')
        show_plot: Whether to display the plot (default True)
    """
    # Get schedule mapping if not provided
    if schedule_mapping is None:
        print(f"Creating schedule mapping for {team_name}...")
        schedule_mapping = create_schedule_mapping(regular_season_data, stadium_distance_data)
    
    # Get team schedule
    schedule = get_team_schedule(schedule_mapping, team_name)
    
    if schedule is None:
        print(f"Error: Could not find schedule for {team_name}")
        return None
    
    # Calculate cumulative burden
    game_numbers, cumulative_burdens = calculate_cumulative_burden(schedule)
    
    if game_numbers is None:
        print(f"Error: Could not calculate burden for {team_name}")
        return None
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(game_numbers, cumulative_burdens, linewidth=2, label=team_name, color='#1f77b4')
    plt.xlabel('Game Number', fontsize=12)
    plt.ylabel('Cumulative Total Burden', fontsize=12)
    plt.title(f'Cumulative Burden Over Season: {team_name}', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    # Show the plot
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return plt.gcf()


if __name__ == "__main__":
    # Example: Visualize one team
    # You can change this to any team name
    team_name = "Los Angeles Lakers"
    
    # Create schedule mapping once (can be reused for multiple teams)
    print("Loading schedule data...")
    schedule_mapping = create_schedule_mapping()
    
    # Plot the team
    plot_team_burden(team_name, schedule_mapping=schedule_mapping, 
                     save_path='lakers_burden.png', show_plot=False)
    
    # Example: List all available teams
    print("\n" + "="*60)
    print("Available teams:")
    print("="*60)
    all_teams = get_all_teams(schedule_mapping)
    for i, team in enumerate(all_teams, 1):
        print(f"{i:2d}. {team}")

