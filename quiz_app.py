import streamlit as st
from constants import athletes  # Import the athletes list

# Constants for password and page names (can be moved to a constants.py later)
PASSWORD = "SRAJEU"
PAGE_WELCOME = "Welcome"
PAGE_LANCER_HOMME = "Lancer Homme"
PAGE_LANCER_FEMME = "Lancer Femme"
PAGE_SAUT_HOMME = "Saut Homme"
PAGE_SAUT_FEMME = "Saut Femme"
PAGE_COURSE_HOMME = "Course Homme"
PAGE_COURSE_FEMME = "Course Femme"
PAGE_POINTS = "Points du Jour"
PAGE_SUMMARY = "Récapitulatif"  # Optional: for showing all answers

# Define the order of pages for the wizard
APP_PAGES_ORDER = [
    PAGE_LANCER_HOMME,
    PAGE_LANCER_FEMME,
    PAGE_SAUT_HOMME,
    PAGE_SAUT_FEMME,
    PAGE_COURSE_HOMME,
    PAGE_COURSE_FEMME,
    PAGE_POINTS,
    PAGE_SUMMARY,
]

# Quiz pages for progress calculation (excluding summary)
QUIZ_PAGES_FOR_PROGRESS = APP_PAGES_ORDER[:-1]

# Prepare athlete choices by adding the "Other" option
ATHLETES_CHOICES = ["Autre (préciser)"] + sorted(athletes)


def main():
    st.set_page_config(
        page_title="Quiz SRA", layout="wide", initial_sidebar_state="collapsed"
    )

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
    st.title("Bienvenue au Quiz SRA!")

    name = st.text_input("Entrez votre nom:", key="name_input_login")
    password_input = st.text_input(
        "Entrez le mot de passe:", type="password", key="password_input_login"
    )

    if st.button("Commencer le Quiz", key="login_button"):
        if password_input == PASSWORD:
            if name:
                st.session_state.logged_in = True
                st.session_state.user_name = name
                st.session_state.current_page_index = 0
                st.session_state.current_page = APP_PAGES_ORDER[0]
                # Clear answers from any previous session for this user upon new login
                st.session_state.answers = {}
                st.rerun()
            else:
                st.error("Veuillez entrer votre nom.")
        else:
            st.error("Mot de passe incorrect.")


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

            if selected_value == "Autre (préciser)":
                other_value = st.session_state.get(other_key, "").strip()
                if other_value:  # Only save if 'other' is filled
                    podium_data_to_save[f"place{i}"] = other_value
            elif (
                selected_value and selected_value != "Choisissez un athlète ou 'Autre'"
            ):  # Non-empty, not placeholder, not "Autre"
                podium_data_to_save[f"place{i}"] = selected_value

        if podium_data_to_save:
            st.session_state.answers[page_answer_key] = podium_data_to_save
        elif page_answer_key in st.session_state.answers and not podium_data_to_save:
            # If user clears all fields on a page that previously had answers
            del st.session_state.answers[page_answer_key]

    elif current_page_name == PAGE_POINTS:
        points_value = st.session_state.get("points_input")
        if points_value is not None:  # number_input can be 0
            st.session_state.answers[page_answer_key] = {"points": points_value}
        # No need to explicitly delete if None, as number_input usually has a default.
        # If it becomes an issue, add logic similar to event pages for deletion.


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
                # No save on previous
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
                save_current_page_data()  # Save data before moving to next page
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
                    st.session_state[select_widget_key] = "Autre (préciser)"
            else:
                st.session_state[select_widget_key] = None  # Let placeholder show

        # Initialize text_input state (for "other")
        if other_widget_key not in st.session_state:
            if (
                current_saved_value_for_place
                and st.session_state.get(select_widget_key) == "Autre (préciser)"
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

        if st.session_state.get(select_widget_key) == "Autre (préciser)":
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
    st.write("Prédisez le podium pour cet événement.")
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
        "Combien de points pensez-vous que l'équipe marquera aujourd'hui?",
        min_value=0,
        step=1,
        key="points_input",  # Let Streamlit manage value via session state
        # value=current_points_saved, # Removed: value now controlled by st.session_state.points_input
    )


def show_summary_page():
    st.title("Récapitulatif de vos réponses")
    if not st.session_state.answers:
        st.write("Vous n'avez pas encore soumis de prédictions.")
        if st.button("Commencer les prédictions", key="start_pred_from_empty_summary"):
            st.session_state.current_page_index = 0
            st.session_state.current_page = APP_PAGES_ORDER[0]
            st.rerun()
        return

    all_pages_keys_ordered = [
        p.lower().replace(" ", "_") for p in APP_PAGES_ORDER if p != PAGE_SUMMARY
    ]

    for page_key in all_pages_keys_ordered:
        page_title_parts = page_key.split("_")
        page_title = " ".join(word.capitalize() for word in page_title_parts)

        page_answers = st.session_state.answers.get(page_key)

        if page_answers:
            st.subheader(page_title)
            if page_key == PAGE_POINTS.lower().replace(" ", "_"):
                st.metric(
                    label="Points Prédits",
                    value=page_answers.get("points", "Non renseigné"),
                )
            else:
                # Event page (Lancer, Saut, Course)
                for i in range(1, 4):
                    athlete_name = page_answers.get(f"place{i}", "Non renseigné")
                    st.metric(label=f"{i}e Place", value=athlete_name)
            st.divider()
        else:
            # Optionally show pages that were skipped or had no answers
            st.subheader(f"{page_title} (Non renseigné)")
            st.write("Aucune prédiction enregistrée pour cette catégorie.")
            st.divider()

    if st.button("Recommencer le quiz", key="restart_quiz_summary"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.current_page_index = 0
        st.session_state.answers = {}
        st.session_state.current_page = PAGE_WELCOME

        # Minimal clearing of widget states, Streamlit handles much of this on rerun/page change
        # Only clear those explicitly managed or that might cause issues.
        keys_to_clear = ["name_input_login", "password_input_login", "points_input"]
        for p_key in all_pages_keys_ordered:
            if p_key != PAGE_POINTS.lower().replace(" ", "_"):
                for i in range(1, 4):
                    keys_to_clear.append(f"{p_key}_place{i}_select")
                    keys_to_clear.append(f"{p_key}_place{i}_other")

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()
