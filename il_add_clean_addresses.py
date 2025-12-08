## this code takes the addresses from MH village
## and uses geocode and the google API to generate clean addresses
## and GPS coordinates respectively
import copy
#import re
import pandas as pd
#import geopandas as gpd
#import numpy as np
#import shapely
#from shapely.geometry import Point
##from regex_add import regex, regex1
#import geopy
from geopy.geocoders import Nominatim

####INPUT FOR UPDATING DATA

#assuming in a relative folder data/
path2folder = r"./dataIL/" # fill in the path to your folder here.
assert len(path2folder) > 0

MHVILLAGE_file_str = "MHVillage_IL_Parks.csv"

#name of outputted files
##mhvillage_name_str = 'data/mhvillage_dec7_googlecoord.csv'

########################################################


# !!!!!!!!!! free but doesn't work as well as google API
# is very slow
geolocator = Nominatim(user_agent="kajana@umich.edu")

# two functions from medium article: 
# link:https://towardsdatascience.com/transform-messy-address-into-clean-data-effortlessly-using-geopy-and-python-d3f726461225
"""
def extract_clean_address(address):
    try:
       location = geolocator.geocode(address)
       return location.address
    except:
        return ''
"""

def extract_lat_long(address):
    try:
        location = geolocator.geocode(address)
        return [location.latitude, location.longitude]
    except:
        return ''


# add clean addresses


mhvillage_df = pd.read_csv(path2folder + MHVILLAGE_file_str)
# prevent editing the original csv, drop the empty rows
mhvillage_df_copy = copy.deepcopy(mhvillage_df)
mhvillage_df_copy = mhvillage_df_copy.dropna(how='all')

##### CLEANING

# check for complete duplicate rows, duplicates in each column
#print(mhvillage_df_copy.duplicated().sum())
#print(mhvillage_df_copy.nunique())

# checking for secret duplicates (assumuption: if name, address,
#  city state zip same, are real duplicates)

# (from gemini <3)
# Create a unique ID for each group of duplicates
mhvillage_df_copy['duplicate_group_id'] = mhvillage_df_copy.groupby(['Address',\
                                                                      'Name', 'City State ZIP']).ngroup()

# Display the first few rows of each group (optional, for checking)
#print(mhvillage_df_copy[mhvillage_df_copy.duplicated(subset=['Address', 'Name', 'City State ZIP'],
#  keep=False)].sort_values('duplicate_group_id'))

# Define the aggregation dictionary
agg_rules = {
    # Columns we grouped by (take the first value, though all are the same)
    'Address': 'first',
    'Name': 'first',
    'City State ZIP': 'first',
    
    #Get the first non-NaN value
    'ZIP': lambda x: x.dropna().iloc[0] if not x.dropna().empty else None,

    # Get max
    'Number of Sites': 'max',
    'Url': 'max'
}

# Group by the unique ID and apply the aggregation rules
mhvillage_df_copy = mhvillage_df_copy.groupby('duplicate_group_id').agg(agg_rules).reset_index()

# Drop the temporary ID column
mhvillage_df_copy = mhvillage_df_copy.drop(columns=['duplicate_group_id'])
# yay

# is this necessary...?
MH_col_names = mhvillage_df_copy.columns.tolist()

# need to combine 'Address' + 'City State ZIP' + 'ZIP' into one col
#  to increase likelihood of extract_lat_long working

mhvillage_df_copy['Address'] = mhvillage_df_copy['Address'].astype('string')
mhvillage_df_copy['City State ZIP'] = mhvillage_df_copy['City State ZIP'].astype('string')
mhvillage_df_copy['ZIP_str'] = (mhvillage_df_copy['ZIP'].astype(int)).astype(str)
mhvillage_df_copy["FULL Address"] = (mhvillage_df_copy["Address"])+ \
    (mhvillage_df_copy["City State ZIP"]) + ", " + (mhvillage_df_copy["ZIP_str"])

print('Checkpt: pre find latlong')
mhvillage_df_copy['lat_long'] = mhvillage_df_copy.apply(lambda x: \
                                                        extract_lat_long(x['FULL Address']) , \
                                                            axis =1)
mhvillage_df_copy['latitude'] = mhvillage_df_copy.apply(lambda x: x['lat_long'][0] \
                                                        if x['lat_long'] != '' else '', axis =1)
mhvillage_df_copy['longitude'] = mhvillage_df_copy.apply(lambda x: x['lat_long'][1] \
                                                         if x['lat_long'] != '' else '', axis =1)
mhvillage_df_copy.drop(columns = ['lat_long'], inplace = True)

mhvillage_df_copy.to_csv('dataIL/LATLONG_MHVillage_IL_Parks.csv')