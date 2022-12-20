#!/usr/bin/env python
#
#
from urllib.error import HTTPError
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

fips_url = "https://en.wikipedia.org/wiki/Federal_Information_Processing_Standard_state_code"
cites_base_url = "https://www2.census.gov/geo/tiger/TIGER2021/PLACE/tl_2021_{FIPSCODE:02d}_place.zip"

fips_df = pd.read_html(fips_url)[0]

fips_records = fips_df.loc[
    ~fips_df.Name.str.contains("\*"),
    ["Name", "Numeric code"]
].to_dict(orient="records")


for item in tqdm(fips_records):
    name = item["Name"]
    fips = item["Numeric code"]
    cities_url = cites_base_url.format(FIPSCODE=fips)
    try:
        cities_df = gpd.read_file(cities_url).to_crs("EPSG:3857")
    except HTTPError as e:
        print(f"Error downloading {name}, skipping it.")
        continue
    total = cities_df.shape[0]
    fn = f"{name.lower().replace(' ', '-')}_{fips:02d}_{total}.fgb"
    cities_df[["PLACEFP", "NAME", "CLASSFP", "ALAND", "AWATER", "geometry"]].to_file(
        fn,
        driver="FlatGeobuf"
    )

