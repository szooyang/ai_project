# streamlit_mbti_images_robust.py
import streamlit as st
import urllib.parse
import urllib.request
import json
from typing import Optional

st.set_page_config(page_title="MBTI 추천 (이미지 개선판)", layout="centered")
st.title("📚🎬 MBTI별 도서·영화 추천 (이미지 안정화 버전)")
st.write("이미지 안 뜨는 문제를 줄이려고 여러 API/방법으로 표지·포스터를 시도해요. 그래도 안 뜨면 알려줘! 😅")

# -------------------------
# 데이터: MBTI -> (book_title, book_author, movie_title, movie_wiki_slug_hint)
# movie_wiki_slug_hint는 가능한 위키페이지 슬러그 예시(없으면 영화 제목)
# -------------------------
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

# 안전한 placeholder (적당히 보이는 이미지)
PLACEHOLDER = "https://via.placeholder.com/300x450?text=No+Image"

# -------------------------
# 네트워크 헬퍼 (User-Agent, timeout)
# -------------------------
def urlopen_json(url: str, timeout: int = 8) -> Optional[dict]:
    """주어진 URL에 GET 요청 -> JSON decode. 실패 시 None 반환."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Streamlit App)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8"))
    except Exception:
        return None

def urlopen_bytes(url: str, timeout: int = 8) -> Optional[bytes]:
    """이미지 등 바이트로 가져오고 싶은 경우(디버그용). 실패 시 None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Streamlit App)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None

# -------------------------
# 책 표지 찾기: Google Books -> Open Library
# -------------------------
@st.cache_data(show_spinner=False)
def get_book_cover_google(title: str, author: Optional[str] = None) -> Optional[str]:
    """Google Books API로 thumbnail 찾기"""
    try:
        q = f"intitle:{title}"
        if author:
            q += f"+inauthor:{author}"
        q = urllib.parse.quote(q)
        url = f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=8"
        data = urlopen_json(url)
        if not data:
            return None
        # 우선순위: volumeInfo.imageLinks.thumbnail -> smallThumbnail
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            imgs = info.get("imageLinks", {})
            # thumbnail 자주 존재
            thumb = imgs.get("thumbnail") or imgs.get("smallThumbnail")
            if thumb:
                # https로 통일
                return thumb.replace("http://", "https://")
    except Exception:
        return None
    return None

@st.cache_data(show_spinner=False)
def get_book_cover_openlibrary(title: str, author: Optional[str] = None) -> Optional[str]:
    """
    OpenLibrary 검색: search.json?q=title+author -> use cover_i -> https://covers.openlibrary.org/b/id/{cover_i}-L.jpg
    This is a robust fallback when Google Books fails.
    """
    try:
        q = title
        if author:
            q += " " + author
        q = urllib.parse.quote(q)
        url = f"https://openlibrary.org/search.json?title={q}&limit=8"
        data = urlopen_json(url)
        if not data:
            return None
        docs = data.get("docs", [])
        for d in docs:
            cover_id = d.get("cover_i")
            if cover_id:
                return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        # 시도 2: general search
        url2 = f"https://openlibrary.org/search.json?q={urllib.parse.quote(title)}&limit=8"
        data2 = urlopen_json(url2)
        if data2:
            for d in data2.get("docs", []):
                if d.get("cover_i"):
                    return f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg"
    except Exception:
        return None
    return None

def get_book_image(title: str, author: Optional[str] = None) -> str:
    """순차적으로 시도해서 표지 URL 반환. 실패하면 PLACEHOLDER 반환."""
    # 1) Google Books (title+author)
    img = get_book_cover_google(title, author)
    if img:
        return img
    # 2) Google Books (title only)
    img = get_book_cover_google(title, None)
    if img:
        return img
    # 3) OpenLibrary (title+author)
    img = get_book_cover_openlibrary(title, author)
    if img:
        return img
    # 4) OpenLibrary (title only)
    img = get_book_cover_openlibrary(title, None)
    if img:
        return img
    # 실패
    return PLACEHOLDER

# -------------------------
# 영화 포스터 찾기: Wikipedia REST summary 시도 (en/ko), 다양한 슬러그 형식 시도
# -------------------------
@st.cache_data(show_spinner=False)
def try_wikipedia_summary_image(lang: str, page_slug: str) -> Optional[str]:
    """
    Wikipedia REST API summary endpoint:
    https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}
    returns JSON that may include 'originalimage' or 'thumbnail'
    """
    try:
        slug = urllib.parse.quote(page_slug)
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}"
        data = urlopen_json(url)
        if not data:
            return None
        # originalimage has higher-res
        oi = data.get("originalimage")
        if oi and oi.get("source"):
            return oi["source"]
        thumb = data.get("thumbnail")
        if thumb and thumb.get("source"):
            return thumb["source"]
    except Exception:
        return None
    return None

