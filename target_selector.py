#!/usr/bin/env python3
"""
Script to calculate the best target (cluster or variable star) to observe given
the information input.

Usage
-----

Enter the program folder and type:

    $ python calc_target.py

The script will ask a sequence of questions to determine which targets to
suggest.

"""

from datetime import datetime, date
from functools import partial

import pandas as pd
import numpy as np


def get_neighbors(ra, dec, diameter, v_cut, catalog):
    """
    Given a position on the sky `ra, dec` find the neighboring stars inside a 
    `diameter` given in arc minutes to say if target has neighboring stars.

    Parameters
    ----------

    ra, dec: float
        sky position.

    diameter: float
        diameter of the observation field.

    v_cut: float
        cutting magnitude.

    catalog: pd.DataFrame
        catalog to search for neighbors

    Returns
    -------
        
        int
           Number of match neighbor stars minus 1 
    """
    
    ## Preparing input

    radius = diameter/2
    radius = radius/60  #  arcmin -> deg

    ## Making selection

    neighbors = (
          (catalog.RA > ra - radius) 
        & (catalog.RA < ra + radius) 
        & (catalog.DEC > dec - radius)
        & (catalog.DEC < dec + radius)
        & (catalog.Vmag < v_cut)
    )
    
    if neighbors.sum() >= 2:
        return neighbors.sum() - 1
    else:
        return 0


def get_neighbors_helper(getter_func):
    """Helper function easily apply neighbor getter function to pandas series"""
    def f(line):
        return getter_func(line["RA"], line["DEC"])
    return f


def order_by_best_target(
        target_table, observation_date, observatory_latitude, filters,
        desired_columns, delta_to_sun, n=15, neighbor_getter=None
    ):
    """
    Script that takes an input table of objects containing astronomical objects
    with a column RA and DEC.

    Parameters
    ----------

    target_table: pd.DataFrame
        Tables with columns for DEC and RA of a bunch of targets

    observation_date: str
        Desired observation date in ISO 8601 format

    observatory_latitude: float
        Observatory latitude in degrees

    filters: list of str
        List with strings applying filters on the columns of the dataframe
        accepts regular comparison operators (<, >, <=, !=, etc)

    desired_columns: list of str
        Strings with names of columns desired on the output

    delta_to_sun: float
        The number of hours of difference desired from the sun's RA

    n: int, default: 15
        number of desired targets

    neighbor_getter: callable
        function defining criteria to find neighbors

    Returns
    -------
        final_result: pd.DataFrame
            DataFrame with the `n` selected targets
    """

    # Put observation date into datetime
    observation_date_dt = datetime.strptime(observation_date, "%Y-%m-%d").date()

    # Define autumn_equinox date (on Brazil) on which sun's RA on midnight is zero
    autumn_equinox = datetime(year=observation_date_dt.year, month=3, day=20).date()

    # Define autumn_equinox date delta
    delta = (observation_date_dt - autumn_equinox).days

    # Calculate sun's RA (difference in day times the sun's increment
    sun_RA = delta*(360/365)

    # Calculating relevant features to calculate from
    target_table["delta_sun_RA"] = (target_table["RA"] - sun_RA)/15
    target_table["abs_delta_sun_RA"] = abs(target_table["delta_sun_RA"])
    target_table["abs_delta_sun_RA_floor"] = np.floor(abs(target_table["abs_delta_sun_RA"] - delta_to_sun))
    target_table["abs_delta_dec_lat"] = abs(target_table["DEC"] - observatory_latitude)

    target_table.sort_values(by=["abs_delta_sun_RA_floor", "abs_delta_dec_lat"], inplace=True)

    # Calculating bins
    target_table["abs_delta_sun_RA_floor"] = np.floor(abs(target_table["abs_delta_sun_RA"] - delta_to_sun))
    target_table["abs_delta_sun_RA_floor"] = target_table["abs_delta_sun_RA_floor"].fillna(99).astype(int)

    # Adding interesting features to the final column selection
    desired_columns.extend(["abs_delta_sun_RA", "abs_delta_sun_RA_floor", "abs_delta_dec_lat"])

    # Applying filters if there are filters
    if filters:
        # Building Query String from list of filters
        joined_filter = " & ".join([f"({filt})" for filt in filters])  
        target_table = target_table.query(joined_filter)

    # If a neighbor_getter function is given go through applying dataframe
    # applying it
    if neighbor_getter:

        neighbor = get_neighbors_helper(neighbor_getter)
        i = 0
        it = target_table.iterrows()
        with_neighbor = []
        counts = []

        while i < n:
            try:
                a, line = next(it)
                neighbor_count = neighbor(line)
                if neighbor_count:
                    with_neighbor.append(a)
                    counts.append(neighbor_count)
                    i += 1
            except StopIteration:  #  The iterator was exhausted
                print(f"Couldn't find the {n} targets")
                break

        
        final_result = target_table.loc[with_neighbor, desired_columns]
        final_result["n_neighbor"] = counts


    else:
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

    N = input("Please, input how many object suggestions you want (leave blank to default to 15): ")

    if not N:
        N = 15
    else:
        N = int(N)

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

    1. Variable star (GCVS 5.1 and Hipparco) 
    2. Stellar cluster (Cantat-Gaudin+2020)

    """
    )

    target_type = int(input("Number: "))

    if target_type == 1:

        # Catalog info
        FILE = "gcvs5_cleaned.csv"
        RA_label = "_RAJ2000"
        DEC_label = "_DEJ2000"
        desired_columns = ["name", "RA", "DEC", "magMax", "VarType", "Period", "Amplitude"] 

        # Taking inputs
        mag_cut = float(input("Please enter the maximum magnitude (in V): "))
        amp_cut = float(input("Please enter the minimum amplitude (in V): "))
        period_cut = float(input("Please enter the maximum period (in days): "))
        field_diameter = float(input("Please enter the FoV diameter (in arcmin): "))
        
        # Preparing filter strings
        FILTERS = [
                f"magMax <= {mag_cut}",
                f"Amplitude >= {amp_cut}",
                f"Period <= {period_cut}"
        ]

        # Preparing necessary tables
        target_table = pd.read_csv(FILE)
        target_table = target_table.rename(columns={RA_label: "RA", DEC_label: "DEC", "GCVS": "name"})

        neighbor_catalog = pd.read_csv("hipparco.csv")

        neighbor_getter = partial(
                get_neighbors, 
                diameter=field_diameter,
                v_cut=mag_cut,
                catalog=neighbor_catalog
                )

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
        neighbor_getter = None


    else:
        print(f"Invalid option: {target_type}")
        return


    result = order_by_best_target(
            target_table,
            DATE, 
            OBS_LAT, 
            FILTERS, 
            desired_columns, 
            DELTA, 
            N, 
            neighbor_getter=neighbor_getter
        )

    print("\n\n RESULT - FULL INFO \n\n")
    print(result.to_string(index=False))

    print("\n\n RESULT - Catserver friendly \n\n")
    cat = (result.name.str.strip().str.replace(" ", "_") + " " + result.RA.astype(str) + " " + result.DEC.astype(str))

    for i in cat:
        print(i)


if __name__ == "__main__":
    main()
