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
From nightly walks with my mom during COVID to helping lower post meal blood glucose levels, walking has always been a big part of my life.
Walking has showed me how much our surroundings influence our feelings of saftey, beloning and calm. But, this also made me
wonder, *what actually makes a city walkable?*\n
This project was my attempt to answer that question systematically. I wanted to turn something meaningful into something measureable. \n
Here is how I did it:
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

#-- Part 4: My perspective --
st.header("Part 4: My perspective")
st.markdown("""
As someone who has lived in Ann Arbor their entire life, here is my two cents:\n

I wouldn't say Ann Arbor is a *walkable* city, but it is definitely a *bikeable* one. There isn't anywhere in Ann Arbor where 
you could realistically live your entire life within a one-mile radius the way you might in New York City, Los Angeles, or San Francisco.
But a three-mile radius? That’s doable, and that’s exactly where biking becomes essential.\n

Let’s take an ideal day in my life as an example. As a college student at U-M, I live in South Quad (in my opinion, the best one). 
If I didn’t have a dining hall downstairs, I’d take the quick 10-minute walk over to The Hen on E. Washington and get a lox sandwich. 
Afterward, I’d walk back to South Quad (probably listening to The Daily or Planet Money) and study for a few hours.\n

Once I start to lose focus, I take a 10 minute walk to the IM building for a workout to clear my head. But when I get back to my dorm, 
I realize I’m out of milk and pasta sauce.
This is where Ann Arbor shifts from being walkable to bikeable. The closest decent-sized grocery store is Meijer on Ann 
Arbor–Saline Road, more than 3 miles away. My options are:
• walk for an hour,
• wait 30 minutes for a bus,
• or… bike.

Biking is the only transportation method that isn’t either physically exhausting or extremely time-consuming. It’s the perfect middle ground.\n

Pickleball is another great example. It’s become one of my favorite new activities, but the closest pickleball courts to downtown 
Ann Arbor are also nearly 3 miles away. Too far to walk, and similarly inconvenient by bus. Yet it’s a quick, easy bike ride.\n

And that’s really the point: Ann Arbor’s scale sits in an awkward middle zone. It’s too spread out to function as a truly walkable 
city, but compact enough that biking unlocks everything—groceries, recreation, campus life, and the parts of the city that make 
living here fun.
""")

st.divider()

# --- Conclusion ---
st.header("Conclusion")
st.markdown("""
I hope this helped you understand the way people feel about walkability and what the data shows about walkability.\n
I really wanted to compare what residents were saying about walkability with objective measures from OpenStreetMap, just to see 
how the lived experience matches the underlying infrastructure.\n 
And overall, Ann Arbor is decently walkable. 
It’s not the best, but it’s definitely not the worst; it sits in that middle space where walking works for some things, 
but biking fills in the gaps.\n

Let me know what you think about walkability in Ann Arbor!
""")
