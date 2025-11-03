# streamlit_mbti_final.py
import streamlit as st
import urllib.parse
import urllib.request
import json
from typing import Optional

st.set_page_config(page_title="MBTI 책&영화 추천", layout="centered")
st.title("📚🎬 MBTI별 맞춤 책 & 영화 추천!")

st.write("이미지 문제 개선! 책은 텍스트 중심, 영화 마지막 작품만 포스터 보여줘요 😄")

# --------------------------------------
# 추천 데이터 (책 2 + 영화 2)
# --------------------------------------
mbti_media = {
    "ISTJ": {
        "books": [
            ("데미안", "헤르만 헤세"),
            ("총, 균, 쇠", "재레드 다이아몬드")
        ],
        "movies": [
            ("인셉션", "Inception"),
            ("인터스텔라", "Interstellar")
        ]
    },
    "INFJ": {
        "books": [
            ("연금술사", "파울로 코엘료"),
            ("멈추면, 비로소 보이는 것들", "혜민 스님")
        ],
        "movies": [
            ("어바웃 타임", "About Time_(2013_film)"),
            ("월-E", "WALL-E")
        ]
    },
    "INFP": {
        "books": [
            ("해리 포터와 마법사의 돌", "J. K. 롤링"),
            ("미드나잇 라이브러리", "매트 헤이그")
        ],
        "movies": [
            ("조제, 호랑이 그리고 물고기들", "Josee,_the_Tiger_and_the_Fish"),
            ("라라랜드", "La_La_Land")
        ]
    },
    "INTJ": {
        "books": [
            ("사피엔스", "유발 하라리"),
            ("코스모스", "칼 세이건")
        ],
        "movies": [
            ("다크 나이트", "The_Dark_Knight_(film)"),
            ("인터스텔라", "Interstellar")
        ]
    },
}

PLACEHOLDER = "https://via.placeholder.com/300x450?text=No+Poster"

# --------------------------------------
# 영화 포스터 가져오기 (Wikipedia)
# --------------------------------------
@st.cache_data(show_spinner=False)
def get_movie_poster(title_slug: str) -> Optional[str]:
    """영화 포스터를 Wikipedia Summary API로 가져오기"""
    try:
        slug = urllib.parse.quote(title_slug)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "originalimage" in data:
                return data["originalimage"]["source"]
            if "thumbnail" in data:
                return data["thumbnail"]["source"]
    except Exception:
        return None
    return None

# --------------------------------------
# 한 줄 서평 & 영화평 생성
# --------------------------------------
def gen_book_comment(title: str) -> str:
    return f"『{title}』 — 너만의 감정을 더 깊게 들여다볼 수 있을걸? ✨"

def gen_movie_comment(title: str) -> str:
    return f"『{title}』 — 분위기 푹 빠져서 보면 인생영화 될 수도! 🎬"


# --------------------------------------
# UI
# --------------------------------------
selected_mbti = st.selectbox("👉 MBTI 선택!", sorted(mbti_media.keys()))

if selected_mbti:
    st.write("---")
    st.markdown(f"## 🌟 {selected_mbti} 추천 세트 🌟")

    rec = mbti_media[selected_mbti]

    # BOOKS
    st.subheader("📚 책 추천 2선")
    for title, author in rec["books"]:
        st.markdown(f"**{title}** — _{author}_")
        st.write(gen_book_comment(title))
        st.write("")  # spacing

    st.write("---")

    # MOVIES
    st.subheader("🎬 영화 추천 2선")

    # 첫 번째: 포스터 없음
    first_movie_name, _ = rec["movies"][0]
    st.markdown(f"**🎞 {first_movie_name}** (텍스트 추천)")
    st.write(gen_movie_comment(first_movie_name))
    st.write("")

    # 두 번째: 포스터 있음
    second_movie_name, slug = rec["movies"][1]
    st.markdown(f"**🍿 {second_movie_name}** (포스터 맞춰왔지!)")
    poster = get_movie_poster(slug)
    if poster:
        st.image(poster, use_column_width=True)
    else:
        st.image(PLACEHOLDER, use_column_width=True)
    st.write(gen_movie_comment(second_movie_name))

    st.write("---")
    st.success("추천 끝! 더 원하는 MBTI도 골라봐 😄")
