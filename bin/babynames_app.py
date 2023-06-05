import streamlit as st
import pandas as pd
import dev.streamlit_helper_functions as sf


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    # Get data
    url = "https://raw.githubusercontent.com/JustinZarb/babyNamesBerlin/master/data/names_combined_features.csv"

    def page_1():
        st.title("Berlin's Baby Names")
        st.markdown(
            """Explore Berlin's most popular open dataset: annual baby name data between 2012 and 2022. Data source: https://github.com/berlinonline/haeufige-vornamen-berlin """
        )

        baby_names = pd.read_csv(url)
        # baby_names = sf.first_names_only(baby_names)

        baby_names = sf.name_position_radio(baby_names)
        baby_names = sf.filter_gender(baby_names)

        kiez_selection = sf.kiez_selector(baby_names)
        name_selection = sf.name_selector(baby_names)

    def page_2():
        st.title("Exploring associated gender")
        baby_names = pd.read_csv(url)
        sf.gender_viz1(baby_names)

    def page_3():
        st.title("A deep dive into names")
        st.text("Let's look at different kinds of name similarity")

        baby_names = pd.read_csv(url)
        baby_names = sf.first_names_only(baby_names)

        sf.similar_names(baby_names)

    def page_4():
        st.title("Predicting this year's names")

    pages = {
        "Home": page_1,
        "Genders": page_2,
        "Names": page_3,
        # "Forecast": page_4,
    }

    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    pages[selection]()
