import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="YouTube Studio Dashboard", page_icon="📊", layout="wide")

st.title("📊 YouTube Channel Analytics Dashboard")
st.write("A mini version of YouTube Studio built with Streamlit and YouTube Data API 💡")

# --- SIDEBAR INPUT ---
st.sidebar.header("🔑 API & Channel Setup")

api_key = st.secrets["YT_API_KEY"]
channel_id = st.sidebar.text_input("Enter Channel ID (e.g. UC_x5XG1OV2P6uZZ5FSM9Ttw):", value="")
refresh = st.sidebar.button("🔄 Refresh Data")

# --- FUNCTION TO FETCH CHANNEL DATA ---
def get_channel_data(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
    response = request.execute()

    if "items" not in response or len(response["items"]) == 0:
        return None, None

    channel = response["items"][0]
    uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    data = {
        "name": channel["snippet"]["title"],
        "description": channel["snippet"]["description"],
        "subscribers": int(channel["statistics"].get("subscriberCount", 0)),
        "views": int(channel["statistics"].get("viewCount", 0)),
        "videos": int(channel["statistics"].get("videoCount", 0)),
        "thumbnail": channel["snippet"]["thumbnails"]["default"]["url"]
    }
    return data, uploads_playlist

# --- FUNCTION TO FETCH TOP VIDEOS ---
def get_top_videos(api_key, playlist_id, limit=5):
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    next_page_token = None

    while len(videos) < limit:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            video_id = item["contentDetails"]["videoId"]
            title = item["snippet"]["title"]
            published = item["snippet"]["publishedAt"]

            stats_request = youtube.videos().list(part="statistics", id=video_id)
            stats_response = stats_request.execute()

            if stats_response["items"]:
                view_count = int(stats_response["items"][0]["statistics"].get("viewCount", 0))
                videos.append({
                    "Title": title,
                    "Views": view_count,
                    "Published": published[:10],
                    "Video Link": f"https://www.youtube.com/watch?v={video_id}"
                })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    df = pd.DataFrame(videos)
    df = df.sort_values(by="Views", ascending=False).head(limit)
    return df

# --- DISPLAY SECTION ---
if api_key and channel_id:
    if refresh or True:
        with st.spinner("Fetching data from YouTube..."):
            channel_data, playlist_id = get_channel_data(api_key, channel_id)

        if channel_data:
            # --- HEADER ---
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(channel_data["thumbnail"], width=100)
            with col2:
                st.subheader(channel_data["name"])
                st.write(channel_data["description"])

            st.markdown("---")

            # --- KPI METRICS ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Subscribers 👥", f"{channel_data['subscribers']:,}")
            c2.metric("Total Views 👀", f"{channel_data['views']:,}")
            c3.metric("Total Videos 🎥", f"{channel_data['videos']:,}")

            st.markdown("---")

            # --- TOP 5 VIDEOS ---
            st.subheader("🔥 Top 5 Most Viewed Videos")

            df_videos = get_top_videos(api_key, playlist_id)
            df_videos["Video Link"] = df_videos["Video Link"].apply(lambda x: f"[Watch Video]({x})")

            st.dataframe(df_videos, use_container_width=True)

            # --- VISUALIZATION ---
            st.subheader("📈 View Distribution of Top 5 Videos")
            fig = px.bar(df_videos, x="Title", y="Views", color="Views", text="Views",
                         labels={"Title": "Video Title", "Views": "View Count"},
                         title="Top 5 Videos by Views")
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            fig.update_layout(xaxis_tickangle=-45, height=500)
            st.plotly_chart(fig, use_container_width=True)

            st.success("✅ Data fetched successfully!")

        else:
            st.warning("⚠️ No channel found. Please check your Channel ID.")
else:
    st.info("🔎 Enter your API Key and Channel ID in the sidebar to begin.")

