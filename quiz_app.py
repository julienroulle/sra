import streamlit as st

st.set_page_config(
    page_title="Pronostics SRA", layout="wide", initial_sidebar_state="collapsed"
)

from constants import athletes  # Import the athletes list
from models import (
    engine,
    QuizPrediction,
    create_db_and_tables_once,
)  # DB Imports, changed function name
from sqlmodel import Session, select  # DB Imports, added select

# Constants for page names (can be moved to a constants.py later)
PAGE_WELCOME = "Welcome"
PAGE_LANCER_HOMME = "LANCERS HOMME"
PAGE_LANCER_FEMME = "LANCERS FEMME"
PAGE_SAUT_HOMME = "SAUTS HOMME"
PAGE_SAUT_FEMME = "SAUTS FEMME"
PAGE_COURSE_HOMME = "COURSES HOMME"
PAGE_COURSE_FEMME = "COURSES FEMME"
PAGE_POINTS = "TOTAL DE POINTS EQUIPE 1"
PAGE_SUMMARY = "Récapitulatif"  # Optional: for showing all answers

# Define prediction type constants
PREDICTION_TYPE_PLACE_1 = "Place 1"
PREDICTION_TYPE_PLACE_2 = "Place 2"
PREDICTION_TYPE_PLACE_3 = "Place 3"
PREDICTION_TYPE_POINTS = "Total Points"

# Define the order of pages for the wizard
APP_PAGES_ORDER = [
    PAGE_LANCER_FEMME,
    PAGE_LANCER_HOMME,
    PAGE_SAUT_FEMME,
    PAGE_SAUT_HOMME,
    PAGE_COURSE_FEMME,
    PAGE_COURSE_HOMME,
    PAGE_POINTS,
    PAGE_SUMMARY,
]

# Quiz pages for progress calculation (excluding summary)
QUIZ_PAGES_FOR_PROGRESS = APP_PAGES_ORDER[:-1]

# Prepare athlete choices by adding the "Other" option
ATHLETES_CHOICES = ["Autre"] + sorted(athletes)


def load_predictions_from_db(user_name: str):
    loaded_answers = {}
    # Helper to map page display names (constants) to page_answer_keys
    page_name_to_answer_key = {
        page: page.lower().replace(" ", "_")
        for page in APP_PAGES_ORDER
        if page not in [PAGE_SUMMARY, PAGE_WELCOME]
    }
    # And the reverse for easier lookup from DB event_category
    answer_key_to_page_name = {v: k for k, v in page_name_to_answer_key.items()}

    with Session(engine) as session:
        db_predictions = session.exec(
            select(QuizPrediction).where(QuizPrediction.user_name == user_name)
        ).all()

        for pred in db_predictions:
            event_category_constant = (
                pred.event_category
            )  # This should be like PAGE_LANCER_HOMME
            page_answer_key = page_name_to_answer_key.get(event_category_constant)

            if not page_answer_key:
                # Fallback if event_category_constant isn't directly in APP_PAGES_ORDER (e.g. old data)
                # This case should ideally not happen with current save logic
                print(
                    f"Warning: Could not map event_category '{event_category_constant}' to a page_answer_key."
                )
                # Attempt a direct conversion as a last resort, though it might not match APP_PAGES_ORDER keys
                page_answer_key = event_category_constant.lower().replace(" ", "_")

            if page_answer_key not in loaded_answers:
                loaded_answers[page_answer_key] = {}

            if pred.prediction_type == PREDICTION_TYPE_POINTS:
                try:
                    loaded_answers[page_answer_key]["points"] = int(
                        pred.predicted_value
                    )
                except ValueError:
                    print(
                        f"Warning: Could not convert points value '{pred.predicted_value}' to int for {page_answer_key}"
                    )
                    loaded_answers[page_answer_key]["points"] = (
                        0  # Default to 0 or handle as error
                    )
            elif pred.prediction_type == PREDICTION_TYPE_PLACE_1:
                loaded_answers[page_answer_key]["place1"] = pred.predicted_value
            elif pred.prediction_type == PREDICTION_TYPE_PLACE_2:
                loaded_answers[page_answer_key]["place2"] = pred.predicted_value
            elif pred.prediction_type == PREDICTION_TYPE_PLACE_3:
                loaded_answers[page_answer_key]["place3"] = pred.predicted_value

    st.session_state.answers = loaded_answers
    # After loading, we need to ensure that the Streamlit widget states themselves are updated
    # for the current page if it's already rendered. This is a bit tricky as Streamlit reruns.
    # The existing logic in get_podium_input and show_points_page should handle initializing
    # widget states from st.session_state.answers when they run.


