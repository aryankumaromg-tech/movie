import streamlit as st
import pandas as pd
import pickle
import requests
import time

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide"
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
    <style>
        /* Background */
        .stApp {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: white;
        }

        /* Title */
        .main-title {
            text-align: center;
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #f72585, #7209b7, #3a0ca3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #a0a0b0;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        /* Movie cards */
        .movie-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 12px;
            text-align: center;
            transition: transform 0.2s;
            backdrop-filter: blur(10px);
        }

        .movie-card:hover {
            transform: translateY(-5px);
            border-color: #f72585;
        }

        .movie-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #ffffff;
            margin-top: 8px;
            line-height: 1.3;
        }

        /* Selectbox label */
        .stSelectbox label {
            color: #a0a0b0 !important;
            font-size: 1rem;
        }

        /* Button */
        .stButton > button {
            background: linear-gradient(90deg, #f72585, #7209b7);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 0.6rem 2.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            width: 100%;
            transition: opacity 0.2s;
        }

        .stButton > button:hover {
            opacity: 0.85;
        }

        /* Divider */
        .divider {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #f72585, transparent);
            margin: 2rem 0;
        }

        /* Section heading */
        .section-heading {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1rem;
        }

        /* Stats bar */
        .stat-box {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .stat-number {
            font-size: 2rem;
            font-weight: 800;
            color: #f72585;
        }

        .stat-label {
            font-size: 0.8rem;
            color: #a0a0b0;
        }

        /* Search history tag */
        .history-tag {
            display: inline-block;
            background: rgba(247, 37, 133, 0.15);
            border: 1px solid #f72585;
            border-radius: 20px;
            padding: 4px 14px;
            margin: 4px;
            font-size: 0.8rem;
            color: #f72585;
        }

        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# ─── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open("similarity.pkl", "rb"))
    return movies, similarity

movies, similarity = load_data()


# ─── Fetch Poster ──────────────────────────────────────────────
@st.cache_data
def fetch_poster(movie_id, retries=3, delay=2):
    url = 'https://api.themoviedb.org/3/movie/{}?api_key=3535afd859e558188f655ea4be0fd63b&language=en-US'.format(movie_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        except requests.exceptions.ConnectionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return "https://via.placeholder.com/500x750?text=No+Poster"
        except (KeyError, requests.exceptions.HTTPError):
            return "https://via.placeholder.com/500x750?text=No+Poster"


# ─── Fetch Movie Details ────────────────────────────────────────
@st.cache_data
def fetch_details(movie_id):
    url = 'https://api.themoviedb.org/3/movie/{}?api_key=3535afd859e558188f655ea4be0fd63b&language=en-US'.format(movie_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        return {
            "rating": round(data.get("vote_average", 0), 1),
            "year": data.get("release_date", "N/A")[:4],
            "overview": data.get("overview", "No description available."),
            "genres": [g["name"] for g in data.get("genres", [])],
        }
    except Exception:
        return {"rating": "N/A", "year": "N/A", "overview": "N/A", "genres": []}


# ─── Recommend ─────────────────────────────────────────────────
def recommend(movie, num=5):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:num+1]
    recommended_movies, recommended_posters, recommended_ids = [], [], []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))
        recommended_ids.append(movie_id)
    return recommended_movies, recommended_posters, recommended_ids


# ─── Session State ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []


# ─── Header ────────────────────────────────────────────────────
st.markdown('<div class="main-title">🎬 CineMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover your next favourite film</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─── Stats Bar ─────────────────────────────────────────────────
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.markdown(f'''<div class="stat-box">
        <div class="stat-number">{len(movies)}</div>
        <div class="stat-label">Movies in Database</div>
    </div>''', unsafe_allow_html=True)
with col_s2:
    st.markdown(f'''<div class="stat-box">
        <div class="stat-number">{len(st.session_state.history)}</div>
        <div class="stat-label">Searches Made</div>
    </div>''', unsafe_allow_html=True)
with col_s3:
    st.markdown(f'''<div class="stat-box">
        <div class="stat-number">{len(st.session_state.watchlist)}</div>
        <div class="stat-label">In Your Watchlist</div>
    </div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─── Controls ──────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    selected_movie_name = st.selectbox(
        '🎥 Search for a movie you like:',
        movies['title'].values
    )
with col_right:
    num_recommendations = st.slider("Results", min_value=3, max_value=10, value=5)

_, col_btn, _ = st.columns([2, 1, 2])
with col_btn:
    recommend_btn = st.button('✨ Recommend')


# ─── Results ───────────────────────────────────────────────────
if recommend_btn:
    if selected_movie_name not in st.session_state.history:
        st.session_state.history.append(selected_movie_name)

    with st.spinner('Finding your perfect matches...'):
        names, posters, ids = recommend(selected_movie_name, num=num_recommendations)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-heading">Because you liked <span style="color:#f72585">{selected_movie_name}</span>...</div>', unsafe_allow_html=True)

    cols = st.columns(num_recommendations)
    for col, name, poster, movie_id in zip(cols, names, posters, ids):
        details = fetch_details(movie_id)
        with col:
            st.markdown(f'''
                <div class="movie-card">
                    <img src="{poster}" style="width:100%; border-radius:10px;">
                    <div class="movie-title">{name}</div>
                    <div style="color:#f72585; font-size:0.8rem; margin-top:4px;">
                        ⭐ {details["rating"]} &nbsp;|&nbsp; 📅 {details["year"]}
                    </div>
                    <div style="color:#a0a0b0; font-size:0.7rem; margin-top:6px;">
                        {" · ".join(details["genres"][:2]) if details["genres"] else ""}
                    </div>
                </div>
            ''', unsafe_allow_html=True)

            if st.button(f"+ Watchlist", key=f"wl_{movie_id}"):
                if name not in st.session_state.watchlist:
                    st.session_state.watchlist.append(name)
                    st.success(f"Added {name}!")


# ─── Tabs: History & Watchlist ──────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🕘 Search History", "📌 My Watchlist"])

with tab1:
    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.markdown(f'<span class="history-tag">🎬 {h}</span>', unsafe_allow_html=True)
    else:
        st.caption("No searches yet.")

with tab2:
    if st.session_state.watchlist:
        for i, w in enumerate(st.session_state.watchlist):
            col_w1, col_w2 = st.columns([4, 1])
            with col_w1:
                st.markdown(f'<span class="history-tag">🎥 {w}</span>', unsafe_allow_html=True)
            with col_w2:
                if st.button("Remove", key=f"rm_{i}"):
                    st.session_state.watchlist.remove(w)
                    st.rerun()
    else:
        st.caption("Your watchlist is empty.")