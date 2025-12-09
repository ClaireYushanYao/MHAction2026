import io
from datetime import date
import pandas as pd

from shiny import reactive, render, ui
from shinywidgets import render_widget

# Imports from your refactored modules
from ui_layout import basemaps
from data_store import (
    lara_df,
    mhvillage_df,
    house_districts_geojson_path,
    senate_districts_geojson_path,
)
from map_layers import create_map
from plot_utils import build_infographics1, build_infographics2


def server(input, output, session):

    # -----------------------------
    # Subcategory options (reactive)
    # -----------------------------
    @reactive.Calc
    def sub_category_options():
        main_category = input.main_category()
        df_name = input.datasource()

        if main_category and df_name == "MHVillage":
            return mhvillage_df[main_category].dropna().tolist()

        elif main_category:
            if main_category in ("House district", "Senate district"):
                return (
                    lara_df[main_category]
                    .dropna()
                    .astype(int)
                    .unique()
                    .tolist()
                )
            else:
                return lara_df[main_category].dropna().unique().tolist()

        return []

    # UI for subcategory dropdown
    @output
    @render.ui
    def sub_category_ui():
        options = sub_category_options()
        options.sort()
        return ui.input_select(
            "sub_category",
            "Select district/county of interest (Note – only locations with MHC data will generate a table):",
            options,
        )

    # -----------------------------
    # Map
    # -----------------------------
    @output
    @render_widget
    def map():
        basemap = basemaps[input.basemap()]
        layerlist = input.layers()
        return create_map(basemap, layerlist)

    # -----------------------------
    # Infographics
    # -----------------------------
    @output
    @render.plot
    def infographics1():
        build_infographics1()

    @output
    @render.download(filename=lambda: "all-mhc-counts.csv")
    def download_info1():
        df = lara_df[["County", "Total_#_Sites"]].dropna()
        county_sites_df = (
            df.groupby("County")["Total_#_Sites"]
            .sum()
            .reset_index()
            .rename(columns={"Total_#_Sites": "Number of Sites"})
            .sort_values("Number of Sites", ascending=False)
        )

        output_stream = io.StringIO()
        county_sites_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        return output_stream.getvalue(), ""

    @output
    @render.plot
    def infographics2():
        build_infographics2()

    @output
    @render.download(filename=lambda: "all-mhc-rents.csv")
    def download_info2():
        total_sites = (
            mhvillage_df.groupby("County")["Average_rent"].mean().dropna()
        )

        total_sites = (
            total_sites.sort_values(ascending=True)
            .to_frame()
            .reset_index()
        )

        df_clean = mhvillage_df[["County", "Average_rent"]].dropna()
        county_counts = df_clean["County"].value_counts().to_frame().reset_index()

        combined = pd.merge(total_sites, county_counts, on="County")
        combined = combined.sort_values("count", ascending=False)

        output_stream = io.StringIO()
        combined.to_csv(output_stream, index=False)
        output_stream.seek(0)
        return output_stream.getvalue(), ""

    # -----------------------------
    # Table Data (reactive)
    # -----------------------------
    @reactive.Calc
    def reactive_site_list():

        # MHVillage logic
        if input.datasource() == "MHVillage":
            if input.main_category() == "County":
                df = mhvillage_df[
                    mhvillage_df["County"] == input.sub_category()
                ][["Name", "Sites", "FullstreetAddress"]]
            else:
                df = mhvillage_df[
                    mhvillage_df[input.main_category()]
                    == int(float(input.sub_category()))
                ][["Name", "Sites", "FullstreetAddress"]]

            df = df.rename(
                columns={
                    "Sites": "Number of Sites",
                    "FullstreetAddress": "Address",
                }
            )
            df = df[["Name", "Address", "Number of Sites"]]
            df = (
                df.dropna(subset=["Number of Sites"])
                .astype({"Number of Sites": int})
                .sort_values("Number of Sites", ascending=False)
            )
            return df

        # LARA logic
        else:
            if input.main_category() == "County":
                df = lara_df[
                    lara_df[input.main_category()] == input.sub_category()
                ][["DBA", "Owner / Community_Name", "Total_#_Sites", "Location_Address"]]
            else:
                district = int(float(input.sub_category()))
                df = lara_df[
                    lara_df[input.main_category()] == district
                ][["DBA", "Owner / Community_Name", "Total_#_Sites", "Location_Address"]]

            # Combine DBA + Owner/Community
            df["Name"] = df.apply(
                lambda x: x["DBA"]
                if pd.notnull(x["DBA"]) and x["DBA"].strip() != ""
                else x["Owner / Community_Name"],
                axis=1,
            )

            df = df.drop(columns=["DBA", "Owner / Community_Name"])
            df.columns = df.columns.str.replace("_", " ")

            df = df.rename(
                columns={
                    "Total # Sites": "Number of Sites",
                    "Location Address": "Address",
                }
            )

            df = df[["Name", "Address", "Number of Sites"]]
            df = (
                df.dropna(subset=["Number of Sites"])
                .astype({"Number of Sites": int})
                .sort_values("Number of Sites", ascending=False)
            )
            return df

    # -----------------------------
    # Table output
    # -----------------------------
    @output
    @render.table
    def site_list():
        return reactive_site_list()

    @output
    @render.table
    def site_list_summary():
        df = reactive_site_list()
        num_mhcs = len(df)
        num_sites = pd.to_numeric(df["Number of Sites"], errors="coerce").sum()

        summary_df = pd.DataFrame(
            {
                "Number of MHC's": [num_mhcs],
                "# of Sites": [num_sites],
            }
        )
        return summary_df

    # -----------------------------
    # Download table data
    # -----------------------------
    @output
    @render.download(filename=lambda: f"data-{date.today().isoformat()}-mhc.csv")
    def download_data():
        df = reactive_site_list()

        # Summary section
        num_mhcs = len(df)
        num_sites = pd.to_numeric(df["Number of Sites"], errors="coerce").sum()

        summary_df = pd.DataFrame(
            {
                "Number of MHC's": [num_mhcs],
                "# of Sites": [num_sites],
            }
        )

        output_stream = io.StringIO()
        df.to_csv(output_stream, index=False)
        summary_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        return output_stream.getvalue(), ""

    # -----------------------------
    # Raw data downloads
    # -----------------------------
    @output
    @render.download(filename=lambda: "MHVillageDec7_Legislative1.csv")
    def download_mhvillage():
        output_stream = io.StringIO()
        mhvillage_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        return output_stream.getvalue(), ""

    @output
    @render.download(filename=lambda: "LARA_with_coord_and_legislativedistrict1.csv")
    def download_lara():
        output_stream = io.StringIO()
        lara_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        return output_stream.getvalue(), ""

    @output
    @render.download(filename=lambda: "Michigan_State_House_Districts_2021.json")
    def download_house_districts():
        with open(house_districts_geojson_path, "r") as f:
            contents = f.read()
        return contents, ""

    @output
    @render.download(filename=lambda: "Michigan_State_Senate_Districts_2021.json")
    def download_senate_districts():
        with open(senate_districts_geojson_path, "r") as f:
            contents = f.read()
        return contents, ""