def main():
    # Create database tables if they don't exist (now uses _once version)
    create_db_and_tables_once()

    # Initialize session state variables if they don't exist
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    # current_page is now derived from current_page_index
    if "current_page_index" not in st.session_state:
        st.session_state.current_page_index = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if not st.session_state.logged_in:
        st.session_state.current_page = PAGE_WELCOME
        show_login_page()
    else:
        if st.session_state.current_page_index < len(APP_PAGES_ORDER):
            st.session_state.current_page = APP_PAGES_ORDER[
                st.session_state.current_page_index
            ]
        else:
            st.session_state.current_page_index = len(APP_PAGES_ORDER) - 1
            st.session_state.current_page = APP_PAGES_ORDER[-1]
        render_wizard_layout()


def show_login_page():
    st.title("PRONOSTICS INTERCLUBS 2025 - EQUIPE 1")

    st.subheader(
        "Bienvenue dans le module de pronostics pour le second tour des Interclubs 2025 !"
    )

    st.write("**Règles du jeu :**")

    st.write(
        """
        - Pour chaque famille de discipline, donne le podium des 3 meilleurs athlètes à la table hongroise (distinction hommes/femmes).
        - Un athlète bien placé sur le podium rapporte **3 points**.
        - Un athlète placé sur le podium mais à la mauvaise place rapporte **1 point**.
        - Un coefficient multiplicateur est appliqué en fonction de l'athlète.
            - Un athlète cité entre 100% et 75% (inclus) des podiums aura un multiplicateur neutre de **(x1)**.
            - Un athlète cité entre 74% et 50% (inclus) des podiums aura un multiplicateur de points **(x2)**.
            - Un athlète cité entre 49% et 25% (inclus) des podiums aura un multiplicateur de points **(x4)**.
            - Un athlète cité dans 24% (et moins) des podiums aura un multiplicateur de points **(x10)**.
        """
    )

    with st.expander("**Exemple :**"):
        st.write(
            """
        Avant la compétition, je pronostique Solène Gicquel à la première place de la catégorie "SAUTS FEMMES".\n
        Durant la compétition, Solène Gicquel réalise le plus grand nombre de points et termine donc à la première place dans la catégorie "SAUTS FEMMES". Cela me rapporte 3 points.\n
        Sur 100 participants au jeu, Solène Gicquel a été pronostiquée sur 12 podiums de la catégorie "SAUTS FEMMES" (citée dans 24% et moins des podiums). Cela applique un coefficient multiplicateur (x10) aux points récoltés ci-dessus.\n  
        Mon pronostic sur Solène Gicquel me rapporte donc 30 points au total.
        """
        )

    st.write(
        """
        - Une question additionnelle sur le total des points de l'équipe permet de rapporter de 1 à 10 points, 1 point pour un résultat proche de +-1000 points.
        - Le joueur ayant accumulé le plus de points avec ses pronostics remporte le jeu.
        - En cas d'égalité au nombre de points, les joueurs sont départagés à celui qui aura prédit le total de points global de l'équipe le plus proche de la réalité. Si l'égalité perdure, les deux joueurs sont désignés vainqueurs ex-aequo.
        - Il est possible de changer tes pronostics jusqu'à dimanche 10h00. Tout formulaire envoyé ou réenvoyé après cet horaire sera considéré hors concours.
        - Pour revenir sur tes pronostics déjà effectués, remets le même "Prénom + Nom" renseignés à l'inscription ainsi que ton code à 4 chiffres.
        """
    )

    st.write("**Bon jeu !**")

    col_1, col_2 = st.columns([4, 1])

    with col_1:
        name = st.text_input(
            "Entrez votre nom:", key="name_input_login", placeholder="Prénom + Nom"
        )

    with col_2:
        code = st.text_input(
            "Entrez un code à 4 chiffres:", key="code_input_login", max_chars=4
        )

    if st.button("JOUER", key="login_button", type="primary"):
        if name and code and len(code) == 4:
            st.session_state.logged_in = True
            st.session_state.user_name = name + code
            st.session_state.current_page_index = 0
            st.session_state.current_page = APP_PAGES_ORDER[0]
            st.session_state.answers = {}
            load_predictions_from_db(name + code)  # Load existing predictions from DB

            # Clear widget-specific states to force re-initialization from loaded answers
            page_keys_for_widgets = [
                page.lower().replace(" ", "_")
                for page in APP_PAGES_ORDER
                if page not in [PAGE_SUMMARY, PAGE_WELCOME, PAGE_POINTS]
            ]
            for page_key in page_keys_for_widgets:
                for i in range(1, 4):
                    select_k = f"{page_key}_place{i}_select"
                    other_k = f"{page_key}_place{i}_other"
                    if select_k in st.session_state:
                        del st.session_state[select_k]
                    if other_k in st.session_state:
                        del st.session_state[other_k]
            if "points_input" in st.session_state:
                del st.session_state["points_input"]

            st.rerun()
        else:
            if not name:
                st.error("Veuillez entrer votre nom.")
            if not code:
                st.error("Veuillez entrer un code à 4 chiffres.")


