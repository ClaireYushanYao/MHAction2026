# data_store.py
from pathlib import Path
import pathlib
import pandas as pd

here = pathlib.Path(__file__).parent

mhvillage_df = pd.read_csv(here / "dataMI/MHVillageDec7_Legislative1.csv")
mhvillage_df["Sites"] = pd.to_numeric(mhvillage_df["Sites"], downcast="integer")

lara_df = pd.read_csv(here / "dataMI/LARA_with_coord_and_legislativedistrict1.csv")
lara_df["County"] = lara_df["County"].str.title()

mhvillage_basic = pd.read_csv(here / "dataMI/mhvillage_base.csv")
mhvillage_basic["Sites"] = pd.to_numeric(mhvillage_basic["Sites"], downcast="integer")

lara_basic = pd.read_csv(here / "dataMI/lara_base.csv")
lara_basic["County"] = lara_basic["County"].str.title()

house_districts_geojson_path = here / "dataMI/Michigan_State_House_Districts_2021.json"
senate_districts_geojson_path = here / "dataMI/Michigan_State_Senate_Districts_2021.json"

# shared lists used by the map builder
circlelist_lara: list = []
circlelist_mh: list = []
mklist_mh: list = []
mklist_lara: list = []
upper_layers: list = []
lower_layers: list = []