from metrics import calculate_average_burden, create_schedule_mapping

# Create schedule mapping
print("Creating schedule mapping...")
schedules = create_schedule_mapping('nba_reg_szn_24-25_scraped.csv')

# Calculate average burdens
print("\nCalculating average burdens...")
burdens = calculate_average_burden(schedules)

# Display top 5 teams by burden
print('\nAverage Game Mile-Hours Burden (top 5):')
sorted_burdens = sorted(
    [(t, b) for t, b in burdens.items() if b is not None],
    key=lambda x: x[1],
    reverse=True
)
for team, burden in sorted_burdens[:5]:
    print(f'{team:30s}: {burden:8.2f}')