def save_current_page_data():
    page_index = st.session_state.current_page_index
    # Ensure we are not trying to save data for summary page or beyond APP_PAGES_ORDER bounds
    if (
        page_index >= len(APP_PAGES_ORDER)
        or APP_PAGES_ORDER[page_index] == PAGE_SUMMARY
    ):
        return

    current_page_name = APP_PAGES_ORDER[page_index]
    page_answer_key = current_page_name.lower().replace(" ", "_")

    if (
        current_page_name in QUIZ_PAGES_FOR_PROGRESS
        and current_page_name != PAGE_POINTS
    ):
        # Event page (Lancer, Saut, Course)
        podium_data_to_save = {}
        for i in range(1, 4):  # Places 1, 2, 3
            select_key = f"{page_answer_key}_place{i}_select"
            other_key = f"{page_answer_key}_place{i}_other"

            selected_value = st.session_state.get(select_key)
            actual_value_to_save = None

            if selected_value == "Autre":
                other_value = st.session_state.get(other_key, "").strip()
                if other_value:  # Only consider if 'other' is filled
                    actual_value_to_save = other_value
            elif (
                selected_value and selected_value != "Choisissez un athlète ou 'Autre'"
            ):  # Non-empty, not placeholder, not "Autre"
                actual_value_to_save = selected_value

            # Save the actual value (or None if nothing valid was selected/entered for this place)
            # This ensures that if a user clears a field, it's reflected as None (or not present in dict)
            if actual_value_to_save:
                podium_data_to_save[f"place{i}"] = actual_value_to_save
            # If not actual_value_to_save, the key f"place{i}" won't be in podium_data_to_save
            # This is important for the DB save logic to know what to delete/insert

        if podium_data_to_save:
            st.session_state.answers[page_answer_key] = podium_data_to_save
            save_page_data_to_db(current_page_name, podium_data_to_save)  # DB save
        elif (
            page_answer_key in st.session_state.answers
        ):  # If all fields cleared on a page that had answers
            del st.session_state.answers[page_answer_key]
            save_page_data_to_db(
                current_page_name, {}
            )  # DB save with empty data to clear entries
        else:  # Page was initially empty and remains empty, no answers, and no pre-existing answers to clear
            save_page_data_to_db(
                current_page_name, {}
            )  # Still call to ensure DB is cleared if it had stale data from a previous session for this user somehow

    elif current_page_name == PAGE_POINTS:
        points_value = st.session_state.get("points_input")
        page_data_to_save = {}
        if points_value is not None:  # number_input can be 0
            page_data_to_save = {"points": points_value}
            st.session_state.answers[page_answer_key] = page_data_to_save
        elif page_answer_key in st.session_state.answers:  # Points cleared
            del st.session_state.answers[page_answer_key]

        save_page_data_to_db(
            current_page_name, page_data_to_save
        )  # DB save (even if empty to clear)


