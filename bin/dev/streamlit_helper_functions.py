import streamlit as st
import plotly.figure_factory as ff
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Levenshtein import distance
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def filter_gender(names: pd.DataFrame):
    gender = st.radio("Registered gender", ["all", "girls", "boys"])
    if gender == "girls":
        selection = names.loc[names.loc[:, "geschlecht"] == "w", :]
    elif gender == "boys":
        selection = names.loc[names.loc[:, "geschlecht"] == "m", :]
    else:
        selection = names
    return selection


def first_names_only(names: pd.DataFrame, remove_pre_2016=False):
    # first name only
    first_name_only = st.checkbox(
        "First names only (all names will be used for 2012-2016)", value=True
    )

    if first_name_only:
        names = names.loc[names.loc[:, "position"] == 1, :]
        if remove_pre_2016:
            names = names.loc[names.loc[:, "jahr"] <= 2016]

    return names


def name_position_radio(names: pd.DataFrame):
    positions = [1, 2, 3, 4, 5, 6]
    position = st.select_slider(
        "Name position. Default is 'All' to include data between 2012 and 2016",
        ["All"] + positions,
        value="All",
    )
    if position is not "All":
        names = names.loc[names.loc[:, "position"] == int(position), :]
        names = names.loc[names.loc[:, "jahr"] > 2016]
    return names


def plot_name_heatmap(df):
    df = df.groupby(["kiez", "jahr"]).sum().sort_values("anzahl")

    pivot_table = pd.pivot_table(
        df, values="anzahl", index="kiez", columns="jahr", fill_value=0
    ).astype("int")

    sorted_pivot_table = pivot_table.sort_values(by=pivot_table.columns.tolist())

    fig = ff.create_annotated_heatmap(
        z=sorted_pivot_table.values,
        x=list(sorted_pivot_table.columns),
        y=list(sorted_pivot_table.index),
        colorscale="jet",
        showscale=True,
    )

    fig.update_layout(title="Name counts*", xaxis_title="Year", yaxis_title="Kiez")

    st.plotly_chart(fig, use_container_width=True)


def multiselect_names(names: pd.DataFrame):
    name_list = list(names.sort_values("vorname").loc[:, "vorname"].unique())
    name_selection = st.multiselect(
        "Enter a name: ",
        options=name_list,
    )
    if len(name_selection) == 0:
        name_selection = name_list
    return name_selection


def name_selector(names: pd.DataFrame):
    names_subset = names.loc[:, ["vorname_", "kiez", "geschlecht", "jahr", "anzahl"]]
    names_subset["vorname"] = names_subset["vorname_"].apply(lambda x: x.split("_")[0])
    name_list = multiselect_names(names_subset)
    selection = names_subset.loc[names_subset.loc[:, "vorname"].isin(name_list), :]

    # Plot heatmap
    plot_name_heatmap(selection)
    return selection


def kiez_selector(names: pd.DataFrame):
    """Select Kiez
    Plot something

    Args:
        kiez_names (_type_): selector for berlin kiez names

    Returns:
        pd.DataFrame: for all berlin or selected kiez
    """
    names_subset_kiez = names.loc[
        :, ["vorname_", "kiez", "geschlecht", "jahr", "anzahl"]
    ]
    names_subset_kiez["vorname"] = names_subset_kiez["vorname_"].apply(
        lambda x: x.split("_")[0]
    )
    kiez_names = list(names_subset_kiez.loc[:, "kiez"].unique())

    # Get user's selections
    selected_kiez = st.multiselect("Filter by Kiez:", kiez_names)
    if selected_kiez == []:
        selected_kiez = kiez_names

    selection = names_subset_kiez[
        names_subset_kiez["kiez"].isin(selected_kiez)
    ].sort_values(by="anzahl", ascending=False)

    if len(selected_kiez) == 1:
        kiez_str = selected_kiez[0]
    elif len(selected_kiez) == 12:
        kiez_str = "Berlin"
    else:
        kiez_str = ", ".join(selected_kiez[:-1]) + f" and {selected_kiez[-1]}"

    selection = (
        selection.drop("kiez", axis=1)
        .groupby(["vorname", "geschlecht", "jahr"])
        .sum()
        .reset_index()
        .sort_values(by="anzahl", ascending=False)
    )

    kiez_selection_to_timeseries(selection, kiez_str)

    return selection


