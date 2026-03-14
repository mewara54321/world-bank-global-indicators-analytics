import pandas as pd
import requests
import time


#---------------------------------------------World bank countries endpoint--------------------------------------------
url =f"https://api.worldbank.org/countries?format=json&per_page=300"

response = requests.get(url)

# print(response.status_code) --> 200 output means request successful

data = response.json()

# data[0] -> metadata
# {'page':1,'pages':1,'per_page':'300','total':296}

# data[1] -> actual country data

countries = data[1]

# convert to dataframe
countries = pd.DataFrame(countries)

#Save countries raw datasets
countries.to_csv("../data/raw/countries_raw.csv", index=False)
print("Countries raw dataset saved")

#---------------------------------------------Cleaning countries data frame---------------------------------------------

countries["region"] = countries["region"].apply(lambda x : x["value"])
countries["incomeLevel"] = countries["incomeLevel"].apply(lambda x : x["value"])
countries["lendingType"] = countries["lendingType"].apply(lambda x : x["value"])

# Drop unnecessary column
countries.drop(columns = ["adminregion" , "capitalCity"], inplace = True)

# Rename column
countries.rename(columns = {'iso2Code' : 'country_id'} , inplace = True)

# Save countries processed datasets
#countries.to_csv("../data/processed/countries_clean.csv", index=False)
#print("Countries cleaned dataset saved")

#---------------------------------------------Getting indicators---------------------------------------------
base_url = "https://api.worldbank.org/v2/indicator?format=json"
response = requests.get(base_url)
#print(response.status_code) --> 200 output means request successful
indicators_data = response.json()

# indicators_data[0] -->meta data
#{'page': 1, 'pages': 590, 'per_page': '50', 'total': 29470}

#indicators_data[1] -->Actual data

all_dfs = []
total_pages = indicators_data[0]["pages"]
for i in range(1,total_pages+1):
    url = f"https://api.worldbank.org/v2/indicator?format=json&per_page=500&page={i}"
    response = requests.get(url, timeout=30)

    if response.status_code == 200:
        data = response.json()

        if len(data)<2:
            print(f"NO data at page {i}")

        indicators = data[1]
        df = pd.DataFrame([{"id" : item['id'],
                       "name" : item['name']} for item in indicators ])

        all_dfs.append(df)
        print(f"Page{i}: {len(df)} indicators collected")

        time.sleep(0.3)

    else :
        print(f"Failed to fetch page {i}, status code {response.status_code}")


final_df = pd.concat(all_dfs , ignore_index = True)
print(final_df)

# Save indicator metadata dataset
final_df.to_csv("../data/raw/world_bank_indicators_metadata.csv", index=False)
print("Indicator metadata saved")