def render_wizard_layout():
    st.sidebar.title(f"Bonjour, {st.session_state.user_name}!")
    # Sidebar can be used for a global "Recommencer" or other non-navigation items later

    current_page_name = APP_PAGES_ORDER[st.session_state.current_page_index]

    # Progress Bar
    if current_page_name in QUIZ_PAGES_FOR_PROGRESS:
        try:
            current_quiz_step = QUIZ_PAGES_FOR_PROGRESS.index(current_page_name)
            total_quiz_steps = len(QUIZ_PAGES_FOR_PROGRESS)
            progress = (current_quiz_step + 1) / total_quiz_steps
            st.progress(progress)
            st.caption(f"Étape {current_quiz_step + 1} sur {total_quiz_steps}")
        except ValueError:
            pass  # current_page_name might not be in QUIZ_PAGES_FOR_PROGRESS (e.g. summary)

    # Display page content
    if (
        current_page_name == PAGE_LANCER_HOMME
        or current_page_name == PAGE_LANCER_FEMME
        or current_page_name == PAGE_SAUT_HOMME
        or current_page_name == PAGE_SAUT_FEMME
        or current_page_name == PAGE_COURSE_HOMME
        or current_page_name == PAGE_COURSE_FEMME
    ):
        show_event_page(current_page_name)
    elif current_page_name == PAGE_POINTS:
        show_points_page()
    elif current_page_name == PAGE_SUMMARY:
        show_summary_page()

    # Navigation Buttons
    col_nav_1, col_nav_2, col_nav_3 = st.columns([1, 4, 1])

    with col_nav_1:
        if st.session_state.current_page_index > 0:
            if st.button(
                "⬅️ Précédent", key="prev_button_wizard", use_container_width=True
            ):
                save_current_page_data()  # Save data of the page user is LEAVING
                st.session_state.current_page_index -= 1
                st.session_state.current_page = APP_PAGES_ORDER[
                    st.session_state.current_page_index
                ]
                st.rerun()

    with col_nav_3:
        if st.session_state.current_page_index < len(APP_PAGES_ORDER) - 1:
            if st.button(
                "Suivant ➡️", key="next_button_wizard", use_container_width=True
            ):
                save_current_page_data()  # Save data of page user is LEAVING
                st.session_state.current_page_index += 1
                st.session_state.current_page = APP_PAGES_ORDER[
                    st.session_state.current_page_index
                ]
                st.rerun()
        elif (
            current_page_name == PAGE_SUMMARY
        ):  # On summary page, no "Next" button. Restart is handled in show_summary_page
            pass


