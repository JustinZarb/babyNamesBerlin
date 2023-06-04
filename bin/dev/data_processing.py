"""Functions for BabyNamesBerlin

Returns:
    _type_: _description_
"""
import pandas as pd
import os
import pathlib


def get_kiez_files():
    names_2012 = (
        pathlib.Path(__file__) / ".." / ".." / ".." / "data" / "cleaned" / "2012"
    ).resolve()
    year_file_names = os.listdir(names_2012)
    return year_file_names


def get_names(year: int, kiez: str):
    """imports the baby names file for a given year and kiez as baby names

    Args:
        year (int): year of baby names
        kiez (str): berlin kiez name

    Returns:
        names (pd.DataFrame): a dataframe with the imported csv and some added columns
    """
    data_path = (
        pathlib.Path(__file__) / ".." / ".." / ".." / "data" / "cleaned"
    ).resolve()

    year_path = os.path.join(data_path, str(year))
    if kiez.endswith(".csv"):
        names = pd.read_csv(os.path.join(year_path, kiez))
        kiez = kiez[:-4]
    else:
        names = pd.read_csv(os.path.join(year_path, f"{kiez}.csv"))

    names.sort_values(by="anzahl", ascending=False)
    names["anzahl"] = names["anzahl"].astype("int16")

    if "position" in names.columns:
        names["position"] = names["position"].astype("int8", errors="ignore")
    else:
        names["position"] = 1
    # add kiez and year as columns
    names.loc[:, "jahr"] = year
    names.loc[:, "kiez"] = kiez

    return names


def get_names_all(write_csv: bool = False):
    all_names = pd.DataFrame()
    kiez_file_names = get_kiez_files()
    for year in range(2012, 2023):
        for kiez in kiez_file_names:
            n = get_names(year, kiez)
            all_names = pd.concat([all_names, n])
    all_names = all_names.loc[:, ~all_names.columns.str.contains("^Unnamed")]
    all_names = all_names.loc[~all_names.loc[:, "vorname"].str.contains("\)"), :]
    all_names = all_names.loc[~all_names.loc[:, "vorname"].str.contains("-"), :]

    if write_csv:
        csv_path = (
            pathlib.Path(__file__)
            / ".."
            / ".."
            / ".."
            / "data"
            / "names_combined_raw.csv"
        ).resolve()
        all_names.to_csv(csv_path)

    return all_names


def combine_vorname_geschlecht_position(names: pd.DataFrame):
    """Creates the "vorname_" column with gender and position encoded

    Args:
        names (_type_): _description_

    Returns:
        pd.DataFrame: input df with an extra "vorname_" column
    """
    # embed gender in name
    names["vorname_"] = names.loc[:, "vorname"] + "_" + names.loc[:, "geschlecht"]

    if "position" in names.columns:
        # add positional name
        names["vorname_"] = (
            names.loc[:, "vorname_"] + "_" + names.loc[:, "position"].astype(str)
        )

    return names


def add_gender_scale_unisex_score(names: pd.DataFrame):
    """Add a gender scale and unisex score

    unisex scale: 0% unisex to 100% unisex
    gender score: 0 if male, 1 if female
    gender category: 5 categories based on gender score
    Args:
        names (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: input df with "unisex_score" and "gender_scale" columns
    """
    # First, calculate the total 'anzahl' for each name and gender
    totals = names.groupby(["vorname", "geschlecht"])["anzahl"].sum()

    unisex_scores = {}
    gender_scale = {}
    for name in totals.index.get_level_values("vorname").unique():
        name_totals = totals[name]

        if ("m" in name_totals) and ("w" in name_totals):
            score = min(name_totals) / max(name_totals)
            scale = name_totals["w"] / name_totals.sum()
        elif "m" in name_totals:
            score = 0
            scale = 0
        elif "w" in name_totals:
            score = 0
            scale = 1

        unisex_scores[name] = score
        gender_scale[name] = scale

    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = [
        "Predominantly Male",
        "Male-leaning Unisex",
        "True Unisex",
        "Female-leaning Unisex",
        "Predominantly Female",
    ]

    # Apply the unisex scores to the DataFrame
    names["unisex_score"] = names["vorname"].map(unisex_scores)
    names["unisex_score"] = names["unisex_score"].astype("float16")
    names["gender_scale"] = names["vorname"].map(gender_scale)
    names["gender_scale"] = names["gender_scale"].astype("float16")
    names["gender_category"] = pd.cut(names["gender_scale"], bins=bins, labels=labels)
    return names


def add_rank(names: pd.DataFrame):
    return names


def add_features(names: pd.DataFrame, write_csv: bool = False):
    names = combine_vorname_geschlecht_position(names)
    names = add_gender_scale_unisex_score(names)

    if write_csv:
        csv_path = (
            pathlib.Path(__file__)
            / ".."
            / ".."
            / ".."
            / "data"
            / "names_combined_features.csv"
        ).resolve()
        names.to_csv(csv_path)

    return names
