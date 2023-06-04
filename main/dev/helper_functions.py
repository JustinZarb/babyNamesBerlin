"""Functions for BabyNamesBerlin

Returns:
    _type_: _description_
"""

import streamlit as st
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
    else:
        names = pd.read_csv(os.path.join(year_path, f"{kiez}.csv"))
        kiez = kiez[:-4]

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

    if write_csv:
        csv_path = (
            pathlib.Path(__file__) / ".." / ".." / ".." / "data" / "all_names.csv"
        ).resolve()
        all_names.to_csv(csv_path)

    return all_names


def kiez_selector(baby_names: pd.DataFrame, kiez_names: list, first_name_only=True):
    """Select Kiez
    If "all" is selected, the name "all" is passed but all names are printed

    Args:
        kiez_names (_type_): selector for berlin kiez names

    Returns:
        pd.DataFrame: for all berlin or selected kiez
    """

    all_option = "select all"
    # Get user's selections
    selected_kiez = st.multiselect(
        "Kiez (ignore to look at all of Berlin)",
        options=[all_option] + kiez_names,
        default=all_option,
    )

    if all_option in selected_kiez:
        # st.write(" | ".join(kiez_names))
        selection = (
            baby_names.groupby(["vorname", "geschlecht", "position", "jahr", "kiez"])
            .sum()
            .reset_index()
            .sort_values(by="anzahl", ascending=False)
        )

    else:
        st.write(" | ".join(selected_kiez))
        selection = baby_names[baby_names["kiez"].isin(selected_kiez)].sort_values(
            by="anzahl", ascending=False
        )

    if first_name_only:
        selection.drop("position", axis=1, inplace=True)
    return selection


def filter_gender(names: pd.DataFrame):
    gender = st.radio("Registered gender", ["all", "girls", "boys"])
    if gender == "girls":
        selection = names.loc[names.loc[:, "geschlecht"] == "w", :]
    elif gender == "boys":
        selection = names.loc[names.loc[:, "geschlecht"] == "m", :]
    else:
        selection = names
    return selection


def name_search(names: pd.DataFrame, kiez_names: list):
    """Search the list for names
    #Todo:
    - filter by kiez

    Args:
        names (pd.DataFrame): _description_
    """

    st.header("Search for a name")
    all_option = "select all"
    options = [all_option] + list(
        names.sort_values("vorname").loc[:, "vorname"].unique()
    )

    name_selection = st.multiselect(
        "Name: ",
        options=options,
        default=all_option,
    )
    name_selection = [s.lower() for s in name_selection]

    # first name only
    first_name_only = st.checkbox(
        "First names only (all names will be used for 2012-2016)", value=True
    )
    if first_name_only:
        selection = names.loc[baby_names.loc[:, "position"] == 1, :]
    else:
        selection = names

    # select gender
    selection = filter_gender(selection)

    # Select
    if all_option not in name_selection:
        selection = selection.loc[
            selection.loc[:, "vorname"].str.lower().isin(name_selection), :
        ].sort_values(by="anzahl")

    selection = kiez_selector(selection, kiez_names, first_name_only)

    return selection


def to_timeseries(names: pd.DataFrame):
    # embed gender in name
    names["vorname_"] = names.loc[:, "vorname"] + "_" + names.loc[:, "geschlecht"]

    if "position" in names.columns:
        # add positional name
        names["vorname_"] = (
            names.loc[:, "vorname_"] + "_" + names.loc[:, "position"].astype(str)
        )
        names.drop("position", axis=1, inplace=True)

    names_ts = names.pivot_table(index="vorname", columns="jahr", values="anzahl")
    names_ts = names_ts.sort_values(by=2022, ascending=False).head(30).T
    names_ts.index = pd.to_datetime(names_ts.index, format="%Y").strftime("%Y")
    names_ts = names_ts.fillna(0).astype(int).sort_index(ascending=False)

    return names_ts


def names_by_kiez(names):
    """Plots a map of berlin with the popular names every year

    Args:
        names (_type_): _description_
    """
    pass
