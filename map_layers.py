# map_layers.py
import json
from geopy.geocoders import Nominatim
from shapely.geometry import Point, shape
from ipywidgets import Label, Layout
import ipyleaflet as L
from ipyleaflet import GeoJSON, LayerGroup

from data_store import (
    mhvillage_df,
    lara_df,
    house_districts_geojson_path,
    senate_districts_geojson_path,
    circlelist_lara,
    circlelist_mh,
    mklist_lara,
    mklist_mh,
    upper_layers,
    lower_layers,
)

# ---- Geocoding helpers ----
def geocode_address(address: str):
    geolocator = Nominatim(user_agent="your_application_name")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None


def check_legislative_district(lat, lng, districts_geojson_path):
    point = Point(lng, lat)
    districts = gpd.read_file(districts_geojson_path)
    spatial_index = districts.sindex
    possible_matches_index = list(spatial_index.query(point))
    possible_matches = districts.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.contains(point)]

    if not precise_matches.empty:
        return precise_matches.iloc[0]["NAME"]
    return None


def find_geojson_centroid(geojson_feature):
    geom = shape(geojson_feature["geometry"])
    return geom.centroid.coords[0]  # (lon, lat)


def build_district_layers(upper: int = 0):
    layer_group = LayerGroup()
    label = Label(layout=Layout(width="100%"))

    if upper == 1:
        color = "green"
        geojson_path = senate_districts_geojson_path
        name = "Michigan Senate Legislative Districts"
    else:
        color = "purple"
        geojson_path = house_districts_geojson_path
        name = "Michigan House Legislative Districts"

    with open(geojson_path, "r") as f:
        michigan_districts_data = json.load(f)

    layerk = GeoJSON(
        data=michigan_districts_data,
        name=name,
        style={"color": color, "weight": 1, "fillOpacity": 0.3},
        hover_style={"color": "orange", "weight": 3},
    )

    layer_group.add_layer(layerk)

    if upper == 1:
        upper_layers.append(layer_group)
    else:
        lower_layers.append(layer_group)

    return layer_group


def build_marker_layer(LARA_C: int):
    if not LARA_C:
        if circlelist_mh and mklist_mh:
            return
        for ind in range(len(mhvillage_df)):
            lon = float(mhvillage_df["longitude"].iloc[ind])
            lat = float(mhvillage_df["latitude"].iloc[ind])

            # handle missing
            if pd.isna(mhvillage_df["House district"].iloc[ind]) or pd.isna(
                mhvillage_df["Senate district"].iloc[ind]
            ):
                house_mh = "missing"
                senate_mh = "missing"
            else:
                house_mh = round(mhvillage_df["House district"].iloc[ind])
                senate_mh = round(mhvillage_df["Senate district"].iloc[ind])

            if pd.isna(mhvillage_df["Sites"].iloc[ind]):
                mhsites = "missing"
            else:
                mhsites = round(mhvillage_df["Sites"].iloc[ind])

            markeri = L.Marker(
                location=(lat, lon),
                draggable=False,
                title=str(mhvillage_df["Name"].iloc[ind])
                + " , number of sites: "
                + str(mhsites)
                + " , average rent: "
                + str(mhvillage_df["Average_rent"].iloc[ind])
                + " , House district: "
                + str(house_mh)
                + " , Senate district: "
                + str(senate_mh)
                + " , url: %s" % str(mhvillage_df["Url"].iloc[ind])
                + " , MHVillage",
            )
            circleMHi = L.Circle(location=(lat, lon), radius=1, color="orange", fill_color="orange")
            circlelist_mh.append(circleMHi)
            mklist_mh.append(markeri)
    else:
        if circlelist_lara and mklist_lara:
            return
        for ind in range(len(lara_df)):
            lon = float(lara_df["longitude"].iloc[ind])
            lat = float(lara_df["latitude"].iloc[ind])

            if lon == 0 and lat == 0:
                continue

            if pd.isna(lara_df["House district"].iloc[ind]) or pd.isna(
                lara_df["Senate district"].iloc[ind]
            ):
                house_lara = "missing"
                senate_lara = "missing"
            else:
                house_lara = int(lara_df["House district"].iloc[ind])
                senate_lara = int(lara_df["Senate district"].iloc[ind])

            if pd.isna(lara_df["Total_#_Sites"].iloc[ind]):
                larasites = "missing"
            else:
                larasites = round(lara_df["Total_#_Sites"].iloc[ind])

            try:
                markeri = L.Marker(
                    location=(lat, lon),
                    draggable=False,
                    title=str(lara_df["Owner / Community_Name"].iloc[ind])
                    + " , number of sites: "
                    + str(larasites)
                    + " , House district: "
                    + str(house_lara)
                    + " , Senate district: "
                    + str(senate_lara)
                    + ", LARA",
                )
                circlei = L.Circle(location=(lat, lon), radius=1, color="blue", fill_color="blue")
                circlelist_lara.append(circlei)
                mklist_lara.append(markeri)
            except Exception:
                continue


def create_map(basemap, layerlist):
    the_map = L.Map(
        basemap=basemap,
        center=[44.44343571548758, -84.36155640717737],
        zoom=6,
        min_zoom=4,
        layout=Layout(width="100%", height="100%"),
        scroll_wheel_zoom=True,
    )

    markerorcircle = False

    if "Legislative districts (Michigan State Senate)" in layerlist:
        build_district_layers(upper=1)
        the_map.add_layer(upper_layers[0])

    if "Legislative districts (Michigan State House of Representatives)" in layerlist:
        build_district_layers(upper=0)
        the_map.add_layer(lower_layers[0])

    if "Marker MHVillage" in layerlist:
        build_marker_layer(LARA_C=0)
        marker_cluster = L.MarkerCluster(name="location markers", markers=tuple(mklist_mh))
        the_map.add_layer(marker_cluster)
        markerorcircle = True

    if "Marker LARA" in layerlist:
        build_marker_layer(LARA_C=1)
        marker_cluster = L.MarkerCluster(name="location markers", markers=tuple(mklist_lara))
        the_map.add_layer(marker_cluster)
        markerorcircle = True

    if "Circle MHVillage (location only)" in layerlist:
        if not markerorcircle:
            build_marker_layer(LARA_C=0)
        layergroup = L.LayerGroup(name="location circles", layers=circlelist_mh)
        the_map.add_layer(layergroup)
        markerorcircle = True

    if "Circle LARA (location only)" in layerlist:
        if not markerorcircle:
            build_marker_layer(LARA_C=1)
        layergroup = L.LayerGroup(name="location circles MH", layers=circlelist_lara)
        the_map.add_layer(layergroup)
        markerorcircle = True

    return the_map