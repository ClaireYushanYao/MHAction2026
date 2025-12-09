# plot_utils.py
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

from data_store import lara_df, mhvillage_df


def build_infographics1():
    total_sites_by_name = (
        lara_df[["County", "Total_#_Sites"]]
        .dropna()
        .groupby("County")
        .sum()
        .sort_values(by="Total_#_Sites", ascending=False)
        .iloc[:20, :]
    )
    sns.set_color_codes("pastel")
    ax = sns.barplot(x="Total_#_Sites", y="County", data=total_sites_by_name, color="b")
    ax.set(
        xlabel="Total Number of Sites",
        title="Top 20 Michigan Counties by number of manufactured home sites (LARA)",
    )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))


def build_infographics2():
    total_sites_by_name = mhvillage_df.groupby("County")["Average_rent"].mean().dropna()
    total_sites_by_name = total_sites_by_name.sort_values(ascending=True)
    total_sites_by_name = total_sites_by_name.to_frame().reset_index()

    df_clean = mhvillage_df[["County", "Average_rent"]].dropna()
    county_counts = df_clean["County"].value_counts().to_frame().reset_index()

    total_sites_by_name_count = pd.merge(total_sites_by_name, county_counts, on="County")
    total_sites_by_name_count = total_sites_by_name_count.sort_values(
        by="count", ascending=False
    )
    total_sites_by_name_20 = total_sites_by_name_count[:20]
    total_sites_by_name_20.sort_values("Average_rent", ascending=False, inplace=True)

    ax = sns.barplot(
        x="Average_rent",
        y="County",
        data=total_sites_by_name_20,
        color="b",
    )
    ax.set(xlabel="Average rent", title="Average rent by county (MHVillage)")
    count0 = total_sites_by_name_20["count"]
    ax.bar_label(ax.containers[0], labels=[f"{c:.0f}" for c in count0], label_type="center")