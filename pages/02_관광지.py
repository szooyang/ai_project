# streamlit_seoul_top10_app.py
# Streamlit app that shows "Top 10 Seoul tourist spots popular with foreigners" using Folium.
# Save this file to your repo and deploy on Streamlit Cloud.

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Seoul Top10 (for foreigners)", layout="wide")

st.title("Seoul: Top 10 Tourist Spots Popular with Foreigners 🇰🇷")
st.markdown("Pick places on the left to filter the map. Click markers for short info and a link.")

# Top 10 spots data (name, lat, lon, short description, link)
TOP10 = [
    {
        "name": "Gyeongbokgung Palace",
        "lat": 37.579617,
        "lon": 126.977041,
        "desc": "The largest royal palace of the Joseon dynasty. Must-see historical site.",
        "link": "https://en.wikipedia.org/wiki/Gyeongbokgung",
    },
    {
        "name": "Bukchon Hanok Village",
        "lat": 37.582604,
        "lon": 126.983059,
        "desc": "Traditional hanok houses in a preserved neighborhood between palaces.",
        "link": "https://en.wikipedia.org/wiki/Bukchon_Hanok_Village",
    },
    {
        "name": "Namsan / N Seoul Tower",
        "lat": 37.5511694,
        "lon": 126.9882266,
        "desc": "Iconic tower with panoramic views of Seoul.",
        "link": "https://en.wikipedia.org/wiki/N_Seoul_Tower",
    },
    {
        "name": "Myeongdong Shopping Street",
        "lat": 37.563757,
        "lon": 126.986124,
        "desc": "Bustling shopping district famous for cosmetics, street food, and fashion.",
        "link": "https://en.wikipedia.org/wiki/Myeongdong",
    },
    {
        "name": "Insadong",
        "lat": 37.574097,
        "lon": 126.985156,
        "desc": "Cultural street known for antiques, tea houses, and crafts.",
        "link": "https://en.wikipedia.org/wiki/Insadong",
    },
    {
        "name": "Hongdae (Hongik University area)",
        "lat": 37.556230,
        "lon": 126.923941,
        "desc": "Youthful area with street performers, indie culture, cafes, and nightlife.",
        "link": "https://en.wikipedia.org/wiki/Hongdae",
    },
    {
        "name": "Dongdaemun Design Plaza (DDP)",
        "lat": 37.5662952,
        "lon": 127.0090436,
        "desc": "Futuristic design complex and major shopping area.",
        "link": "https://en.wikipedia.org/wiki/Dongdaemun_Design_Plaza",
    },
    {
        "name": "Lotte World Tower & Mall",
        "lat": 37.513087,
        "lon": 127.101257,
        "desc": "Tall skyscraper with observation deck, shopping, and aquarium.",
        "link": "https://en.wikipedia.org/wiki/Lotte_World_Tower",
    },
    {
        "name": "Changdeokgung Palace & Huwon",
        "lat": 37.579529,
        "lon": 126.991020,
        "desc": "UNESCO World Heritage site notable for its secret garden.",
        "link": "https://en.wikipedia.org/wiki/Changdeokgung",
    },
    {
        "name": "COEX Mall & Starfield Library (Gangnam)",
        "lat": 37.512070,
        "lon": 127.058556,
        "desc": "Large underground mall, aquarium, and the famous Starfield Library.",
        "link": "https://en.wikipedia.org/wiki/COEX_Mall",
    },
]

# Sidebar controls
st.sidebar.header("Controls")
show_cluster = st.sidebar.checkbox("Use marker cluster", value=True)
search_place = st.sidebar.text_input("Search place (type and press Enter)")
selected_place = st.sidebar.selectbox("Jump to a place (or choose 'All')",
                                      options=["All"] + [p["name"] for p in TOP10])

# Filter by search
if search_place:
    filtered = [p for p in TOP10 if search_place.lower() in p["name"].lower()]
else:
    filtered = TOP10.copy()

# If a specific place selected, zoom to it
if selected_place != "All":
    filtered = [p for p in TOP10 if p["name"] == selected_place]

# Create folium map centered in Seoul
seoul_center = [37.5665, 126.9780]
m = folium.Map(location=seoul_center, zoom_start=12)

if show_cluster:
    marker_cluster = MarkerCluster().add_to(m)

for idx, place in enumerate(filtered, start=1):
    popup_html = f"<b>{place['name']}</b><br>{place['desc']}<br><a href=\"{place['link']}\" target=\"_blank\">More info</a>"
    marker = folium.Marker(location=[place["lat"], place["lon"]], popup=popup_html,
                           tooltip=f"{idx}. {place['name']}")
    if show_cluster:
        marker.add_to(marker_cluster)
    else:
        marker.add_to(m)

# If a specific place was selected, re-center map
if selected_place != "All" and filtered:
    m.location = [filtered[0]["lat"], filtered[0]["lon"]]
    m.zoom_start = 15

# Render map with streamlit_folium
st_data = st_folium(m, width=900, height=600)

# Show list of Top10 with short descriptions and external links in the app
st.subheader("Top 10 (short list)")
cols = st.columns(2)
for i, place in enumerate(TOP10):
    with cols[i % 2]:
        st.markdown(f"**{i+1}. {place['name']}**")
        st.write(place["desc"])
        st.markdown(f"[More info]({place['link']})")

st.markdown("---")
st.caption("Data: curated list — places commonly popular with international visitors to Seoul.")


# EOF

# Below is the recommended requirements.txt content. Create a separate file named 'requirements.txt'
# and paste these lines into it (the canvas also includes it for your convenience):
# === requirements.txt ===
# streamlit
# folium
# streamlit-folium
# pandas
# === end of requirements.txt ===