def kiez_selection_to_timeseries(names: pd.DataFrame, kiez_string):
    """Generate a name count timeseries for visualization

    Args:
        names (pd.DataFrame): Takes the names dataframe, with or without 'kiez' information

    Returns:
        _type_: _description_
    """

    names_ts = names.pivot_table(index="vorname", columns="jahr", values="anzahl")
    names_ts = names_ts.sort_values(by=2022, ascending=False).head(30).T  # .astype(int)
    names_ts.index = pd.to_datetime(names_ts.index, format="%Y").strftime("%Y")
    names_ts = names_ts.fillna(0).astype(int).sort_index(ascending=True)

    fig = px.line(names_ts, title=f"{kiez_string}'s top 30 names in 2022")
    st.plotly_chart(fig, use_container_width=True)


def gender_viz1(names):
    df = names.copy()

    # Start streamlit app
    st.header("Gender Visualization")
    st.markdown(
        "Using the assigned gender at birth, it is possible to assign a 'unisex score' to the names, where a score of 0 means the name was only assigned to either males or females, while 1 was assigned equally to males and females. This has no connection to the chosen gender of the individual. The following graphs represent the entire dataset (2012-2022)."
    )

    # Select name position
    df = name_position_radio(df)
    # Calculate the gender score bins
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = [
        "Predominantly Male",
        "Male-leaning Unisex",
        "True Unisex",
        "Female-leaning Unisex",
        "Predominantly Female",
    ]
    df["gender_category"] = pd.cut(df["gender_scale"], bins=bins, labels=labels)

    # Calculate the number of names in each gender score bin
    bin_counts = df["gender_category"].value_counts().sort_index()

    # Plot the histogram of names per bin
    hist_fig = px.bar(
        x=labels,
        y=bin_counts,
        labels={"x": "Gender Score Range", "y": "Number of Names"},
        title="Number of Names per Gender Score Range",
    )
    st.plotly_chart(hist_fig, use_container_width=True)

    # Let the user select a gender score bin
    selected_category = st.select_slider(
        "Select a Gender Score Range", labels, value="True Unisex"
    )

    # Filter the DataFrame for names within the selected gender score bin
    df_category = df[df["gender_category"] == selected_category]

    # Aggregate the filtered DataFrame by name (taking the sum of 'anzahl')
    df_category = (
        df_category.groupby("vorname")
        .agg(
            {
                "anzahl": "sum",
                "gender_scale": "mean",
                "unisex_score": "mean",
            }
        )
        .reset_index()
        .sort_values(["gender_scale"], ascending=[True])
    )

    # Create a bar plot with names on x-axis and 'anzahl' on y-axis
    # Colors are set based on 'gender_scale'
    fig = px.bar(
        df_category,
        x="vorname",
        y="anzahl",
        color="gender_scale",
        labels={"anzahl": "Total Count"},
        color_continuous_scale=px.colors.sequential.RdBu_r,
        color_continuous_midpoint=0.5,
        title=f"Names in Gender Score Range: {selected_category}",
    )
    fig.update_coloraxes(cmin=0, cmax=1)
    fig.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=1.5)

    # Define function to get names above a certain percentile within each gender category
    def get_outliers_in_category(group):
        threshold = group["anzahl"].quantile(0.98)  # 98th percentile within each group
        show_labels = group[group["anzahl"] > threshold]
        if len(show_labels) > 50:
            threshold = group["anzahl"].quantile(
                0.9995
            )  # 99.95th percentile within each group
            show_labels = group[group["anzahl"] > threshold]
        return show_labels

    # Get outliers within the selected gender score bin
    outliers = get_outliers_in_category(df_category)

    # Add text labels for outlier names
    for i, row in outliers.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["vorname"]],
                y=[row["anzahl"]],
                text=[row["vorname"]],
                mode="text",
                showlegend=False,
            )
        )

    fig.update_traces(
        hovertemplate="Name: %{x}<br>Total Count: %{y}<br>Unisex Score: %{customdata[0]:.2f}<br>Gender Scale: %{customdata[1]:.2f}",
        customdata=df_category[["unisex_score", "gender_scale"]].values,
    )

    st.plotly_chart(fig, use_container_width=True)


