#!/usr/bin/env python3
"""
Script to calculate the best target to observe given some information.
"""
from datetime import datetime, date

import pandas as pd
import numpy as np


def order_by_best_target(
        target_table,
        observation_date,
        observatory_latitude,
        filters,
        desired_columns,
        delta_to_sun,
        n=15
        ):
    """
    Script that takes an input table of objects containing astronomical objects
    with a column RA and DEC.
    """

    # Put observation date into datetime
    observation_date_dt = datetime.strptime(observation_date, "%Y-%m-%d").date()

    # Define autumn_equinox date (on Brazil) on which sun's RA on midnight is zero
    autumn_equinox = datetime(year=observation_date_dt.year, month=3, day=20).date()

    # Define autumn_equinox date delta
    delta = (observation_date_dt - autumn_equinox).days

    # Calculate sun's RA (difference in day times the sun's increment
    sun_RA = delta*(360/365)

    target_table["delta_sun_RA"] = (target_table["RA"] - sun_RA)/15
    target_table["abs_delta_sun_RA"] = abs(target_table["delta_sun_RA"])
    target_table["abs_delta_sun_RA_floor"] = np.floor(abs(target_table["abs_delta_sun_RA"] - delta_to_sun))
    target_table["abs_delta_dec_lat"] = abs(target_table["DEC"] - observatory_latitude)

    target_table.sort_values(by=["abs_delta_sun_RA_floor", "abs_delta_dec_lat"], inplace=True)


    target_table["abs_delta_sun_RA_floor"] = np.floor(abs(target_table["abs_delta_sun_RA"] - delta_to_sun))
    target_table["abs_delta_sun_RA_floor"] = target_table["abs_delta_sun_RA_floor"].fillna(99).astype(int)

    if filters:

        joined_filter = " & ".join([f"({filt})" for filt in filters])

        filtered = target_table.query(joined_filter)

        target_table = filtered

    desired_columns.extend(["abs_delta_sun_RA", "abs_delta_sun_RA_floor", "abs_delta_dec_lat"])
    final_result = target_table.head(n)[desired_columns]

    final_result = final_result.rename(columns={"abs_delta_sun_RA": "Delta_to_Sun", "abs_delta_sun_RA_floor": "Bin", "abs_delta_dec_lat": "Lat_to_Dec"})

    return final_result
    

def main():

    print(
    """
    Target Selector
    ---------------

    Utility program designed to facilitate target selection.
    """
    )

    OBS_LAT = float(input("Please, input the observatory latitude (in degrees, ex: 50.05): "))

    print()

    DATE = input("Please, input the observation date (as YYYY-MM-DD, ex: 2022-09-01) (leave blank for today): ")

    if not DATE:
        DATE = date.today().strftime("%Y-%m-%d") 

    N = int(input("Please, input how many object suggestions you want: "))

    print(
    """
    Which period of the night to observe:

    1. First half
    2. Second half
    3. Entire night
    """
    )

    PERIOD = int(input("Number: "))

    if PERIOD in [1, 2, 3]:
        DELTA = {1: 9, 2: 15, 3: 12}[PERIOD]
    else:
        print("Invalid option. Terminating.")
        return


    print(
    """
    Please select the kind of target:

    1. Variable star (GCVS 5.1)
    2. Stellar cluster (Cantat-Gaudin+2020)

    """
    )

    target_type = int(input("Number: "))

    if target_type == 1:

        FILE = "gcvs5_cleaned.csv"
        RA_label = "_RAJ2000"
        DEC_label = "_DEJ2000"
        desired_columns = ["name", "RA", "DEC", "magMax", "VarType", "Period", "Amplitude"] 

        mag_cut = float(input("Please enter the maximum magnitude: "))
        amp_cut = float(input("Please enter the minimum amplitude (in mag): "))
        period_cut = float(input("Please enter the maximum period (in days): "))
        
        FILTERS = [
                f"magMax <= {mag_cut}",
                f"Amplitude >= {amp_cut}",
                f"Period <= {period_cut}"
        ]

        target_table = pd.read_csv(FILE)
        target_table = target_table.rename(columns={RA_label: "RA", DEC_label: "DEC", "GCVS": "name"})


    elif target_type == 2:

        RA_label = "RA_ICRS"
        DEC_label = "DE_ICRS"
        FILE = "cantat-gaudin_2020.tsv"
        desired_columns = ["name", "RA", "DEC", "nbstars07", "r50"]

        min_stars = int(input("Please enter the minimum number of stars: "))
        max_radii = float(input("Please enter the maximum radius for half of the stars (in arcmin): "))

        max_radii /= 60


        FILTERS = [ 
                f"nbstars07 >= {min_stars}",
                f"r50 <= {max_radii}"
        ]

        target_table = pd.read_csv(FILE, delimiter="|")
        target_table = target_table.rename(columns={RA_label: "RA", DEC_label: "DEC", "Cluster": "name"})


    else:
        print(f"Invalid option: {target_type}")
        return

    result = order_by_best_target(target_table, DATE, OBS_LAT, FILTERS, desired_columns, DELTA, N)

    print("\n\n RESULT - FULL INFO \n\n")
    print(result)

    print("\n\n RESULT - Catserver friendly \n\n")
    cat = (result.name.str.strip().str.replace(" ", "_") + " " + result.RA.astype(str) + " " + result.DEC.astype(str))

    for i in cat:
        print(i)


if __name__ == "__main__":
    main()
