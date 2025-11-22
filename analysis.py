import csv
import pandas as pd

# Read the CSV file and calculate average distances
def calculate_average_distances(csv_file):
    """
    Calculate the average distance from each stadium to all other stadiums.
    
    Args:
        csv_file: Path to the CSV file containing distance matrix
        
    Returns:
        Dictionary with team names as keys and average distances as values
    """
    average_distances = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        # Read header row to get team names
        header = next(reader)
        teams = header[1:]  # Skip the first empty column
        
        # Read each row and calculate average distance
        for row in reader:
            if not row or not row[0]:  # Skip empty rows
                continue
                
            team_name = row[0]
            distances = [float(dist) for dist in row[1:] if dist]  # Convert to float, skip empty values
            
            # Calculate average excluding the 0.0 self-distance
            # Filter out 0.0 values (self-distance)
            other_distances = [d for d in distances if d != 0.0]
            
            if other_distances:
                average_distance = sum(other_distances) / len(other_distances)
                average_distances[team_name] = average_distance
    
    return average_distances


# Create DataFrame with team, average distance, and yearly road trip distance
def create_BTY_dataframe(csv_file):
    """
    Create a DataFrame with team, average distance, and average yearly road trip.
    
    Args:
        csv_file: Path to the CSV file containing distance matrix
        
    Returns:
        DataFrame with columns: team, average_distance, average_yearly_road_trip
    """
    average_distances = calculate_average_distances(csv_file)
    
    # Create DataFrame
    BTY_data = pd.DataFrame({
        'team': list(average_distances.keys()),
        'average_distance': list(average_distances.values()),
        'average_yearly_road_trip': [dist * 41 for dist in average_distances.values()]
    })
    
    return BTY_data


# Create the BTY_data DataFrame
BTY_data = create_BTY_dataframe("nba_stadium_distances.csv")