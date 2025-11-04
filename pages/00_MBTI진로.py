import streamlit as st

st.set_page_config(page_title="MBTI 진로 추천 봇", page_icon="🎯")

st.title("🎯 MBTI 진로 추천 봇")
st.write("너의 MBTI에 맞는 찰떡 진로를 추천해줄게! 😎")

mbti_options = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

# MBTI 선택하기
selected_mbti = st.selectbox("너의 MBTI를 골라줘!", mbti_options)

# MBTI별 진로 데이터
careers = {
    "INTJ": ["데이터 과학자 🤖", "전략 기획자 📊"],
    "INTP": ["연구원 🧪", "시스템 개발자 🧑‍💻"],
    "ENTJ": ["경영 컨설턴트 🏢", "프로덕트 매니저 📈"],
    "ENTP": ["벤처 창업가 🚀", "크리에이티브 디렉터 🎬"],
    "INFJ": ["심리 상담가 💬", "작가 ✍️"],
    "INFP": ["콘텐츠 크리에이터 🎨", "사회복지사 🤝"],
    "ENFJ": ["교사 👩‍🏫", "홍보 전문가 📣"],
    "ENFP": ["광고 기획자 📺", "이벤트 플래너 🎉"],
    "ISTJ": ["회계사 📚", "공무원 🏛️"],
    "ISFJ": ["간호사 🏥", "교육 행정가 🗂️"],
    "ESTJ": ["프로젝트 매니저 🧱", "군 장교 🎖️"],
    "ESFJ": ["호텔리어 🏨", "인사 담당자 👥"],
    "ISTP": ["엔지니어 🔧", "보안 전문가 🔐"],
    "ISFP": ["디자이너 🎨", "사진 작가 📷"],
    "ESTP": ["영업 전문가 💼", "기자 📰"],
    "ESFP": ["배우 🎭", "연예 기획자 ⭐"]
}

if selected_mbti:
    st.subheader(f"✨ {selected_mbti} 유형 추천 진로 ✨")
    for job in careers[selected_mbti]:
        st.write(f"- {job}")

    st.write("\n너한테 꼭 맞는 멋진 꿈을 향해 GO! 🚀🔥")
