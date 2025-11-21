import pandas as pd
import numpy as np

stadiums = pd.read_csv('stadiums 2.csv')

nba_stadiums = stadiums[stadiums['League'] == 'NBA']

nba_stadiums.to_csv('nba_stadiums.csv', index=False)
