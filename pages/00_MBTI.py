import streamlit as st

# MBTI 추천 데이터
recommendations = {
    "INTJ": {
        "books": [
            "C: <생각의 탄생>",
            "C: <총균쇠>"
        ],
        "movies": [
            {"title": "인터스텔라", "poster": "https://m.media-amazon.com/images/I/71nJcZyQHDL._AC_SY679_.jpg"},
            {"title": "이미테이션 게임", "poster": None}
        ]
    },
    "INTP": {
        "books": [
            "C: <코스모스>",
            "C: <사피엔스>"
        ],
        "movies": [
            {"title": "매트릭스", "poster": "https://m.media-amazon.com/images/I/51EG732BV3L._AC_SY679_.jpg"},
            {"title": "인셉션", "poster": None}
        ]
    },
    "ENTJ": {
        "books": [
            "C: <손자병법>",
            "C: <칭기즈칸>"
        ],
        "movies": [
            {"title": "월 스트리트", "poster": "https://m.media-amazon.com/images/I/81eR8t2jcFL._AC_SL1500_.jpg"},
            {"title": "머니볼", "poster": None}
        ]
    },
    "ENTP": {
        "books": [
            "C: <호모 데우스>",
            "C: <괴델, 에셔, 바흐>"
        ],
        "movies": [
            {"title": "아이언맨", "poster": "https://m.media-amazon.com/images/I/81w0Jc7sQ3L._AC_SL1500_.jpg"},
            {"title": "셜록 홈즈", "poster": None}
        ]
    },
    "INFJ": {
        "books": [
            "C: <연금술사>",
            "C: <데미안>"
        ],
        "movies": [
            {"title": "어바웃 타임", "poster": "https://m.media-amazon.com/images/I/71w+PFl9z0L._AC_SY606_.jpg"},
            {"title": "인생은 아름다워", "poster": None}
        ]
    },
    "INFP": {
        "books": [
            "C: <너의 췌장을 먹고 싶어>",
            "C: <시네마 천국>"
        ],
        "movies": [
            {"title": "월-E", "poster": "https://m.media-amazon.com/images/I/81z8XZGqerL._AC_SY679_.jpg"},
            {"title": "코코", "poster": None}
        ]
    },
    "ENFJ": {
        "books": [
            "C: <사람을 얻는 기술>",
            "C: <하버드 사람들은 어떻게 명확하게 말하는가>"
        ],
        "movies": [
            {"title": "파운더", "poster": "https://m.media-amazon.com/images/I/61YNuYeMoDL._AC_SY679_.jpg"},
            {"title": "히든 피겨스", "poster": None}
        ]
    },
    "ENFP": {
        "books": [
            "C: <가벼움의 시대>",
            "C: <지적 대화를 위한 넓고 얕은 지식>"
        ],
        "movies": [
            {"title": "라라랜드", "poster": "https://m.media-amazon.com/images/I/81jKnz8dOFp._AC_SY679_.jpg"},
            {"title": "월터의 상상은 현실이 된다", "poster": None}
        ]
    },
    "ISTJ": {
        "books": [
            "C: <원칙>",
            "C: <나는 어떻게 일하는가>"
        ],
        "movies": [
            {"title": "덩케르크", "poster": "https://m.media-amazon.com/images/I/91vZt+8CAEL._AC_SL1500_.jpg"},
            {"title": "체르노빌(시리즈)", "poster": None}
        ]
    },
    "ISFJ": {
        "books": [
            "C: <죽은 시인의 사회>",
            "C: <미움받을 용기>"
        ],
        "movies": [
            {"title": "인턴", "poster": "https://m.media-amazon.com/images/I/71C2q5ogZ0L._AC_SY679_.jpg"},
            {"title": "월터의 상상은 현실이 된다", "poster": None}
        ]
    },
    "ESTJ": {
        "books": [
            "C: <성공하는 사람들의 7가지 습관>",
            "C: <원씽>"
        ],
        "movies": [
            {"title": "미션 임파서블", "poster": "https://m.media-amazon.com/images/I/71MK7pjdAlL._AC_SY879_.jpg"},
            {"title": "글래디에이터", "poster": None}
        ]
    },
    "ESFJ": {
        "books": [
            "C: <하트 시그널>",
            "C: <말 그릇>"
        ],
        "movies": [
            {"title": "러브 액츄얼리", "poster": "https://m.media-amazon.com/images/I/71+vJkEpQfL._AC_SY679_.jpg"},
            {"title": "굿윌헌팅", "poster": None}
        ]
    },
    "ISTP": {
        "books": [
            "C: <오리지널스>",
            "C: <괴짜 경제학>"
        ],
        "movies": [
            {"title": "007 스카이폴", "poster": "https://m.media-amazon.com/images/I/81GEXZcYH9L._AC_SY679_.jpg"},
            {"title": "본 시리즈", "poster": None}
        ]
    },
    "ISFP": {
        "books": [
            "C: <바람의 그림자>",
            "C: <모모>"
        ],
        "movies": [
            {"title": "가디언즈 오브 갤럭시", "poster": "https://m.media-amazon.com/images/I/91YQgWcxdRL._AC_SY679_.jpg"},
            {"title": "500일의 썸머", "poster": None}
        ]
    },
    "ESTP": {
        "books": [
            "C: <부자 아빠 가난한 아빠>",
            "C: <넛지>"
        ],
        "movies": [
            {"title": "분노의 질주", "poster": "https://m.media-amazon.com/images/I/81HFqRSbVwL._AC_SY679_.jpg"},
            {"title": "테이큰", "poster": None}
        ]
    },
    "ESFP": {
        "books": [
            "C: <배움의 발견>",
            "C: <파티피플>"
        ],
        "movies": [
            {"title": "맘마미아!", "poster": "https://m.media-amazon.com/images/I/81KXOkGg91L._AC_SY879_.jpg"},
            {"title": "위대한 쇼맨", "poster": None}
        ]
    }
}

st.title("📚 MBTI 책 & 영화 추천 🍿")

mbti = st.selectbox("당신의 MBTI는?", list(recommendations.keys()))

if mbti:
    st.subheader(f"📖 책 추천 for {mbti}")
    for book in recommendations[mbti]["books"]:
        st.write(book)

    st.subheader(f"🎬 영화 추천 for {mbti}")
    
    # 첫번째 영화 포스터 이미지
    movie1 = recommendations[mbti]["movies"][0]
    st.write(movie1["title"])
    if movie1["poster"]:
        st.image(movie1["poster"], width=250)

    # 두번째 영화는 텍스트만
    movie2 = recommendations[mbti]["movies"][1]
    st.write(movie2["title"])
