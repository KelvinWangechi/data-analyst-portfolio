import pandas as pd
import random
from datetime import datetime, timedelta

# Settings
num_weeks = 104
start_date = datetime(2023, 5, 1)  # 104 weeks backward covers approx till May 2023
tasks = ['Lead_Report', 'Traffic_Analysis', 'Dashboard_Update', 'Data_Cleaning', 'Monthly_Summary']

data = []
for week in range(num_weeks):
    week_start = start_date + timedelta(weeks=week)
    for task in tasks:
        hours_before = round(random.uniform(1, 5), 2)
        hours_after = round(hours_before * random.uniform(0.05, 0.5), 2)
        data.append({
            'Week_Start': week_start.strftime('%Y-%m-%d'),
            'Task': task,
            'Hours_Before': hours_before,
            'Hours_After': hours_after,
            'Hours_Saved': round(hours_before - hours_after, 2)
        })

df = pd.DataFrame(data)
#df.to_csv('manual_reports_time.csv', index=False)
#print(f"Generated manual_reports_time.csv with {len(df)} records")


csv_path = "[OS_PATH]/manual_reports_time.csv"
df.to_csv(csv_path, index=False)
print(f"Generated {csv_path}")


## Edit [OS_PATH] to insert your preferred location to save the file
