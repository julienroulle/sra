import streamlit as st
import pandas as pd
import plotly.express as px
from sqlmodel import Session, select
from models import engine, QuizPrediction  # Assuming models.py is accessible

st.set_page_config(page_title="Stats", layout="wide")


# Helper function to calculate 'Cote'
def calculate_cote(percentage):
    if percentage >= 75:
        return 1
    elif 50 <= percentage < 75:
        return 2
    elif 25 <= percentage < 50:
        return 4
    else:
        return 10


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

            # Create columns for chart and table
            col1, col2 = st.columns(2)

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
                labels = [f"{b}-{b + 1000}" for b in bins[:-1]]

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

                # Prepare DataFrame for plotting and table
                bin_counts_df = bin_counts.reset_index()
                bin_counts_df.columns = ["Points Range", "Count"]

                # Calculate percentages for the table
                total_count_bin = bin_counts_df["Count"].sum()
                bin_counts_df["Percentage"] = (
                    (bin_counts_df["Count"] / total_count_bin) * 100
                ).round(2)

                # Calculate 'Cote'
                bin_counts_df["Cote"] = bin_counts_df["Percentage"].apply(
                    calculate_cote
                )

                # Plot bar chart in the first column (still using Count for y-axis)
                with col1:
                    fig = px.bar(
                        bin_counts_df,
                        x="Points Range",
                        y="Count",
                        title=f"Distribution of Predicted Points for {category}",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Display the data table with percentages in the second column
                with col2:
                    st.write("Data:")
                    # Display relevant columns for the table, excluding 'Count'
                    st.dataframe(
                        bin_counts_df[["Points Range", "Percentage", "Cote"]],
                        use_container_width=True,
                    )

            else:
                # Calculate occurrences of each predicted value
                value_counts_raw = category_df["predicted_value"].value_counts()
                value_counts_df = value_counts_raw.reset_index()
                value_counts_df.columns = ["Predicted Value", "Count"]

                # Calculate percentages
                total_count_cat = value_counts_df["Count"].sum()
                value_counts_df["Percentage"] = (
                    (value_counts_df["Count"] / total_count_cat) * 100
                ).round(2)

                # Calculate 'Cote'
                value_counts_df["Cote"] = value_counts_df["Percentage"].apply(
                    calculate_cote
                )

                if not value_counts_df.empty:
                    # Plot pie chart in the first column using percentages
                    with col1:
                        fig = px.pie(
                            value_counts_df,  # Use the df with percentages
                            names="Predicted Value",
                            values="Percentage",  # Use Percentage for pie slices
                            title=f"Distribution of Predicted Values for {category} (%)",
                        )
                        fig.update_traces(
                            textinfo="percent+label", texttemplate="%{value:.2f}%"
                        )  # Format hover info
                        st.plotly_chart(fig, use_container_width=True)

                    # Display the data table with percentages in the second column
                    with col2:
                        st.write("Data:")
                        # Display relevant columns for the table, excluding 'Count'
                        st.dataframe(
                            value_counts_df[["Predicted Value", "Percentage", "Cote"]],
                            use_container_width=True,
                        )
                else:
                    # If no data, display message across both columns implicitly (or could span)
                    st.write(f"No predicted values to display for {category}.")


show_stats_page()
