import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import os

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
MAP_FILE = 'ann_arbor_walkability_top_10%.html'

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
This presentation explores walkability in Ann Arbor by combining two different perspectives:
1.  **Public Sentiment:** What are people saying on social media (r/AnnArbor) about walkability, downtown access, and pedestrian issues?
2.  **Geospatial Data:** Which neighborhoods and street paths are objectively the most walkable based on network analysis from OpenStreetMap?
""")

st.divider()

# --- Part 1: Sentiment Analysis ---
st.header("Part 1: The Public's Voice - Reddit Sentiment")

if reddit_df is not None:
    st.markdown("""
    We analyzed posts and comments from the r/AnnArbor subreddit to gauge public opinion.
    Using VADER sentiment analysis, each comment was assigned a score from -1 (very negative) to +1 (very positive).
    """)

    # 1.1: Sentiment Distribution Histogram
    fig_hist = px.histogram(
        reddit_df,
        x="sentiment_score",
        title="Distribution of Reddit Sentiment Scores (Compound)",
        nbins=50,
        labels={"sentiment_score": "Sentiment Score", "count": "Number of Comments"}
    )
    st.plotly_chart(fig_hist, use_container_width=True)

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
    Using OpenStreetMap data and the `osmnx` library, we calculated a 'walkability' score 
    (based on network closeness centrality) for each street segment and aggregated these scores by neighborhood.
    """)
    
    # 2.1: Top 10 Neighborhoods Bar Chart
    st.subheader("Top 10 Most Walkable Neighborhoods")
    
    # Sort data for the chart
    top_10 = neighborhood_df.sort_values("weighted_walkability", ascending=False).head(10).sort_values("weighted_walkability", ascending=True)
    
    fig_bar = px.bar(
        top_10,
        y="neighborhood_name",
        x="weighted_walkability",
        orientation='h',
        title="Top 10 Neighborhoods by Weighted Walkability Score",
        labels={"neighborhood_name": "Neighborhood", "weighted_walkability": "Weighted Walkability Score"}
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)
    
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
This analysis combines what people *feel* about walkability with what the data *shows*. 
We can see a vibrant public discussion with both strong positive and negative sentiments, 
which can provide context for *why* certain areas are used or avoided.

This public feedback is complemented by a clear, data-driven ranking of neighborhood walkability, 
and a street-level map that pinpoints the most connected and accessible paths in the city.
""")