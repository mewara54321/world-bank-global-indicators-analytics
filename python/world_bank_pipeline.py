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
countries.to_csv("../data/processed/countries_clean.csv", index=False)
print("Countries cleaned dataset saved")

#---------------------------------------------Getting List of indicators---------------------------------------------
base_url = "https://api.worldbank.org/v2/indicator?format=json"
response = requests.get(base_url)
# print(response.status_code) --> 200 output means request successful
indicators_data = response.json()

# indicators_data[0] -->meta data
# {'page': 1, 'pages': 590, 'per_page': '50', 'total': 29470}

# indicators_data[1] -->Actual data

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


#---------------------------------------------Getting data with the indicators---------------------------------------------
indicator_groups = {
"economic_activity_growth": [
"NY.GDP.MKTP.KD.ZG", # GDP growth (annual %)
"NY.GDP.PCAP.CD" # GDP per capita (current US$)
],
"labour_market_indicators": [
"SL.UEM.TOTL.ZS", # Unemployment total
"SL.UEM.1524.ZS", # Unemployment youth total (ages 15–24)
"SL.TLF.TOTL.IN" # Labour force, total
],
"trade_globalization": [
"NE.EXP.GNFS.CD", # Exports of goods and services (current US$)
"NE.IMP.GNFS.CD" # Imports of goods and services (current US$)
],
"poverty_inequality": [
"SI.POV.NAHC", # Poverty headcount ratio at national poverty lines (% of population)
"SI.POV.GINI" # Gini index (measure of income inequality)
],
"environmental_indicators": [
"EG.FEC.RNEW.ZS", # Renewable energy consumption (% of total final energy consumption)
"AG.LND.FRST.ZS" # Forest area (% of land area)
],
"health_indicators": [
"SP.DYN.LE00.IN", # Life expectancy at birth
"SP.DYN.IMRT.IN", # Infant mortality rate
"SH.H2O.BASW.ZS", # Access to at least basic water services (% of population)
"SH.XPD.CHEX.GD.ZS", # Current health expenditure (% of GDP)
"SH.IMM.IDPT", # Immunization, DPT (% of children ages 12–23 months)
"SH.IMM.MEAS", # Immunization, measles (% of children ages 12–23 months)
"SH.MMR.RISK.ZS", # Risk of maternal death
"SH.DTH.COMM.ZS", # Deaths from communicable diseases (% of total)
"SH.TBS.INCD", # Tuberculosis incidence (per 100,000 people)
"SH.STA.BRTC.ZS", # Births attended by skilled health staff (%)
"SH.STA.MMRT", # Maternal mortality ratio (modeled estimate, per 100,000 live births)
"SP.POP.65UP.TO.ZS", # Population ages 65 and above (% of total population)
"SH.HIV.INCD.ZS" # HIV incidence rate (per 1,000 uninfected population ages 15–49)
],
"technology_indicators": [
"IT.NET.USER.ZS", # Individuals using the Internet (% of population)
"IT.CEL.SETS.P2" # Mobile cellular subscriptions (per 100 people)
]}

base1_url = "https://api.worldbank.org/countries/all/indicators/{}?format=json&per_page=1000&page={}"

category_dataframes={}
for category , indicators in indicator_groups.items():
    print(f"Fetching information for category: {category}")
    all_dfs_for_category = []

    for indicator_code in indicators:
        print(f"Fetching data for indicator: {indicator_code}")
        page =1

        while True:
            url =base1_url.format(indicator_code, page)
            response = requests.get(url)
            if response.status_code != 200:
                print(f"No data for indicator '{indicator_code}' on page '{page}' ")
                break

            data = response.json()
            if len(data) <2:
                print(f"Failed at page: {page}")
                break


            total_pages = data[0]["pages"]
            record = data[1]

            df = pd.json_normalize(record)

            df = df[[
                "country.id", "country.value", "indicator.id",
                "indicator.value", "date", "value"
                ]].rename(columns={
                "country.id": "country_id",
                "country.value": "country_value",
                "indicator.id": "indicator_id",
                "indicator.value": "indicator_name",
                "date": "year"},inplace=True)

            df = df[df["year"].astype(int)>2015]
            all_dfs_for_category.append(df)


            if page >= total_pages:
                break
            else:
                page+=1
                time.sleep(0.3)


    if all_dfs_for_category :
        combined_df = pd.concat(all_dfs_for_category, ignore_index=True)
        category_dataframes[category] = combined_df
        print(f"Total rows collected for {category}: {len(combined_df)}")

    else:
        print(f"No data for category: {category}")

print("Data fetching completed")

indicator_values_df = pd.concat(category_dataframes.values(), ignore_index=True)

indicator_values_df.to_csv(
    "../data/raw/indicator_values_raw.csv",
    index=False
)

print("Indicator values dataset saved")



#-----------------------------------Getting different dataframe from each set indicators--------------------------------
economic_activity = category_dataframes.get("economic_activity_growth" , pd.DataFrame())
labour_market_jobs = category_dataframes.get("labour_market_indicators" , pd.DataFrame())
trade_globalization = category_dataframes.get("trade_globalization" , pd.DataFrame())
poverty_inequality = category_dataframes.get("poverty_inequality" , pd.DataFrame())
environmental_indicators = category_dataframes.get("environmental_indicators" , pd.DataFrame())
health_indicators = category_dataframes.get("health_indicators" , pd.DataFrame())
technology_indicators = category_dataframes.get("technology_indicators" , pd.DataFrame())


#-------------------------------------Merge with countries data frame---------------------------------------------------
economic = pd.merge(economic_activity , countries ,on="country_id" , how="inner")
labour_market = pd.merge(labour_market_jobs , countries ,on="country_id" , how="inner")
trade = pd.merge(trade_globalization , countries ,on="country_id" , how="inner")
poverty = pd.merge(poverty_inequality , countries ,on="country_id" , how="inner")
environmental = pd.merge(environmental_indicators , countries ,on="country_id" , how="inner")
health = pd.merge(health_indicators , countries ,on="country_id" , how="inner")
technology = pd.merge(technology_indicators , countries ,on="country_id" , how="inner")


#-------------------------------------Dropping un-necessary columns-----------------------------------------------------
economic.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
labour_market.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
trade.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
poverty.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
environmental.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
health.drop(columns=["indicator_id" , "name" , "id"], inplace=True)
technology.drop(columns=["indicator_id" , "name" , "id"], inplace=True)



economic.to_csv("../data/processed/economic_activity.csv", index=False)

labour_market.to_csv("../data/processed/labour_market.csv", index=False)

trade.to_csv("../data/processed/trade_globalization.csv", index=False)

poverty.to_csv("../data/processed/poverty_inequality.csv", index=False)

environmental.to_csv("../data/processed/environmental_indicators.csv", index=False)

health.to_csv("../data/processed/health_indicators.csv", index=False)

technology.to_csv("../data/processed/technology_indicators.csv", index=False)

print("All category datasets saved successfully")