def get_podium_input(page_key_prefix):
    podium = {}
    st.subheader("Podium")
    page_answers = st.session_state.answers.get(page_key_prefix, {})

    for i in range(1, 4):
        place_key = f"place{i}"
        select_widget_key = f"{page_key_prefix}_{place_key}_select"
        other_widget_key = f"{page_key_prefix}_{place_key}_other"

        current_saved_value_for_place = page_answers.get(
            place_key
        )  # This is the actual athlete name or other string

        # Initialize selectbox state
        if select_widget_key not in st.session_state:
            if current_saved_value_for_place:
                if current_saved_value_for_place in ATHLETES_CHOICES:
                    st.session_state[select_widget_key] = current_saved_value_for_place
                else:  # It's an "other" value not in ATHLETES_CHOICES list (e.g. custom text)
                    st.session_state[select_widget_key] = "Autre"
            else:
                st.session_state[select_widget_key] = None  # Let placeholder show

        # Initialize text_input state (for "other")
        if other_widget_key not in st.session_state:
            if (
                current_saved_value_for_place
                and st.session_state.get(select_widget_key) == "Autre"
            ):
                st.session_state[other_widget_key] = current_saved_value_for_place
            else:
                st.session_state[other_widget_key] = ""  # Default to empty string

        st.selectbox(
            f"{i}e Place:",
            options=ATHLETES_CHOICES,
            key=select_widget_key,  # Let Streamlit manage value via session state
            # index=None, # Removed: value now controlled by st.session_state[select_widget_key]
            placeholder="Choisissez un athlète ou 'Autre'",
        )

        if st.session_state.get(select_widget_key) == "Autre":
            st.text_input(
                f"Précisez le nom ({i}e Place):",
                key=other_widget_key,  # Let Streamlit manage value via session state
                # value=..., # Removed: value now controlled by st.session_state[other_widget_key]
            )
        else:
            # If "Autre" is not selected, ensure the corresponding text input state is cleared
            # This is useful if the user selected "Autre", typed something, then switched back to an athlete
            st.session_state[other_widget_key] = ""

    # podium dict is not strictly used by caller for value retrieval anymore, but helps structure the creation
    return podium


def show_event_page(page_name):
    st.title(page_name)
    page_answer_key = page_name.lower().replace(" ", "_")
    if page_name == PAGE_LANCER_HOMME:
        st.write(
            "Donne le classement des 3 meilleurs lanceurs de l'équipe 1 sur la compétition."
        )
    elif page_name == PAGE_LANCER_FEMME:
        st.write(
            "Donne le classement des 3 meilleures lanceuses de l'équipe 1 sur la compétition."
        )
    elif page_name == PAGE_SAUT_HOMME:
        st.write(
            "Donne le classement des 3 meilleurs sauteurs de l'équipe 1 sur la compétition."
        )
    elif page_name == PAGE_SAUT_FEMME:
        st.write(
            "Donne le classement des 3 meilleures sauteuses de l'équipe 1 sur la compétition."
        )
    elif page_name == PAGE_COURSE_HOMME:
        st.write(
            "Donne le classement des 3 meilleurs coureurs de l'équipe 1 sur la compétition."
        )
    elif page_name == PAGE_COURSE_FEMME:
        st.write(
            "Donne le classement des 3 meilleures coureuses de l'équipe 1 sur la compétition."
        )
    get_podium_input(page_answer_key)


def show_points_page():
    st.title(PAGE_POINTS)
    page_answer_key = PAGE_POINTS.lower().replace(" ", "_")
    current_points_saved = st.session_state.answers.get(page_answer_key, {}).get(
        "points", 0
    )

    # Initialize points_input state if it doesn't exist
    if "points_input" not in st.session_state:
        st.session_state.points_input = current_points_saved

    st.number_input(
        "Quel sera le total de points récoltés par l'équipe 1 à la fin de la journée de compétition ?",
        min_value=0,
        step=1,
        key="points_input",  # Let Streamlit manage value via session state
        # value=current_points_saved, # Removed: value now controlled by st.session_state.points_input
    )


