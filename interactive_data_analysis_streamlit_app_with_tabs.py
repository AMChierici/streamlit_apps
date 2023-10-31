
import streamlit as st
from streamlit_ace import st_ace
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re

# Function to clean column data
def clean_column_data(df, column, groupby):
    # df[column] = df[column].astype(str).apply(lambda x: re.split('; |, ', x))
    # df = df.explode(column, ignore_index=True)
    # df[column] = df[column].str.strip().str.lower()

    # Drop rows where groupby is NaN
    # df_filtered = df.dropna(subset=[groupby])
    # # Convert groupby to integers for better readability
    # df_filtered[groupby] = df_filtered[groupby].astype(int)

    # Split the column into a list of items
    df_filtered = df.copy()
    df_filtered[column] = df[column].astype(str).apply(lambda x: re.split('; |, ', x))
    # Explode the DataFrame so that each country has its own row, keeping other columns the same
    df_exploded = df_filtered.explode(column, ignore_index=True)
    # Trim whitespace and convert to lowercase for the column column
    df_exploded[column] = df_exploded[column].str.strip().str.lower()
    if column != groupby:
        # Sum counts for duplicate countries and years
        df_grouped = df_exploded.groupby([column, groupby]).size().reset_index(name='Count')

        return df_grouped
    else:

        return df_exploded

# Streamlit app starts here
# Create a password input field
password = st.text_input("Enter Password", type="password")

# Check if the password is correct
if password == PASSWORD:
    st.success("Authentication successful!")

        # Your protected content here
    st.title("Interactive Data Analysis")

    # Cache the DataFrame to maintain state across tabs
    # @st.cache(allow_output_mutation=True)
    # @st.cache_data(show_spinner="Fetching data from file...", )
    def load_data(uploaded_file=False, new_file=pd.DataFrame()):
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
        else:
            df = new_file
        return df

    df = load_data()
    uploaded_file = None

    # Create tabs
    tab1, tab2 = st.tabs(["Data Upload & Cleaning", "Visualization"])
    # tab_selection = st.sidebar.radio("Go to", ["Data Upload & Cleaning", "Visualization"])

    # if tab_selection == "Data Upload & Cleaning":
    with tab1:
        st.header("Data Upload & Cleaning")
        
        # File Upload
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file:
            # df = pd.read_csv(uploaded_file)
            # load_data(df)
            df = load_data(uploaded_file=uploaded_file)
            st.write("Data uploaded successfully!")
            
            # Column Selection for Cleaning and Grouping
            column_to_clean = st.selectbox("Select column to clean", df.columns)
            column_to_group_by = st.selectbox("Select column to group by", df.columns)
            df = clean_column_data(df, column_to_clean, column_to_group_by)
            df = load_data(new_file=df)
            
            # Display Unique Values
            if st.checkbox("Display unique values for cleaning"):
                unique_values = df[column_to_clean].unique()
                st.write(unique_values)
                
                # Manual Cleaning
                mappings = st.text_area("""Enter mappings for cleaning (old_value\:new_value, separated by commas)""", "")
                if mappings:
                    mapping_dict = dict(item.split(":") for item in mappings.split(","))
                    df[column_to_clean] = df[column_to_clean].replace(mapping_dict)
                    df = load_data(new_file=df)
                    unique_values = df[column_to_clean].unique()
                    st.write(unique_values)
        
    # elif tab_selection == "Visualization":
    with tab2:
        st.header("Visualization")
        
        if not uploaded_file:
            st.write("Please upload a CSV file to get started.")
        else:
            df = load_data(new_file=df)

        if df is not None:
            
            # Column Selection for Analysis
            column_to_analyze = st.selectbox("Select column for analysis", df.columns)
            # column_to_group_by = st.selectbox("Select column to group by", df.columns)

            if column_to_analyze and column_to_group_by:  
                # Parameter Selection: Top N or Top X%
                analysis_type = st.selectbox("Select analysis type", ["Top N", "Top X%"])
                df_counts = df[column_to_analyze].value_counts().reset_index()
                if analysis_type == "Top N":
                    top_n = st.slider("Select Top N", min_value=1, max_value=100, value=10)
                    df_counts_top = df_counts.head(top_n)
                else:
                    top_x_percent = st.slider("Select Top X%", min_value=1, max_value=100, value=20)
                    df_counts_top = df_counts.head(int(len(df) * (top_x_percent / 100)))

                st.dataframe(df_counts_top, use_container_width=True)
                # Calculate the quartiles for the total occurrences by technology
                quartiles_tech_distribution = df_counts['count'].describe(percentiles=[.25, .5, .75])
                st.dataframe(quartiles_tech_distribution, use_container_width=False)

                # Display Bar Chart
                st.subheader(f"Bar Chart for {analysis_type}")
                fig = plt.figure(figsize=(12, 6))
                sns.barplot(x='count', y=column_to_analyze, data=df_counts_top.sort_values('count', ascending=False))
                plt.title(f'{analysis_type} {column_to_analyze} by Occurrence Count')
                plt.xlabel('Count of Occurrences')
                plt.ylabel(column_to_analyze)
                st.pyplot(fig)
                
                min_tot_count = st.slider("Select Min Total Count to Display", min_value=1, max_value=50, value=5)
                
                # Display Heatmap
                st.subheader(f"Heatmap for {analysis_type}")
                # Filter col where the total count is above min_tot_count
                col_above_min_count = df_counts[df_counts['count'] >= min_tot_count].sort_values('count', ascending=False)[column_to_analyze].tolist()
                # Filter the grouped DataFrame to include only these occ
                df_grouped_above_min_count = df[df[column_to_analyze].isin(col_above_min_count)]
                # Create a pivot table for the heatmap
                pivot_data = df_grouped_above_min_count.pivot_table(index=column_to_analyze, columns=column_to_group_by, values='Count').fillna(0)
                # Reorder the pivot table based on this sorted list
                pivot_data = pivot_data.reindex(col_above_min_count)

                fig = plt.figure(figsize=(18, 12))
                sns.heatmap(pivot_data.head(20), annot=True, cmap="coolwarm", cbar=True, fmt="g")
                plt.title(f"Count of Occurrences by Year for {analysis_type} {column_to_analyze}")
                plt.xlabel("Year of Occurrence")
                plt.ylabel(column_to_analyze)
                st.pyplot(fig)
            else:
                st.write("Upload a file, and select a column to analyze.")
        
        else:
            st.write("Please go to the 'Data Upload & Cleaning' tab to upload and clean data first.")

elif password != "":
    st.warning("Incorrect password. Please try again.")

