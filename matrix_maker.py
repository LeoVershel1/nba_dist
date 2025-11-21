import pandas as pd
import numpy as np
from geopy.distance import geodesic

# Read the NBA stadiums data
stadiums_df = pd.read_csv('nba_stadiums.csv')

# Get the number of stadiums
num_stadiums = len(stadiums_df)

# Initialize the distance matrix with zeros
distance_matrix = np.zeros((num_stadiums, num_stadiums))

# Get team names for row and column labels
team_names = stadiums_df['Team'].values

# Loop through every stadium
for i in range(num_stadiums):
    # Get coordinates for stadium i
    lat_i = stadiums_df.iloc[i]['Lat']
    long_i = stadiums_df.iloc[i]['Long']
    coord_i = (lat_i, long_i)
    
    # Loop through every other stadium
    for j in range(num_stadiums):
        if i != j:  # Don't calculate distance from stadium to itself
            # Get coordinates for stadium j
            lat_j = stadiums_df.iloc[j]['Lat']
            long_j = stadiums_df.iloc[j]['Long']
            coord_j = (lat_j, long_j)
            
            # Calculate distance using geodesic (returns distance in miles)
            distance = geodesic(coord_i, coord_j).miles
            
            # Store the distance in the matrix
            distance_matrix[i][j] = distance
        else:
            # Distance from stadium to itself is 0
            distance_matrix[i][j] = 0.0

# Create a DataFrame with team names as row and column indices
distance_df = pd.DataFrame(
    distance_matrix,
    index=team_names,
    columns=team_names
)

# Round to 4 decimal places for readability
distance_df = distance_df.round(4)

# Save the distance matrix to a CSV file
distance_df.to_csv('nba_stadium_distances.csv')

print("Distance matrix created successfully!")
print(f"Matrix shape: {distance_df.shape}")
print("\nFirst few rows of the distance matrix:")
print(distance_df.head())

