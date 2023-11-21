import pandas as pd
import geopy

locator = geopy.Nominatim(user_agent="myGeocoder")
df = pd.read_excel("IR_Institute_konsolidierte_Liste.xlsx")

df = df.head()

df["geo"] = df["Adresse"].apply(locator.geocode)

# df["latitude"], df["longitude"] = df["

print(df.geo)
