import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os
import altair as alt


# --- Page Configuration ---
st.set_page_config(
    page_title="Ann Arbor Walkability Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- File Paths ---
# Use relative paths to the files you uploaded
SENTIMENT_FILE = 'reddit_with_sentiment.csv'
NEIGHBORHOOD_FILE = 'ann_arbor_neighborhood_walkability.csv'
MAP_FILE = 'ann_arbor_walkability_top_10.html'

# --- Caching Data ---
@st.cache_data
def load_data(file_path):
    """Loads a CSV file, handling potential errors."""
    if not os.path.exists(file_path):
        st.error(f"Error: File not found at {file_path}. Please make sure the file is in the same directory as the script.")
        return None
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None

@st.cache_data
def load_html_map(file_path):
    """Loads an HTML file from disk."""
    if not os.path.exists(file_path):
        st.error(f"Error: Map file not found at {file_path}. Please make sure the file is in the same directory.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None

# --- Load All Data ---
reddit_df = load_data(SENTIMENT_FILE)
neighborhood_df = load_data(NEIGHBORHOOD_FILE)
html_map = load_html_map(MAP_FILE)

# --- Main Application ---
st.title("Ann Arbor Walkability: A Two-Part Analysis")
st.markdown("""
By: Brighton Han\n
I wanted to explore walkability in Ann Arbor from multiple perspectives:
1.  **Public Sentiment:** What are people saying on Reddit (r/AnnArbor) about walkability, downtown access, and pedestrian issues?
2.  **Geospatial Data:** Which neighborhoods and street paths are objectively the most walkable based on network analysis from OpenStreetMap?
""")

st.divider()

# --- Part 1: Sentiment Analysis ---
st.header("Part 1: The Public's Voice - Reddit Sentiment")

if reddit_df is not None:
    st.markdown("""
    I analyzed posts and comments from the r/AnnArbor subreddit to gauge public opinion.
    Using VADER sentiment analysis, I assigned each comment a score from -1 (very negative) to +1 (very positive).
    """)

    # 1.1: Sentiment Distribution Histogram
    st.subheader("Sentiment Distribution")
    st.markdown("The histogram below shows the distribution of sentiment scores for Reddit comments related to walkability.")
    chart = alt.Chart(reddit_df).mark_bar().encode(
        alt.X("sentiment_score", bin=alt.Bin(maxbins=50), title="Sentiment Score"),
        alt.Y('count()', title="Number of Comments"),
        tooltip=["sentiment_score", "count()"]
    ).properties(
        title="Distribution of Reddit Sentiment Scores (All)"
    )


    st.altair_chart(chart, use_container_width=True)

    reddit_df0 = reddit_df[reddit_df['sentiment_score'] != 0]
    chart2 = alt.Chart(reddit_df0).mark_bar().encode(
        alt.X("sentiment_score", bin=alt.Bin(maxbins=50), title="Sentiment Score"),
        alt.Y('count()', title="Number of Comments"),
        tooltip=["sentiment_score", "count()"]
    ).properties(
        title="Distribution of Reddit Sentiment Scores (Without score 0)"
    )


    # Display the Altair chart in Streamlit
    st.altair_chart(chart2, use_container_width=True)
    st.markdown("Here, once I removed the comments with a sentiment score of 0, we can see a slight left" \
    " skewed distribution. Most of the people in these comments have a slightly positive sentiment" \
    " towards walkability in Ann Arbor. To see what specifically people are saying, take a look down below!")



    # 1.2: Most Positive and Negative Comments
    st.subheader("What are people saying?")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Most Positive Comments")
        # Filter for non-null text and sort
        positive_comments = reddit_df[reddit_df['text_to_analyze'].notna()].sort_values("sentiment_score", ascending=False).head(5)
        for _, row in positive_comments.iterrows():
            with st.expander(f"Score: {row['sentiment_score']:.2f} | Type: {row['type']}"):
                st.markdown(f"> {row['text_to_analyze']}")
                st.link_button("View Source", row['url'])

    with col2:
        st.markdown("#### Most Negative Comments")
        # Filter for non-null text and sort
        negative_comments = reddit_df[reddit_df['text_to_analyze'].notna()].sort_values("sentiment_score", ascending=True).head(5)
        for _, row in negative_comments.iterrows():
            with st.expander(f"Score: {row['sentiment_score']:.2f} | Type: {row['type']}"):
                st.markdown(f"> {row['text_to_analyze']}")
                st.link_button("View Source", row['url'])
    
    # 1.3: Raw Data Explorer
    if st.checkbox("Show Raw Sentiment Data"):
        st.dataframe(reddit_df)

else:
    st.warning("Could not load Reddit sentiment data to display this section.")

st.divider()

# --- Part 2: Geospatial Analysis ---
st.header("Part 2: The Objective Data - Neighborhood Walkability")

if neighborhood_df is not None:
    st.markdown("""
    Using OpenStreetMap data and the `osmnx` library, I calculated a 'walkability' score 
    (based on factors such as, street length, intersection density and green space proximity) for each street segment and aggregated these scores by neighborhood.
    """)
    
    # 2.1: Top 10 Neighborhoods Bar Chart
    st.subheader("Top 10 Most Walkable Neighborhoods")
    
    # Sort data for the chart
    top_10 = neighborhood_df.sort_values("weighted_walkability", ascending=False).head(10).sort_values("weighted_walkability", ascending=True)
    #st.bar_chart(data=top_10, x='neighborhood', y='weighted_walkability', use_container_width=True)
    df_sorted = top_10.sort_values("weighted_walkability", ascending=False)

    chart = (
        alt.Chart(df_sorted)
        .mark_bar()
        .encode(
            x=alt.X("weighted_walkability:Q", title="Weighted Walkability Score"),
            y=alt.Y("neighborhood_name:N", sort=None, title="Neighborhood"),
            tooltip=["neighborhood_name", "weighted_walkability"]
        )
        .properties(
            title="Top 10 Neighborhoods by Weighted Walkability Score",
            width='container'
        )
    )

    st.altair_chart(chart, use_container_width=True)

    # 2.2: Full Neighborhood Rankings Dataframe
    st.subheader("Full Neighborhood Rankings")
    st.dataframe(neighborhood_df)

else:
    st.warning("Could not load neighborhood walkability data to display this section.")

st.divider()

# --- Part 3: Map Visualization ---
st.header("Part 3: Visualizing Ann Arbor's Most Walkable Paths")

if html_map is not None:
    st.markdown("""
    This interactive map, generated from our `osmnx` analysis, shows the **top 10% most walkable street segments** in Ann Arbor.
    Brighter (yellow/red) paths indicate a higher walkability score. You can zoom in to explore specific streets and neighborhoods.
    """)
    
    # 3.1: Embed the HTML Map
    components.html(html_map, height=600, scrolling=True)

else:
    st.warning("Could not load the HTML map to display this section.")

st.divider()

# --- Conclusion ---
st.header("Conclusion")
st.markdown("""
I hope this helped you guys understand the way people *feel* about walkability and what the data *shows* about walkability. \n

I really wanted to compare what other people were saying about walkability with some objective measures from Open Street Map data
just to see how they compare. Overall, Ann Arbor is decently walkable. It's not the best but definitely not the worst.\n
 
From my perspective, as someone who's lived in Ann Arbor my entire life, I wouldn't say Ann Arbor is a "walkable" city, but it is a "bikeable" city.
There isn't a place in Ann Arbor where you could live your entire life within a 1 mile radius, like you probably could in NYC or LA or SF, 
but a 3 mile radius should be doable.\n

Let me know what you think about walkability in Ann Arbor!  
""")
