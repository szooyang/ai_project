import streamlit as st

st.set_page_config(page_title="MBTI 추천 도서 & 영화 🎬📚")

st.title("📚 MBTI별 책 & 영화 추천 🎬")
st.write("너의 MBTI를 선택하면 취향저격 추천을 해줄게! 😎")

# MBTI 리스트
mbti_list = [
    "ISTJ","ISFJ","INFJ","INTJ",
    "ISTP","ISFP","INFP","INTP",
    "ESTP","ESFP","ENFP","ENTP",
    "ESTJ","ESFJ","ENFJ","ENTJ"
]

# MBTI별 책/영화 데이터
recommend_data = {
    "ISTJ": {
        "books": ["🔹 데미안 - 헤르만 헤세", "🔹 총, 균, 쇠 - 재러드 다이아몬드"],
        "movies": ["🎬 인셉션", "🎬 셜록 홈즈"]
    },
    "ISFJ": {
        "books": ["🔹 작은 아씨들 - 루이자 메이 올컷", "🔹 파친코 - 이민진"],
        "movies": ["🎬 플립", "🎬 겨울왕국"]
    },
    "INFJ": {
        "books": ["🔹 연금술사 - 파울로 코엘료", "🔹 죽음에 관하여 - 어빈 얄롬"],
        "movies": ["🎬 어바웃 타임", "🎬 월터의 상상은 현실이 된다"]
    },
    "INTJ": {
        "books": ["🔹 인간 본성에 대하여 - 스티븐 핑커", "🔹 사피엔스 - 유발 하라리"],
        "movies": ["🎬 인터스텔라", "🎬 매트릭스"]
    },
    "ISTP": {
        "books": ["🔹 모모 - 미하엘 엔데", "🔹 나는 나로 살기로 했다 - 김수현"],
        "movies": ["🎬 분노의 질주", "🎬 본 아이덴티티"]
    },
    "ISFP": {
        "books": ["🔹 아몬드 - 손원평", "🔹 보건교사 안은영 - 정세랑"],
        "movies": ["🎬 비긴 어게인", "🎬 라라랜드"]
    },
    "INFP": {
        "books": ["🔹 나미야 잡화점의 기적 - 히가시노 게이고", "🔹 해리 포터 - J.K. 롤링"],
        "movies": ["🎬 월-E", "🎬 코코"]
    },
    "INTP": {
        "books": ["🔹 코스모스 - 칼 세이건", "🔹 생각에 관한 생각 - 다니엘 카너먼"],
        "movies": ["🎬 소셜 네트워크", "🎬 트루먼 쇼"]
    },
    "ESTP": {
        "books": ["🔹 침묵의 봄 - 레이첼 카슨", "🔹 82년생 김지영 - 조남주"],
        "movies": ["🎬 아바타", "🎬 007 스카이폴"]
    },
    "ESFP": {
        "books": ["🔹 달러구트 꿈 백화점 - 이미예", "🔹 미드나잇 라이브러리 - 매트 헤이그"],
        "movies": ["🎬 맘마미아!", "🎬 인사이드 아웃"]
    },
    "ENFP": {
        "books": ["🔹 미움받을 용기 - 기시미 이치로", "🔹 오늘도 펭수, 내일도 펭수"],
        "movies": ["🎬 해리 포터 시리즈", "🎬 주토피아"]
    },
    "ENTP": {
        "books": ["🔹 총, 균, 쇠 - 재러드 다이아몬드", "🔹 멀티플라이어 - 주창윤"],
        "movies": ["🎬 아이언맨", "🎬 빅쇼트"]
    },
    "ESTJ": {
        "books": ["🔹 1cm 다이빙 - 태수,문지민", "🔹 트렌드 코리아",],
        "movies": ["🎬 캡틴 아메리카", "🎬 머니볼"]
    },
    "ESFJ": {
        "books": ["🔹 훈민정음의 길 - 신영복", "🔹 사랑의 기술 - 에리히 프롬"],
        "movies": ["🎬 인턴", "🎬 사랑과 영혼"]
    },
    "ENFJ": {
        "books": ["🔹 정의란 무엇인가 - 마이클 샌델", "🔹 멈추면, 비로소 보이는 것들 - 혜민"],
        "movies": ["🎬 굿 윌 헌팅", "🎬 리틀 포레스트"]
    },
    "ENTJ": {
        "books": ["🔹 원씽 - 게리 켈러", "🔹 넛지 - 탈러 & 선스타인"],
        "movies": ["🎬 다크 나이트", "🎬 킹스맨"]
    },
}

# 사용자 선택
selected_mbti = st.selectbox("👉 MBTI 선택!", mbti_list)

if selected_mbti:
    st.subheader(f"✨ {selected_mbti}에게 추천하는 책 📚")
    for b in recommend_data[selected_mbti]["books"]:
        st.write(b)

    st.subheader(f"🎬 {selected_mbti}에게 추천하는 영화 🍿")
    for m in recommend_data[selected_mbti]["movies"]:
        st.write(m)

    st.write("👉 마음에 드는 작품 하나 골라서 오늘 도전해볼래? 😆🔥")