def show_summary_page():
    st.title(PAGE_SUMMARY)
    st.write(f"Merci pour ta participation, {st.session_state.user_name}!")
    st.write("Voici un récapitulatif de tes réponses:")

    # Display answers (existing logic)
    for page_key, data in st.session_state.answers.items():
        # Attempt to map page_key back to a displayable page name
        # This is a bit manual; consider a reverse mapping if this becomes complex
        display_page_name = page_key.replace("_", " ").title()
        for constant_name, constant_value in globals().items():
            if (
                isinstance(constant_value, str)
                and constant_value.lower().replace(" ", "_") == page_key
            ):
                display_page_name = constant_value
                break

        st.subheader(display_page_name)
        if isinstance(data, dict):
            if "points" in data:  # Points page
                st.write(f"Points: {data['points']}")
            else:  # Event page (podium)
                for place, athlete in data.items():
                    # Convert place key (e.g., "place1") to display string (e.g., "1ère Place")
                    place_display = ""
                    if place == "place1":
                        place_display = "1ère Place"
                    elif place == "place2":
                        place_display = "2ème Place"
                    elif place == "place3":
                        place_display = "3ème Place"
                    else:
                        place_display = place.title()
                    st.write(f"{place_display}: {athlete}")
        else:
            st.write(str(data))
        st.markdown("---")

    if st.button("Terminer", key="restart_quiz_summary"):
        # Reset relevant session state variables to restart the quiz
        st.session_state.logged_in = False  # Go back to login
        st.session_state.user_name = ""
        st.session_state.current_page_index = 0
        st.session_state.answers = {}
        # Or you could hide the button: if not st.session_state.get('predictions_submitted', False): display button...
        st.rerun()


def save_page_data_to_db(page_name_constant: str, data: dict):
    user_name = st.session_state.user_name
    if not user_name:
        # This should ideally not happen if user is logged in, but good for robustness
        print("Error: User name not found in session state for DB save.")
        return

    event_category = page_name_constant  # e.g., PAGE_LANCER_HOMME

    with Session(engine) as session:
        # Delete existing predictions for this user and event_category to avoid duplicates/outdated entries
        if event_category == PAGE_POINTS:
            stmt = QuizPrediction.__table__.delete().where(
                (QuizPrediction.user_name == user_name)
                & (QuizPrediction.event_category == event_category)
                & (QuizPrediction.prediction_type == PREDICTION_TYPE_POINTS)
            )
            session.execute(stmt)
        else:  # For event pages (podium)
            stmt_place1 = QuizPrediction.__table__.delete().where(
                (QuizPrediction.user_name == user_name)
                & (QuizPrediction.event_category == event_category)
                & (QuizPrediction.prediction_type == PREDICTION_TYPE_PLACE_1)
            )
            session.execute(stmt_place1)
            stmt_place2 = QuizPrediction.__table__.delete().where(
                (QuizPrediction.user_name == user_name)
                & (QuizPrediction.event_category == event_category)
                & (QuizPrediction.prediction_type == PREDICTION_TYPE_PLACE_2)
            )
            session.execute(stmt_place2)
            stmt_place3 = QuizPrediction.__table__.delete().where(
                (QuizPrediction.user_name == user_name)
                & (QuizPrediction.event_category == event_category)
                & (QuizPrediction.prediction_type == PREDICTION_TYPE_PLACE_3)
            )
            session.execute(stmt_place3)

        predictions_to_add = []
        if event_category == PAGE_POINTS:
            points_value = data.get("points")
            if points_value is not None:
                prediction = QuizPrediction(
                    user_name=user_name,
                    event_category=event_category,
                    prediction_type=PREDICTION_TYPE_POINTS,
                    predicted_value=str(points_value),
                )
                predictions_to_add.append(prediction)
        else:  # Event page (podium)
            for place_key, athlete_name in data.items():
                prediction_type = ""
                if place_key == "place1":
                    prediction_type = PREDICTION_TYPE_PLACE_1
                elif place_key == "place2":
                    prediction_type = PREDICTION_TYPE_PLACE_2
                elif place_key == "place3":
                    prediction_type = PREDICTION_TYPE_PLACE_3

                if (
                    prediction_type and athlete_name
                ):  # athlete_name might be None/empty if cleared
                    prediction = QuizPrediction(
                        user_name=user_name,
                        event_category=event_category,
                        prediction_type=prediction_type,
                        predicted_value=str(athlete_name),
                    )
                    predictions_to_add.append(prediction)

        if predictions_to_add:
            session.add_all(predictions_to_add)

        session.commit()


if __name__ == "__main__":
    main()
