import streamlit as st
import urllib.parse
import urllib.request
import json

st.set_page_config(page_title="MBTI 추천 도서 & 영화", layout="centered")
st.title("📚🎬 MBTI별 도서 & 영화 추천")
st.write("너의 MBTI를 고르면 취향저격 추천을 해줄게! 😎")

# ======================
# 데이터 매핑
# ======================
mbti_media = {
    "ISTJ": ("Demian", "Hermann Hesse", "Inception", "Inception_(film)"),
    "ISFJ": ("Little Women", "Louisa May Alcott", "Frozen", "Frozen_(2013_film)"),
    "INFJ": ("The Alchemist", "Paulo Coelho", "About Time", "About_Time_(2013_film)"),
    "INTJ": ("Sapiens", "Yuval Noah Harari", "Interstellar", "Interstellar"),
    "ISTP": ("Momo", "Michael Ende", "The Bourne Identity", "The_Bourne_Identity_(film)"),
    "ISFP": ("Almond", "Son Won-pyung", "La La Land", "La_La_Land"),
    "INFP": ("Harry Potter and the Sorcerer's Stone", "J. K. Rowling", "WALL·E", "WALL-E"),
    "INTP": ("Cosmos", "Carl Sagan", "The Social Network", "The_Social_Network"),
    "ESTP": ("Silent Spring", "Rachel Carson", "Avatar", "Avatar_(2009_film)"),
    "ESFP": ("The Midnight Library", "Matt Haig", "Mamma Mia!", "Mamma_Mia!"),
    "ENFP": ("The Courage to Be Disliked", "Ichiro Kishimi", "Zootopia", "Zootopia"),
    "ENTP": ("Guns, Germs, and Steel", "Jared Diamond", "Iron Man", "Iron_Man_(2008_film)"),
    "ESTJ": ("Trend Korea", "Various", "Moneyball", "Moneyball"),
    "ESFJ": ("The Art of Loving", "Erich Fromm", "The Intern", "The_Intern_(2015_film)"),
    "ENFJ": ("Justice: What's the Right Thing to Do?", "Michael J. Sandel", "Good Will Hunting", "Good_Will_Hunting"),
    "ENTJ": ("The One Thing", "Gary Keller", "The Dark Knight", "The_Dark_Knight_(film)"),
}

PLACEHOLDER = "https://via.placeholder.com/300x450?text=No+Image"

# ======================
# Helper Functions
# ======================
def fetch_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def get_book_cover_url(title, author=None):
    try:
        q = f"intitle:{title}"
        if author:
            q += f"+inauthor:{author}"
        q = urllib.parse.quote(q)
        url = f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=5"
        data = fetch_json(url)

        if data and "items" in data:
            for item in data["items"]:
                info = item.get("volumeInfo", {})
                imgs = info.get("imageLinks", {})
                if "thumbnail" in imgs:
                    return imgs["thumbnail"].replace("http://", "https://")
                if "smallThumbnail" in imgs:
                    return imgs["smallThumbnail"].replace("http://", "https://")
    except Exception:
        pass
    return None

def get_movie_poster_url_from_wikipedia(page_title):
    try:
        slug = urllib.parse.quote(page_title)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
        data = fetch_json(url)

        if data:
            if "originalimage" in data and "source" in data["originalimage"]:
                return data["originalimage"]["source"]
            if "thumbnail" in data and "source" in data["thumbnail"]:
                return data["thumbnail"]["source"]
    except Exception:
        pass
    return None

def generate_one_line_book_review(mbti, title):
    if mbti in ("INFJ","INTJ","INFP","INTP"):
        return f"『{title}』은(는) 너의 깊은 생각과 감성을 촉촉하게 적셔줄 책! ✨"
    if mbti in ("ISTJ","ISFJ","ISFP","ISTP"):
        return f"『{title}』은(는) 현실적이면서도 마음을 울리는 스토리! 💛"
    if mbti in ("ENFP","ENTP","ENTJ","ENFJ"):
        return f"『{title}』은(는) 인생에 새로운 관점을 선물할 책! 🔥"
    return f"『{title}』 — 누구든 빠져들 수 있는 매력적인 책! 📖"

def generate_one_line_movie_review(mbti, title):
    if mbti in ("INTJ","ENTJ","INTP"):
        return f"『{title}』 — 두뇌 풀가동하며 보면 꿀잼 인정! 🧩"
    if mbti in ("INFP","ISFP","ESFP","ENFP"):
        return f"『{title}』 — 감성 제대로 자극하는 잔잔한 여운 🎞️"
    if mbti in ("ESTP","ENTP","ESTJ","ENFJ"):
        return f"『{title}』 — 에너지 풀 충전되는 텐션 UP 영화 🔥"
    return f"『{title}』 — 집중하면 더 재밌는 명작 🍿"

# ======================
# UI
# ======================
selected_mbti = st.selectbox("👉 MBTI 선택!", sorted(mbti_media.keys()))

if selected_mbti:
    book_title, book_author, movie_title, movie_wiki = mbti_media[selected_mbti]

    st.markdown(f"## ✨ {selected_mbti} 추천 콘텐츠")

    col_book, col_movie = st.columns(2)

    # --- BOOK ---
    with col_book:
        st.subheader("📚 책")
        st.write(f"**{book_title}** — _{book_author}_")

        img = get_book_cover_url(book_title, book_author)
        if not img:
            img = get_book_cover_url(book_title)
        if not img:
            img = PLACEHOLDER

        st.image(img, use_column_width=True)
        st.caption(generate_one_line_book_review(selected_mbti, book_title))

    # --- MOVIE ---
    with col_movie:
        st.subheader("🎬 영화")
        st.write(f"**{movie_title}**")

        poster = get_movie_poster_url_from_wikipedia(movie_wiki)
        if not poster:
            poster = PLACEHOLDER

        st.image(poster, use_column_width=True)
        st.caption(generate_one_line_movie_review(selected_mbti, movie_title))

    st.write("---")
    st.info("이미지 안 뜨는 경우 말해줘! 더 좋은 데이터로 바로 고쳐줄게 😆🔥")
