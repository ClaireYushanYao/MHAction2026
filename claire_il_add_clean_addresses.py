"""
This script takes addresses from MH Village in IL and geocodes them using
OpenStreetMap's Nominatim API to produce latitude/longitude coordinates.
It performs:
    1) First-pass geocoding
    2) Retry missing using same address
    3) Retry missing using full address (street + city/state + ZIP)
    4) Export remaining missing rows for manual fix
    5) Merge manually entered coordinates back into the main file
"""

# -----------------------------
# Imports
# -----------------------------
import pandas as pd
from geopy.geocoders import Nominatim
from pathlib import Path
from tqdm import tqdm

tqdm.pandas(dynamic_ncols=True)


# -----------------------------
# Long-Lat Extraction Functions
# -----------------------------
"""
Reference: https://towardsdatascience.com/transform-messy-address-into-clean-data-effortlessly-using-geopy-and-python-d3f726461225
"""
def extract_clean_address(address):
    geolocator = Nominatim(user_agent="yyushan@umich.edu")
    try:
        location = geolocator.geocode(address)
        return location.address if location else None
    except Exception:
        return None


def extract_lat_long(address):
    geolocator = Nominatim(user_agent="yyushan@umich.edu")

    try:
        location = geolocator.geocode(address)
        if location is None:
            return None
        return [location.latitude, location.longitude]
    except Exception:
        return None


# -----------------------------
# Geocode Functions (Auto)
# -----------------------------
def get_coordinates(data_dir, input_file, address_col, output_file):

    input_path = Path(input_file)
    output_path = Path(output_file)

    df = pd.read_csv(input_path)

    print("\nExtracting GPS coordinates...")

    df["lat_long"] = df[address_col].progress_apply(extract_lat_long)

    # Handle None values safely
    df["latitude"] = df["lat_long"].apply(lambda x: x[0] if isinstance(x, list) else None)
    df["longitude"] = df["lat_long"].apply(lambda x: x[1] if isinstance(x, list) else None)

    df.drop(columns=["lat_long"], inplace=True)

    df.to_csv(output_path, index=False)
    print(f"\nDone! Saved output to: {output_path}")


def fill_missing_coordinates(csv_path, address_col, max_loops=10):

    csv_path = Path(csv_path)

    for loop in range(1, max_loops + 1):
        df = pd.read_csv(csv_path)

        # Identify missing lat/long
        missing_mask = df["latitude"].isna() | df["longitude"].isna()
        missing_count = missing_mask.sum()

        if missing_count == 0:
            print(f"\nNo missing coordinates left. All done after {loop-1} loops!")
            return

        print(f"\nLoop {loop}: {missing_count} rows still missing coords...")

        fixed_this_round = 0

        for idx in tqdm(df[missing_mask].index, total=missing_count):
            addr = df.at[idx, address_col]
            result = extract_lat_long(addr)

            if isinstance(result, list):
                df.at[idx, "latitude"] = result[0]
                df.at[idx, "longitude"] = result[1]
                fixed_this_round += 1

        df.to_csv(csv_path, index=False)
        print(f" → Loop {loop} fixed {fixed_this_round} rows.")

        # # Safety: stop if no progress is being made
        # if fixed_this_round == 0:
        #     print("\nStopping because no new coordinates were resolved this round.")
        #     print("Some addresses may simply be ungeocodable.")
        #     return

    print(f"\nStopped after max_loops={max_loops}. Some rows may still be missing.")


