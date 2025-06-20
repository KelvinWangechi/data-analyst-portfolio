import pandas as pd
import random
from datetime import datetime, timedelta

num_rows = 500
start_date = datetime(2024, 1, 1)
platforms = ['TikTok', 'Meta', 'LinkedIn', 'Twitter', 'Instagram']
campaigns = ['Brand Awareness', 'Lead Gen', 'Product Launch', 'Retargeting']
data = []

for i in range(num_rows):
    date = start_date + timedelta(days=i % 180)
    platform = random.choice(platforms)
    campaign = random.choice(campaigns)
    impressions = random.randint(1000, 50000)
    clicks = random.randint(50, impressions // 10)
    spend = round(random.uniform(100, 5000), 2)
    conversions = random.randint(0, clicks // 5)
    cr = round(conversions / clicks * 100, 2) if clicks else 0
    cpa = round(spend / conversions, 2) if conversions else None
    revenue = round(conversions * random.uniform(50.0, 300.0), 2)
    data.append({
        "Date": date.strftime("%Y-%m-%d"),
        "Platform": platform,
        "Campaign": campaign,
        "Impressions": impressions,
        "Clicks": clicks,
        "Spend": spend,
        "Conversions": conversions,
        "Conversion_Rate": cr,
        "CPA": cpa,
        "Revenue": revenue
    })

df = pd.DataFrame(data)
# df.to_csv("social_media_performance.csv", index=False)

csv_path = "[OS_PATH]/social_media_performance.csv"
df.to_csv(csv_path, index=False)
print(f"Generated {csv_path}")

## Edit [OS_PATH] to insert your preferred location to save the file
