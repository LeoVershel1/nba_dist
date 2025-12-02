"""
Streamlit app for visualizing NBA team cumulative burden over time.
Allows users to select teams from sidebar organized by division and compare their burden curves.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from metrics import create_schedule_mapping, get_team_schedule, get_all_teams
from visualize_burden import calculate_cumulative_burden, calculate_cumulative_burden_with_metadata

# Configure page
st.set_page_config(
    page_title="NBA Team Burden Visualization",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NBA Divisions (2024-2025 season)
NBA_DIVISIONS = {
    "Atlantic": [
        "Boston Celtics",
        "Brooklyn Nets",
        "New York Knicks",
        "Philadelphia 76ers",
        "Toronto Raptors"
    ],
    "Central": [
        "Chicago Bulls",
        "Cleveland Cavaliers",
        "Detroit Pistons",
        "Indiana Pacers",
        "Milwaukee Bucks"
    ],
    "Southeast": [
        "Atlanta Hawks",
        "Charlotte Hornets",
        "Miami Heat",
        "Orlando Magic",
        "Washington Wizards"
    ],
    "Northwest": [
        "Denver Nuggets",
        "Minnesota Timberwolves",
        "Oklahoma City Thunder",
        "Portland Trail Blazers",
        "Utah Jazz"
    ],
    "Pacific": [
        "Golden State Warriors",
        "Los Angeles Clippers",
        "Los Angeles Lakers",
        "Phoenix Suns",
        "Sacramento Kings"
    ],
    "Southwest": [
        "Dallas Mavericks",
        "Houston Rockets",
        "Memphis Grizzlies",
        "New Orleans Pelicans",
        "San Antonio Spurs"
    ]
}

# NBA Team Primary Colors (hex codes)
TEAM_COLORS = {
    "Atlanta Hawks": "#E03A3E",
    "Boston Celtics": "#007A33",
    "Brooklyn Nets": "#000000",
    "Charlotte Hornets": "#1D1160",
    "Chicago Bulls": "#CE1141",
    "Cleveland Cavaliers": "#860038",
    "Dallas Mavericks": "#00538C",
    "Denver Nuggets": "#0E2240",
    "Detroit Pistons": "#C8102E",
    "Golden State Warriors": "#1D428A",
    "Houston Rockets": "#CE1141",
    "Indiana Pacers": "#002D62",
    "Los Angeles Clippers": "#C8102E",
    "Los Angeles Lakers": "#552583",
    "Memphis Grizzlies": "#5D76A9",
    "Miami Heat": "#98002E",
    "Milwaukee Bucks": "#00471B",
    "Minnesota Timberwolves": "#0C2340",
    "New Orleans Pelicans": "#0C2340",
    "New York Knicks": "#006BB6",
    "Oklahoma City Thunder": "#007AC1",
    "Orlando Magic": "#0077C0",
    "Philadelphia 76ers": "#006BB6",
    "Phoenix Suns": "#1D1160",
    "Portland Trail Blazers": "#E03A3E",
    "Sacramento Kings": "#5A2D81",
    "San Antonio Spurs": "#000000",  # Black (silver might be too light)
    "Toronto Raptors": "#CE1141",
    "Utah Jazz": "#002B5C",
    "Washington Wizards": "#002B5C"
}

# Cache the schedule mapping to avoid reloading on every interaction
@st.cache(allow_output_mutation=True)
def load_schedule_data():
    """Load schedule mapping for all teams using the scraped data."""
    return create_schedule_mapping(regular_season_data='nba_reg_szn_24-25_scraped.csv')


def main():
    st.title("🏀 NBA Team Burden Visualization")
    st.markdown("Compare cumulative travel burden over the season for different NBA teams.")
    st.markdown("---")
    
    # Load schedule data
    with st.spinner("Loading schedule data..."):
        schedule_mapping = load_schedule_data()
    
    # Get all teams
    all_teams = get_all_teams(schedule_mapping)
    
    # Sidebar: Team selection organized by division
    st.sidebar.header("Select Teams")
    st.sidebar.markdown("Choose teams to compare by division:")
    
    # Track selected teams
    selected_teams = []
    
    # Create checkboxes organized by division
    for division, teams in NBA_DIVISIONS.items():
        st.sidebar.subheader(division)
        
        # Filter teams to only include those that exist in our data
        available_teams = [team for team in teams if team in all_teams]
        
        for team in available_teams:
            if st.sidebar.checkbox(team, key=f"checkbox_{team}"):
                selected_teams.append(team)
    
    # Add "Select All" / "Deselect All" buttons
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    if col1.button("Select All"):
        for division, teams in NBA_DIVISIONS.items():
            for team in teams:
                if team in all_teams:
                    st.session_state[f"checkbox_{team}"] = True
    
    if col2.button("Deselect All"):
        for division, teams in NBA_DIVISIONS.items():
            for team in teams:
                if team in all_teams:
                    st.session_state[f"checkbox_{team}"] = False
    
    # Main content area
    if not selected_teams:
        st.info("👈 Select one or more teams from the sidebar to visualize their cumulative burden.")
    else:
        # Calculate cumulative burden for each selected team
        fig = go.Figure()
        
        for team in selected_teams:
            schedule = get_team_schedule(schedule_mapping, team)
            
            if schedule is None:
                st.warning(f"Could not load schedule for {team}")
                continue
            
            # Calculate cumulative burden with metadata
            result = calculate_cumulative_burden_with_metadata(schedule)
            
            if result[0] is None or len(result[0]) == 0:
                st.warning(f"Could not calculate burden for {team}")
                continue
            
            game_numbers, cumulative_burdens, game_datetimes, locations, opponents = result
            
            # Get team color
            team_color = TEAM_COLORS.get(team, "#808080")  # Default to gray if not found
            
            # Prepare custom data for hover template
            # We'll pass metadata as a 2D array where each row contains [datetime, location, opponent]
            custom_data = np.column_stack([game_datetimes, locations, opponents])
            
            # Add trace for this team with enhanced hover template
            fig.add_trace(go.Scatter(
                x=game_numbers,
                y=cumulative_burdens,
                mode='lines',
                name=team,
                line=dict(color=team_color, width=2.5),
                customdata=custom_data,
                hovertemplate=(
                    f'<b>{team}</b><br>' +
                    'Game: %{x}<br>' +
                    'Date/Time: %{customdata[0]}<br>' +
                    'Location: %{customdata[1]}<br>' +
                    'Opponent: %{customdata[2]}<br>' +
                    'Cumulative Burden: %{y:.2f}' +
                    '<extra></extra>'
                )
            ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Cumulative Burden Over Season',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            xaxis_title="Game Number",
            yaxis_title="Cumulative Total Burden",
            hovermode='closest',
            height=600,
            template='plotly_white',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(l=80, r=150, t=80, b=80)
        )
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Display selected teams info
        st.markdown("---")
        st.subheader("Selected Teams")
        cols = st.columns(min(len(selected_teams), 5))
        for idx, team in enumerate(selected_teams):
            with cols[idx % len(cols)]:
                team_color = TEAM_COLORS.get(team, "#808080")
                st.markdown(f"<span style='color: {team_color}; font-weight: bold;'>●</span> {team}", 
                           unsafe_allow_html=True)


if __name__ == "__main__":
    main()

