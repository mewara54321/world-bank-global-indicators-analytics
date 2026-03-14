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


#---------------------------------------------Cleaning countries data frame---------------------------------------------

countries["region"] = countries["region"].apply(lambda x : x["value"])
countries["incomeLevel"] = countries["incomeLevel"].apply(lambda x : x["value"])
countries["lendingType"] = countries["lendingType"].apply(lambda x : x["value"])

# Drop unnecessary column
countries.drop(columns = ["adminregion" , "capitalCity"], inplace = True)

# Rename column
countries.rename(columns = {'iso2Code' : 'country_id'} , inplace = True)



