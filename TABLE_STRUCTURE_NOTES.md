# TeamRankings.com Table Structure Analysis

## What We Found:
- **Table shape**: (1200, 3) - 1200 games, 3 columns
- **Columns**: 
  1. Matchup (e.g., "Houston @ Okla City")
  2. Time (e.g., "7:30 PM")
  3. Location/Stadium (e.g., "Paycom Center")

## Data Format:
- Matchups use format: "Visitor @ Home" (e.g., "Houston @ Okla City")
- Times are in 12-hour format with AM/PM
- Stadium names need to be mapped to team names

## Issues:
- Date information was lost in HTML parsing (dates were in column headers)
- We'll need to either:
  1. Parse HTML differently to extract dates
  2. Match games to dates based on known schedule
  3. Use the order of games to infer dates

## Next Steps:
1. Parse matchup strings to extract visitor and home teams
2. Map stadium names to team names using our mapping
3. Convert time format to match expected format
4. Either extract dates from HTML or match to known schedule dates