def generate_wikipedia_candidates(title: str, hint_slug: Optional[str] = None):
    """
    가능한 wiki 페이지 slug 후보들을 반환.
    시도 순서: hint_slug, title, title + ' (film)', title + ' (movie)', title with underscores
    """
    candidates = []
    if hint_slug:
        candidates.append(hint_slug)
    # raw title variants
    candidates.append(title)
    candidates.append(title.replace(" ", "_"))
    candidates.append(f"{title}_(film)")
    candidates.append(f"{title}_(movie)")
    # also try removing punctuation (basic)
    cleaned = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    if cleaned and cleaned != title:
        candidates.append(cleaned)
        candidates.append(cleaned.replace(" ", "_"))
        candidates.append(f"{cleaned}_(film)")
    # unique preserving order
    seen = set()
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out

def get_movie_image(title: str, hint_slug: Optional[str] = None) -> str:
    """
    다국어(영어, 한국어) 위키 요약을 여러 후보로 시도해서 포스터 URL 얻기.
    실패하면 PLACEHOLDER 반환.
    """
    # 후보 슬러그
    candidates = generate_wikipedia_candidates(title, hint_slug)
    # languages to try (en then ko)
    langs = ["en", "ko"]
    for lang in langs:
        for slug in candidates:
            img = try_wikipedia_summary_image(lang, slug)
            if img:
                return img
    # 마지막으로, 간단히 검색 API로 가장 유력한 페이지만 시도해보는 방법(English opensearch)
    try:
        search_q = urllib.parse.quote(title)
        opensearch_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search_q}&limit=5&format=json"
        data = urlopen_json(opensearch_url)
        if data and isinstance(data, list) and len(data) >= 2:
            # data[1]는 제목 리스트
            for candidate_title in data[1]:
                # convert to slug
                slug = candidate_title.replace(" ", "_")
                img = try_wikipedia_summary_image("en", slug)
                if img:
                    return img
    except Exception:
        pass
    # 실패
    return PLACEHOLDER

# -------------------------
# 간단한 한줄 리뷰 생성기 (같은 톤 유지)
# -------------------------
def gen_book_one_liner(mbti: str, title: str) -> str:
    if mbti.startswith("IN") or mbti in ("INTJ","INTP"):
        return f"『{title}』 — 생각을 넓혀주는 책이라 깊이 몰두하기 좋아. ✨"
    if mbti.startswith("IS") or mbti.startswith("ES"):
        return f"『{title}』 — 감성이랑 공감이 살아있는 편안한 이야기야. 💛"
    if mbti.startswith("EN") or mbti in ("ENTJ","ENTP"):
        return f"『{title}』 — 새로운 관점과 에너지를 주는 추천작! 🔥"
    return f"『{title}』 — 재밌고 마음에 남는 작품이야. 📖"

def gen_movie_one_liner(mbti: str, title: str) -> str:
    if mbti in ("INTJ","INTP","ENTP"):
        return f"『{title}』 — 두뇌 풀가동해서 보면 더 재미있어! 🧩"
    if mbti.startswith("IS") or mbti.startswith("IN"):
        return f"『{title}』 — 감성적 여운이 큰 영화야. 🎞️"
    if mbti.startswith("ES") or mbti.startswith("EN"):
        return f"『{title}』 — 텐션 높은 장면이 많아서 신나게 볼 수 있어! 🔥"
    return f"『{title}』 — 몰입도 높은 작품이라 추천해. 🍿"

# -------------------------
# UI
# -------------------------
selected_mbti = st.selectbox("👉 MBTI 선택!", sorted(mbti_media.keys()))
if selected_mbti:
    book_title, book_author, movie_title, movie_hint = mbti_media[selected_mbti]
    st.markdown(f"## ✨ {selected_mbti} 추천 콘텐츠")

    col1, col2 = st.columns([1, 1])

    # BOOK
    with col1:
        st.subheader("📚 책")
        st.write(f"**{book_title}** — _{book_author}_")
        st.caption("표지를 여러 소스에서 찾아오고 있어요... (GoogleBooks → OpenLibrary)")

        book_img = get_book_image(book_title, book_author)
        st.image(book_img, use_column_width=True)
        st.write(gen_book_one_liner(selected_mbti, book_title))

        # 디버그용: 직접 이미지 URL 확인/수정 가능 (사용자에게 보이게 선택적으로)
        if st.checkbox("표지 URL 직접 보기/수정 (디버그용)"):
            url_in = st.text_input("표지 URL (수정하려면 붙여넣기)", value=book_img)
            if url_in:
                st.image(url_in, use_column_width=True)

    # MOVIE
    with col2:
        st.subheader("🎬 영화")
        st.write(f"**{movie_title}**")
        st.caption("포스터를 여러 위키/슬러그로 시도 중 (en/ko 위키)")

        movie_img = get_movie_image(movie_title, movie_hint)
        st.image(movie_img, use_column_width=True)
        st.write(gen_movie_one_liner(selected_mbti, movie_title))

        if st.checkbox("포스터 URL 직접 보기/수정 (디버그용)", key="movie_debug"):
            url_in2 = st.text_input("포스터 URL (수정하려면 붙여넣기)", value=movie_img, key="movie_url_input")
            if url_in2:
                st.image(url_in2, use_column_width=True)

    st.write("---")
    st.info("이미지가 여전히 안 뜨면 알려줘! 제목-저자(또는 영화 한글/영어 제목)을 알려주면 내가 슬러그를 직접 매핑해줄게 😊")

# -------------------------
# 끝
# -------------------------
