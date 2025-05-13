import streamlit as st
import pandas as pd
from sqlmodel import Session, select
from models import engine, QuizPrediction

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

        # --- Store actual podiums ---
        actual_podiums_details = {}  # To store detailed podiums for scoring

        podiums = {}
        for sexe in ["M", "F"]:
            for discipline_type in ["COURSES", "SAUTS", "LANCERS"]:
                # Get top 3 for each original discipline within the type/sex category
                top_3_overall_type = perfs_club[
                    (perfs_club["Sexe"] == sexe)
                    & (perfs_club["Discipline_Type"] == discipline_type)
                ]
                # Group by original discipline name to get top 3 per specific event
                # And store these detailed results for scoring
                for discipline_name, group in top_3_overall_type.groupby("Discipline"):
                    actual_podiums_details[discipline_name] = group.head(3)

                # For display purposes, we might still want a summarized view or the overall top 3 for the type
                # This part remains for displaying general podiums as before
                sexe_str = "FEMME" if sexe == "F" else "HOMME"
                podiums[f"{discipline_type} {sexe_str}"] = top_3_overall_type.head(3)

        st.subheader("Podiums Hommes")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Courses", "")
            st.dataframe(podiums["COURSES HOMME"])
        with col2:
            st.metric("Sauts", "")
            st.dataframe(podiums["SAUTS HOMME"])
        with col3:
            st.metric("Lancers", "")
            st.dataframe(podiums["LANCERS HOMME"])

        st.subheader("Podiums Femmes")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Courses", "")
            st.dataframe(podiums["COURSES FEMME"])
        with col2:
            st.metric("Sauts", "")
            st.dataframe(podiums["SAUTS FEMME"])
        with col3:
            st.metric("Lancers", "")
            st.dataframe(podiums["LANCERS FEMME"])

        # --- Score Calculation ---
        st.subheader("Scores des Participants")
        user_scores = {}

        with Session(engine) as session:
            statement = select(QuizPrediction)
            predictions = session.exec(statement).all()

            if not predictions:
                st.write("Aucune prédiction trouvée.")
            else:
                # Group predictions by user
                user_predictions = {}
                for p in predictions:
                    user_predictions.setdefault(p.user_name, []).append(p)

                for user_name, preds in user_predictions.items():
                    score = 0
                    for pred in preds:
                        # We are interested in place predictions, e.g., "Place 1", "Place 2", "Place 3"
                        if "Place " not in pred.prediction_type:
                            continue

                        # pred.event_category should match a key in actual_podiums_details
                        # e.g., "100m / M" or "Javelot (800g) / F"
                        actual_event_podium_df = podiums.get(pred.event_category)

                        if (
                            actual_event_podium_df is not None
                            and not actual_event_podium_df.empty
                        ):
                            predicted_place_str = pred.prediction_type.split(" ")[1]
                            if not predicted_place_str.isdigit():
                                continue  # Malformed prediction_type
                            predicted_place_index = (
                                int(predicted_place_str) - 1
                            )  # 0-indexed

                            predicted_athlete = pred.predicted_value

                            # Check for exact match (athlete and place)
                            if predicted_place_index < len(actual_event_podium_df):
                                actual_athlete_at_predicted_place = (
                                    actual_event_podium_df.iloc[predicted_place_index][
                                        "Athlète"
                                    ]
                                )
                                if (
                                    actual_athlete_at_predicted_place.strip().lower()
                                    == predicted_athlete.strip().lower()
                                ):
                                    score += 3
                                    continue  # Move to next prediction

                            # Check if athlete is on podium but wrong place
                            actual_podium_athletes = (
                                actual_event_podium_df["Athlète"]
                                .str.strip()
                                .str.lower()
                                .tolist()
                            )
                            if (
                                predicted_athlete.strip().lower()
                                in actual_podium_athletes
                            ):
                                score += 1

                    user_scores[user_name] = score

                if user_scores:
                    scores_df = pd.DataFrame(
                        list(user_scores.items()), columns=["Utilisateur", "Score"]
                    )
                    scores_df = scores_df.sort_values(by="Score", ascending=False)
                    st.dataframe(scores_df, use_container_width=True)
                else:
                    st.write("Aucun score à afficher pour les prédictions de podium.")


# Remplacer la colonne "Discipline" par "LANCER", "COURSE" ou "SAUT"
def categorize_discipline(discipline):
    discipline_clean = (
        discipline.split("/")[0].strip().upper()
    )  # Use only event name part
    if any(x in discipline_clean for x in ["JAVELOT", "DISQUE", "MARTEAU", "POIDS"]):
        return "LANCERS"
    elif any(
        x in discipline_clean for x in ["HAUTEUR", "LONGUEUR", "TRIPLE", "PERCHE"]
    ):
        return "SAUTS"
    else:
        # Assume everything else is a race, excluding relays handled earlier
        return "COURSES"


show_results_page()
