import streamlit as st
import pandas as pd
import plotly.express as px
from sqlmodel import Session, select
from models import engine, QuizPrediction  # Assuming models.py is accessible


def show_stats_page():
    st.title("Prediction Statistics by Event Category")

    with Session(engine) as session:
        statement = select(QuizPrediction)
        results = session.exec(statement).all()

        if not results:
            st.write("No prediction data found to generate statistics.")
            return

        # Convert results to DataFrame for easier manipulation
        data_for_df = [
            {
                "event_category": res.event_category,
                "predicted_value": res.predicted_value,
            }
            for res in results
        ]
        df = pd.DataFrame(data_for_df)

        # Get unique event categories
        event_categories = df["event_category"].unique()

        for category in event_categories:
            st.subheader(f"Stats for: {category}")
            category_df = df[df["event_category"] == category]

            if category_df.empty:
                st.write("No predictions for this category.")
                continue

            if category == "TOTAL DE POINTS EQUIPE 1":
                # For the "TOTAL DE POINTS EQUIPE 1" category, plot a bar chart with bins of 1000 between 35000 and 65000
                # Convert predicted_value to numeric, coerce errors to NaN and drop them
                category_df_numeric = category_df.copy()
                category_df_numeric["predicted_value"] = pd.to_numeric(
                    category_df_numeric["predicted_value"], errors="coerce"
                )
                category_df_numeric = category_df_numeric.dropna(
                    subset=["predicted_value"]
                )

                # Define bins from 35000 to 65000 (inclusive) with step 1000
                bins = list(range(35000, 65001, 1000))
                labels = [f"{b}-{b + 999}" for b in bins[:-1]]

                # Bin the values
                category_df_numeric["bin"] = pd.cut(
                    category_df_numeric["predicted_value"],
                    bins=bins,
                    labels=labels,
                    include_lowest=True,
                    right=True,
                )

                # Count occurrences in each bin
                bin_counts = category_df_numeric["bin"].value_counts().sort_index()

                # Prepare DataFrame for plotting
                bin_counts_df = bin_counts.reset_index()
                bin_counts_df.columns = ["Points Range", "Count"]

                # Plot bar chart
                fig = px.bar(
                    bin_counts_df,
                    x="Points Range",
                    y="Count",
                    title=f"Distribution of Predicted Points for {category}",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Calculate occurrences of each predicted value
                value_counts = (
                    category_df["predicted_value"].value_counts().reset_index()
                )
                value_counts.columns = ["predicted_value", "count"]

                if not value_counts.empty:
                    fig = px.pie(
                        value_counts,
                        names="predicted_value",
                        values="count",
                        title=f"Distribution of Predicted Values for {category}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write(f"No predicted values to display for {category}.")


show_stats_page()
