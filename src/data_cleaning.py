# Author: Nico Van den Hooff <www.nicovandenhooff.com>
# License: MIT License

"""
Cleans the scraped repo and user data from Github.

Usage:
    data_cleaning.py [options]
    data_cleaning.py (-h | --help)

Options:
    -h --help                       Show this screen.
    -i <path> --input_path=<path>   The input file path for the raw scraped data. [default: data/scraped/]
    -o <path> --output_path=<path>  The output file path to save the cleaned data. [default: data/cleaned/]
"""

import os
import numpy as np
import pandas as pd
from docopt import docopt
from functools import partial
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


def clean_repo_data(df):
    """Cleans repo data scraped from Github.

    Parameters
    ----------
    df : pandas DataFrame
        The raw data to clean.

    Returns
    -------
    pandas DataFrame
        The cleaned data.
    """
    types = {
        "repo_name": "str",
        "full_name": "str",
        "description": "str",
        "language": "str",
        "type": "str",
        "username": "str",
    }

    # set string types and reset nans
    clean_df = df.astype(types).replace("nan", np.nan)

    # remove new lines and carriage returns in descriptions
    clean_df["description"] = clean_df["description"].str.replace(
        r"\r|\n", "", regex=True
    )

    # clean up lists of topics
    clean_df["topics"] = (
        clean_df["topics"].apply(eval).apply(lambda x: x if x else np.nan)
    )

    # drop any duplicates from scrape
    clean_df = clean_df.drop_duplicates(subset="id", keep=False)

    return clean_df


def clean_user_data(df):
    """Cleans user data scraped from Github.

    Parameters
    ----------
    df : pandas DataFrame
        The raw data to clean.

    Returns
    -------
    pandas DataFrame
        The cleaned data.
    """

    # difference is that user data does not contain "topics"
    types = {
        "username": "str",
        "name": "str",
        "type": "str",
        "bio": "str",
        "company": "str",
        "email": "str",
        "location": "str",
    }

    # set string types and reset nans
    clean_df = df.astype(types).replace("nan", np.nan)

    # remove new lines and carriage returns in bios
    clean_df["bio"] = clean_df["bio"].str.replace(r"\r|\n", "", regex=True)

    # remove duplicate users, ensuring to keep one
    clean_df = clean_df.drop_duplicates(subset="id", keep="first")

    return clean_df


# TODO: clean up file names with raw for scraped data
def clean_data(input_path, output_path):
    """Cleans user and repo data scraped from github.

    Parameters
    ----------
    input_path : str
        The input file path for the raw scraped data.
    output_path : str
        The output file path to save the cleaned data.
    """

    for filename in os.listdir(input_path):
        f = os.path.join(input_path, filename)
        df = pd.read_csv(f, parse_dates=["created"])

        if "user-data" in f:
            clean_df = clean_user_data(df)
            clean_df.to_csv(f"{output_path}{filename}", index=False)

            location_df = create_location_df(clean_df)
            location_df.to_csv(f"{output_path}user-location-data.csv", index=False)

        else:
            clean_df = clean_repo_data(df)
            clean_df.to_csv(f"{output_path}{filename}", index=False)


def create_location_df(df):
    """Creates a dataframe containing detailed geolocation information.

    Parameters
    ----------
    df : pandas DataFrame
        The dataframe to add geolocation information too.

    Returns
    -------
    pandas DataFrame
        The new dataframe that contains detailed geolocation data.
    """
    url = "https://raw.githubusercontent.com/dbouquin/IS_608/master/NanosatDB_munging/Countries-Continents.csv"
    continents_df = pd.read_csv(url, names=["continent", "country"], header=0)

    missing_countries = pd.DataFrame(
        [["Asia", "Taiwan"], ["Africa", "Eswatini"]], columns=["continent", "country"]
    )
    continents_df = continents_df.append(missing_countries, ignore_index=True)

    location_df = df.copy().dropna(subset=["location"])

    # these values caused exceptions in the location scrape, it's not necessary to
    # remove them but it's cleaner as it avoids the printing of errors to the console.
    error_inducing = ["Armonk, New York, U.S.", "School 42 Paris, France", "微博：迪哥有点愁"]
    location_df = location_df.query("location not in @error_inducing")

    geolocator = Nominatim(user_agent="github-analysis")

    # allows locator to return all address details and returned results are in english
    geocode = partial(geolocator.geocode, addressdetails=True, language="en")

    # avoids rate limiting for Nominatim (1 request per second)
    geocode = RateLimiter(geocode, min_delay_seconds=1, max_retries=0)

    # gets detailed location data and drops repos without any data
    location_df["geo-location"] = location_df["location"].apply(geocode)
    location_df = location_df.dropna(subset=["geo-location"])

    # adds columns to data for visualization
    location_df["latitude"] = location_df["geo-location"].apply(
        lambda x: x.latitude if x else None
    )
    location_df["longitude"] = location_df["geo-location"].apply(
        lambda x: x.longitude if x else None
    )
    location_df["country"] = location_df["geo-location"].apply(
        lambda x: x.raw["address"]["country"] if x else None
    )

    # adds continents since geopy doesn't return continent values
    to_replace = ["United States", "South Korea", "Russia", "Czechia"]
    replace_with = ["US", "Korea, South", "Russian Federation", "CZ"]
    location_df = location_df.replace(to_replace, value=replace_with)
    location_df = location_df.merge(continents_df, on="country", how="left")

    return location_df


def main(input_path, output_path):
    """Main function that performs the data cleaning"""
    clean_data(input_path, output_path)


if __name__ == "__main__":
    print("--Data cleaning starting")
    opt = docopt(__doc__)
    main(opt["--input_path"], opt["--output_path"])
    print("--Data cleaning complete")
