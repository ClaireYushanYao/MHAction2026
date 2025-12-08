#add legislative districts to mhvillage data

# this code takes a csv with community names, addresses, and gps coordinate
# then uses the districts geoJSON file to find the district for each coordinate
# we use the original geojson from https://gis-michigan.opendata.arcgis.com/
# we do not upload them to shiny because their too big so they don't appear in the
# github as well

# data from https://www.elections.il.gov/shape/2020_House_Districts/ 

#this code assumes the gps coordinates contained in each file ar called
# 'longitude', 'latitude' based on the encoding in add_clean_addresses

import pandas as pd
import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import Point
import geopy

#####INPUT

path2folder = r"./dataIL/" # fill in the path to your folder here.
assert len(path2folder) > 0

MHVILLAGE_FILE_IN = "LATLONG_MHVillage_IL_Parks.csv"

# The original program uses gpd to read geojson, however IL only available
# in shapefile, so will have geojson read from that

house_shapefile_path = path2folder + "House Plan.shp"
senate_shapefile_path = path2folder + "Senate Plan.shp"

#name of outut files
MHVILLAGE_FILE_OUT = "LEGIS_LATLONG_MHVillage_IL_Parks.csv"

#######################################################################################

#ACTION!!! - read
def find_district(shpfile, coordinates):
    # Load the Shapefile into a GeoDataFrame
    gdf = gpd.read_file(shpfile)
    
    # Create a Point geometry from the coordinates
    point = Point(coordinates)
    
    # Check each district for a containing point
    for _, row in gdf.iterrows():  # We use iterrows() here to get the row as a Series
        # If the point is within the polygon of this row, return the label
        if point.within(row['geometry']):
            return row['ID']
    return None  # Return None or an appropriate value if the point isn't in any district

#read data
mhvillage_df = pd.read_csv(path2folder + MHVILLAGE_FILE_IN)

#create columns
sLength = len(mhvillage_df['longitude'])
mhvillage_df['House district'] = pd.Series(np.zeros(sLength), index=mhvillage_df.index)
mhvillage_df['Senate district'] = pd.Series(np.zeros(sLength), index=mhvillage_df.index)


for ind in range(len(mhvillage_df)):
    lon = float(mhvillage_df['longitude'].iloc[ind])
    lat = float(mhvillage_df['latitude'].iloc[ind])
    if lat and lon:
        # Check the legislative district
        district_house = find_district(house_shapefile_path, (lon,lat))
        district_senate = find_district(senate_shapefile_path, (lon,lat))
        if district_senate and district_house:
            #print(district_senate)
            #print(district_house)
            print(ind)
            mhvillage_df.loc[ind, 'House district'] = int(district_house)
            mhvillage_df.loc[ind, 'Senate district'] = int(district_senate)



mhvillage_df.to_csv(path2folder + MHVILLAGE_FILE_OUT)
