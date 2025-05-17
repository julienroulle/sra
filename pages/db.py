import streamlit as st

st.set_page_config(page_title="Database View", layout="wide")

from sqlmodel import Session, select
from models import (
    engine,
    QuizPrediction,
)  # Assuming models.py is in the same directory or accessible
import pandas as pd


def show_db_view():
    # st.set_page_config(page_title="Database View", layout="wide") # Removed: Should be in the main app script
    st.title("Database Content: Quiz Predictions")

    with Session(engine) as session:
        statement = select(QuizPrediction)
        results = session.exec(statement).all()

        if results:
            # Convert to a list of dictionaries for DataFrame creation
            data_for_df = [
                {
                    "ID": res.id,
                    "User Name": res.user_name,
                    "Event Category": res.event_category,
                    "Prediction Type": res.prediction_type,
                    "Predicted Value": res.predicted_value,
                    "Submission Timestamp": res.submission_timestamp,
                }
                for res in results
            ]
            st.subheader("Database content")
            df = pd.DataFrame(data_for_df)
            st.dataframe(df)

            st.subheader("Participants")
            participants = df["User Name"].unique()
            participants_df = pd.DataFrame(participants, columns=["User Name"])
            participants_df["Missing Predictions"] = participants_df.apply(
                lambda x: 19 - len(df[df["User Name"] == x["User Name"]]),
                axis=1,
            )
            st.dataframe(
                participants_df.sort_values(by="Missing Predictions", ascending=False)
            )

        else:
            st.write("No predictions found in the database.")


# To ensure this page can be run directly for testing if needed,
# but it will be called by Streamlit when navigating to the /db route.
# if __name__ == "__main__":  # This condition prevents Streamlit from running it as a page
#     show_db_view()

show_db_view()  # Call the function directly to render the page
