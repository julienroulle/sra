import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

LANCERS = ["javelot", "poids", "disque", "marteau"]
SAUTS = ["hauteur", "perche", "longueur"]


def show_results_page():
    st.title("Results")

    col1, col2 = st.columns([8, 1])

    with col1:
        url = st.text_input(
            "Base Athle URL",
            key="url",
            value="https://bases.athle.fr/asp.net/liste.aspx?frmbase=resultats&frmmode=1&frmespace=0&frmcompetition=304693",
        )
        url = url + "&frmposition={}"

    with col2:
        page_nb = st.number_input("Page nb", key="page_nb", step=1, value=5)

    if st.button("Process results"):
        df = pd.concat(
            [
                pd.read_html(url.format(i), skiprows=3 if i == 0 else 2)[0]
                for i in range(page_nb)
            ],
            ignore_index=True,
        )
        df = df.drop(columns=[0, 3, 5, 7, 8, 9, 10, 11, 12, 13, 15])
        df.columns = [
            "Discipline",
            "Performance",
            "Athlète",
            "Club",
            "Cotation",
            "Points",
        ]

        perfs = pd.DataFrame()

        sports = df.loc[df.Club.str.contains("Finale")]
        for idx in range(len(sports.index)):
            sport = df.iloc[sports.index[idx]].Club.split("|")[0]

            if idx == len(sports.index) - 1:
                results = df.iloc[sports.index[idx] + 1 :].copy()
            else:
                results = df.iloc[sports.index[idx] + 1 : sports.index[idx + 1]].copy()

            if "4 X" in sport:
                continue
            if (
                "Javelot" in sport
                or "Hauteur" in sport
                or "Perche" in sport
                or "Triple" in sport
                or "Longueur" in sport
                or "Poids" in sport
                or "Disque" in sport
                or "Marteau" in sport
            ):
                results = results.loc[~results.Performance.isna()]
            results["Discipline"] = [sport] * len(results)
            perfs = pd.concat([perfs, results], ignore_index=True)

        perfs_club = perfs.loc[
            perfs.Club.str.lower().str.startswith("stade rennais athletisme")
        ].copy()

        perfs_club.Points = perfs_club.Points.fillna(0)
        perfs_club.Points = perfs_club.Points.astype(int)

        perfs_club = perfs_club.drop(columns=["Cotation"])

        # Extract gender (assuming format "Event / G")
        perfs_club["Sexe"] = (
            perfs_club["Discipline"].str.split("/").str.get(1).str.strip().str.get(2)
        )

        perfs_club["Discipline_Type"] = perfs_club["Discipline"].apply(
            categorize_discipline
        )  # Renamed to avoid overwriting original discipline needed for podium title

        perfs_club = perfs_club.sort_values(
            by="Points", ascending=False
        )  # Sort before grouping

        podiums = {}
        for sexe in ["M", "F"]:
            for discipline_type in ["COURSE", "SAUT", "LANCER"]:
                # Get top 3 for each original discipline within the type/sex category
                top_3 = perfs_club[
                    (perfs_club["Sexe"] == sexe)
                    & (perfs_club["Discipline_Type"] == discipline_type)
                ]
                # Group by original discipline name to get top 3 per specific event
                podiums[f"{discipline_type}_{sexe}"] = top_3.head(3)

        st.subheader("Podiums Hommes")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Courses", "")
            st.dataframe(podiums["COURSE_M"])
        with col2:
            st.metric("Sauts", "")
            st.dataframe(podiums["SAUT_M"])
        with col3:
            st.metric("Lancers", "")
            st.dataframe(podiums["LANCER_M"])

        st.subheader("Podiums Femmes")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Courses", "")
            st.dataframe(podiums["COURSE_F"])
        with col2:
            st.metric("Sauts", "")
            st.dataframe(podiums["SAUT_F"])
        with col3:
            st.metric("Lancers", "")
            st.dataframe(podiums["LANCER_F"])


# Remplacer la colonne "Discipline" par "LANCER", "COURSE" ou "SAUT"
def categorize_discipline(discipline):
    discipline_clean = (
        discipline.split("/")[0].strip().upper()
    )  # Use only event name part
    if any(x in discipline_clean for x in ["JAVELOT", "DISQUE", "MARTEAU", "POIDS"]):
        return "LANCER"
    elif any(
        x in discipline_clean for x in ["HAUTEUR", "LONGUEUR", "TRIPLE", "PERCHE"]
    ):
        return "SAUT"
    else:
        # Assume everything else is a race, excluding relays handled earlier
        return "COURSE"


show_results_page()
