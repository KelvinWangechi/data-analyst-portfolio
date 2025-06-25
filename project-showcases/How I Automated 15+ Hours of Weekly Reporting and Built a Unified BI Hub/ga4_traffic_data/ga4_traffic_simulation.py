import pandas as pd
import random
from datetime import datetime, timedelta

# Parameters
num_rows = 500
start_date = datetime(2024, 1, 1)
sources = ['organic', 'direct', 'referral', 'google / cpc', 'social', 'email']
mediums = ['organic', 'none', 'referral', 'paid', 'social', 'email']
# In GA4, "organic" vs "direct" distinction: direct means no referral info :contentReference[oaicite:1]{index=1}

data = []
for i in range(num_rows):
    date = start_date + timedelta(days=i % 180)
    source = random.choice(sources)
    medium = random.choice(mediums)
    sessions = random.randint(100, 2000)
    new_users = int(sessions * random.uniform(0.2, 0.6))
    conversions = int(sessions * random.uniform(0.01, 0.05))
    revenue = round(conversions * random.uniform(20.0, 200.0), 2)  # value per conversion
    data.append([
        date.strftime("%Y-%m-%d"),
        source,
        medium,
        sessions,
        new_users,
        conversions,
        revenue
    ])

df = pd.DataFrame(
    data,
    columns=["Date", "Source", "Medium", "Sessions", "New_Users", "Conversions", "Revenue"]
)

csv_path = "[OS_PATH]/ga4_traffic.csv"
df.to_csv(csv_path, index=False)
print(f"Generated {csv_path}")

## Edit [OS_PATH] to insert your preferred location to save the file