def gender_viz2(names):
    df = names.copy()

    # Start streamlit app
    st.header("Gender Visualization")

    # Let the user select a score range
    score_range = st.slider(
        "Associated gender range",
        min_value=0.0,
        max_value=1.0,
        value=(0.25, 0.75),  # the initial range
        step=0.01,
    )

    # Filter the DataFrame for names within the selected score range
    df_category = df[
        (df["gender_scale"] >= score_range[0]) & (df["gender_scale"] <= score_range[1])
    ]

    # Create a histogram of the number of names per bin
    fig_hist = px.histogram(
        df_category,
        x="gender_scale",
        nbins=20,
        labels={"gender_scale": "Gender Scale", "count": "Number of Names"},
        title="Distribution of Names by Gender Scale",
        color_discrete_sequence=["#1f77b4"],
        opacity=0.8,
    )
    fig_hist.update_layout(
        xaxis={"title": "Gender Scale"},
        yaxis={"title": "Number of Names"},
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # Aggregate the filtered DataFrame by name (taking the sum of 'anzahl')
    df_category = (
        df_category.groupby("vorname")
        .agg(
            {
                "anzahl": "sum",
                "gender_scale": "mean",
                "unisex_score": "mean",
            }
        )
        .reset_index()
        .sort_values(["gender_scale"], ascending=[True])  # Sort by gender scale
    )

    # Create a bar plot with names on x-axis and 'anzahl' on y-axis
    # Colors are set based on 'gender_scale'
    fig_bar = px.bar(
        df_category,
        x="vorname",
        y="anzahl",
        color="gender_scale",
        labels={"anzahl": "Total Count"},
        color_continuous_scale=px.colors.sequential.RdBu_r,
        color_continuous_midpoint=0.5,
        title=f"Names in gender range {score_range}",
    )
    fig_bar.update_coloraxes(cmin=0, cmax=1)
    fig_bar.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=1.5)

    # Define function to get names above a certain percentile within each gender category
    def get_outliers_in_category(group):
        threshold = group["anzahl"].quantile(0.98)  # 98th percentile within each group
        show_labels = group[group["anzahl"] > threshold]
        if len(show_labels) > 50:
            threshold = group["anzahl"].quantile(
                0.9995
            )  # 99.95th percentile within each group
            show_labels = group[group["anzahl"] > threshold]
        return show_labels

    # Get outliers within the filtered names
    outliers = get_outliers_in_category(df_category)

    # Add text labels for outlier names
    for i, row in outliers.iterrows():
        fig_bar.add_trace(
            go.Scatter(
                x=[row["vorname"]],
                y=[row["anzahl"]],
                text=[row["vorname"]],
                mode="text",
                showlegend=False,
            )
        )

    fig_bar.update_traces(
        hovertemplate="Name: %{x}<br>Total Count: %{y}<br>Unisex Score: %{customdata[0]:.2f}<br>Gender Scale: %{customdata[1]:.2f}",
        customdata=df_category[["unisex_score", "gender_scale"]].values,
    )

    st.plotly_chart(fig_bar, use_container_width=True)


def levenshtein_similarity(name, names, n=10):
    """Find the `n` names most similar to `name` based on Levenshtein distance."""
    distances = [(other_name, distance(name, other_name)) for other_name in names]
    distances.sort(key=lambda x: x[1])
    return {
        name: dist for name, dist in distances[:n]
    }  # [name for name, dist in distances[:n]]


def plot_word_cloud(names):
    """Plot a word cloud from a list of names."""
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        " ".join(names)
    )
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot()


def similar_names(names: pd.DataFrame):
    names_subset = names.loc[:, ["vorname_", "kiez", "geschlecht", "jahr", "anzahl"]]
    names_subset["vorname"] = names_subset["vorname_"].apply(lambda x: x.split("_")[0])

    selected_names = multiselect_names(names)
    all_names = list(names_subset.sort_values("vorname").loc[:, "vorname"].unique())
    st.text([len(selected_names), len(names)])

    if len(selected_names) == 1:
        for n in selected_names:
            similar = levenshtein_similarity(n, all_names, n=20)
            st.text(f"Levenshtein similarity: {similar}")
