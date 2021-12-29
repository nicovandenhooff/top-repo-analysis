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
        else:
            clean_df = clean_repo_data(df)
            clean_df.to_csv(f"{output_path}{filename}", index=False)


def main(input_path, output_path):
    """Main function that performs the data cleaning"""
    clean_data(input_path, output_path)


if __name__ == "__main__":
    opt = docopt(__doc__)
    main(opt["--input_path"], opt["--output_path"])