def fill_missing_coordinates_with_full_address(
    csv_path,
    address_col="Address",
    city_state_col="City State",
    zip_col="ZIP",
    max_loops=3
):
    csv_path = Path(csv_path)

    for loop in range(1, max_loops + 1):
        df = pd.read_csv(csv_path)

        # Treat NaN, empty string, and "Not found" as missing
        lat_str = df["latitude"].astype(str).str.strip().str.lower()
        lon_str = df["longitude"].astype(str).str.strip().str.lower()

        missing_mask = (
            df["latitude"].isna()
            | df["longitude"].isna()
            | lat_str.isin(["", "nan", "not found"])
            | lon_str.isin(["", "nan", "not found"])
        )
        missing_count = missing_mask.sum()

        if missing_count == 0:
            print(f"\nNo missing coordinates left. All done after {loop-1} loops!")
            return

        print(f"\nFull-address loop {loop}: {missing_count} rows still missing coords...")

        fixed_this_round = 0

        for idx in tqdm(df[missing_mask].index, total=missing_count):
            street = str(df.at[idx, address_col]).strip()
            city_state = str(df.at[idx, city_state_col]).strip()

            zip_val = ""
            if zip_col in df.columns:
                raw_zip = df.at[idx, zip_col]
                if pd.notna(raw_zip):
                    # Handle float ZIPs like 60002.0 → "60002"
                    try:
                        zip_val = str(int(raw_zip))
                    except Exception:
                        zip_val = str(raw_zip).strip()

            # Build full address: "street, city_state [ZIP]"
            parts = [street, city_state]
            if zip_val:
                parts.append(zip_val)
            full_addr = ", ".join(parts)

            result = extract_lat_long(full_addr)

            if isinstance(result, list):
                df.at[idx, "latitude"] = result[0]
                df.at[idx, "longitude"] = result[1]
                fixed_this_round += 1

        df.to_csv(csv_path, index=False)
        print(f" → Full-address loop {loop} fixed {fixed_this_round} rows.")

        # # Safety: stop if we didn't fix anything this round
        # if fixed_this_round == 0:
        #     print("\nStopping: no new coordinates resolved using full addresses.")
        #     print("Remaining rows are probably not geocodable with Nominatim.")
        #     return

    print(f"\nStopped after max_loops={max_loops}. Some rows may still be missing.")


# -----------------------------
# Geocode Functions (Manual)
# -----------------------------
def export_missing_for_manual(csv_path, output_path):
    df = pd.read_csv(csv_path)

    lat_str = df["latitude"].astype(str).str.strip().str.lower()
    lon_str = df["longitude"].astype(str).str.strip().str.lower()

    missing = (
        df["latitude"].isna()
        | df["longitude"].isna()
        | lat_str.isin(["", "not found", "nan"])
        | lon_str.isin(["", "not found", "nan"])
    )

    missing_df = df[missing].copy()
    missing_df.to_csv(output_path, index=False)

    print(f"\n Exported {missing.sum()} unresolved rows to:\n   → {output_path}\n")


def merge_manual_fixes(main_csv, manual_csv, output_csv):
    main = pd.read_csv(main_csv)
    manual = pd.read_csv(manual_csv)

    KEY_COLS = ["Name", "Address", "City State", "ZIP"]

    manual_small = manual[KEY_COLS + ["latitude", "longitude"]].copy()
    manual_small = manual_small.rename(
        columns={"latitude": "lat_manual", "longitude": "lon_manual"}
    )

    merged = main.merge(manual_small, on=KEY_COLS, how="left")

    for col in ["latitude", "longitude"]:
        merged[col] = merged[f"{col[:3]}_manual"].where(
            merged[f"{col[:3]}_manual"].notna(), merged[col]
        )
        merged.drop(columns=[f"{col[:3]}_manual"], inplace=True)

    merged.to_csv(output_csv, index=False)
    print(f"\n✓ Manual fixes merged into:\n   → {output_csv}")






# -----------------------------
# Driver Script
# -----------------------------
if __name__ == "__main__":
    MODULE_DIR = Path(__file__).resolve().parent
    DATA_DIR = MODULE_DIR / "dataIL"

    INPUT = DATA_DIR / "MHVillage_IL_Parks.csv"
    OUTPUT = DATA_DIR / "MHVillage_IL_Parks_coordinated.csv"
    MANUAL_FILE = DATA_DIR / "MHVillage_manual_fix.csv"

    # 1) First pass
    # get_coordinates(INPUT, OUTPUT, "Address")

    # # 2) Retry missing (same address)
    # fill_missing_coordinates(OUTPUT, "Address", max_loops=3)

    # # 3) Retry missing (full address)
    # fill_missing_coordinates_with_full_address(OUTPUT, "Address", "City State", "ZIP", max_loops=3)

    # 4) Export remaining missing for manual correction
    # export_missing_for_manual(OUTPUT, MANUAL_FILE)

    # print("\n Please fill missing lat/lon manually in:")
    # print(f"   {MANUAL_FILE}")
    # print("   Then re-run merge_manual_fixes() to finalize the dataset.\n")

    # 5) When manual edits done — merge back into the SAME geocoded CSV
    merge_manual_fixes(OUTPUT, MANUAL_FILE, OUTPUT)
