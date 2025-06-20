import pandas as pd
import random
from datetime import datetime, timedelta

# Parameters
num_rows = 1500
start_date = datetime(2024, 1, 1)
lead_sources = ['Google_Ads', 'TikTok', 'LinkedIn', 'Email', 'Referral']
lead_stages = ['Prospect', 'Qualified', 'Proposal', 'Won', 'Lost']
regions = ['New York', 'California', 'Texas', 'Florida', 'Illinois', 'New Jersey', 'Georgia', 'Arizona', 'Washington', 'Colorado']

# Generate data
data = []
for i in range(num_rows):
    date = start_date + timedelta(days=i % 90)
    lead_source = random.choice(lead_sources)
    lead_stage = random.choice(lead_stages)
    revenue_potential = random.randint(50000, 500000)  # in USD
    region = random.choice(regions)
    data.append([date.strftime("%Y-%m-%d"), lead_source, lead_stage, revenue_potential, region])

# Create DataFrame
df = pd.DataFrame(data, columns=["Date", "Lead_Source", "Lead_Stage", "Revenue_Potential", "Region"])

# Save to CSV
# csv_path = "/mnt/data/salesforce_leads.csv"
# df.to_csv(csv_path, index=False)

csv_path = "[OS_PATH]/salesforce_leads.csv"
df.to_csv(csv_path, index=False)
print(f"Generated {csv_path}")


## Edit [OS_PATH] to insert your preferred location to save the file
