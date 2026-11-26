import time
import streamlit as st
from google import genai
from google.genai import types

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="나만의 교육 소감문 도우미",
    page_icon="✍️",
    layout="centered"
)

# 2. Gemini API 클라이언트 연결 (Streamlit Secrets에서 gemini_api 키 불러오기)
try:
    api_key = st.secrets["gemini_api"]
    client = genai.Client(api_key=api_key)
except KeyError:
    st.error("⚠️ Streamlit Secrets에 'gemini_api' 키가 설정되어 있지 않습니다. Settings > Secrets에서 키를 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ API 초기화 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 초기화용 카운터 설정
if "reset_id" not in st.session_state:
    st.session_state["reset_id"] = 0

reset_id = st.session_state["reset_id"]

# 4. 30개 핵심 단어 및 뜻 데이터 정의 (카테고리별 구성)
KEYWORDS_DICT = {
    "💡 깨달음과 인식 변화": [
        "깨달음 (몰랐던 사실이나 가치를 새롭게 알게 됨)",
        "경각심 (위험이나 문제에 대해 주의를 기울여 경계하는 마음)",
        "소중함 (매우 귀중하게 여기는 가치)",
        "중요성 (핵심이 되어 꼭 필요한 성질)",
        "역사의식 (과거의 사실을 바탕으로 현재와 미래를 바라보는 태도)",
        "편견 (한쪽으로 치우친 공정하지 못한 생각)",
        "고정관념 (잘 변하지 않는 굳어진 생각)"
    ],
    "🤝 공감과 태도": [
        "존중 (남을 높이어 귀중하게 대함)",
        "배려 (도와주거나 보살펴 주려고 마음을 씀)",
        "공감 (남의 감정이나 생각에 자기도 그렇다고 느낌)",
        "포용 (남을 너그럽게 감싸 주거나 받아들임)",
        "책임감 (맡아서 해야 할 임무를 중히 여기는 마음)",
        "감사함 (고맙게 여기는 마음)",
        "희생 (다른 사람이나 목적을 위해 자신을 바침)"
    ],
    "🔥 실천과 다짐": [
        "실천 (생각한 바를 실제로 행함)",
        "노력 (목적을 이루기 위해 몸과 마음을 다해 애씀)",
        "변화 (사물의 성질, 모양, 상태 따위가 바뀌어 달라짐)",
        "관심 (어떤 것에 마음이 끌려 주의를 기울임)",
        "기억 (이전의 인상이나 경험을 의식 속에 간직함)",
        "계승 (조상의 전통이나 문화유산 따위를 물려받아 이어 나감)",
        "수호 (지키고 보호함)",
        "동참 (같은 생각이나 행동으로 함께 참여함)"
    ],
    "🌍 사회 및 환경적 가치": [
        "안전 (위험이 생기거나 사고가 날 염려가 없음)",
        "예방 (질병이나 재해 따위가 일어나기 전에 미리 대처하여 막음)",
        "권리 (어떤 일을 행하거나 누릴 수 있는 마땅한 자격)",
        "평등 (권리, 의무, 자격 등이 차별 없이 고르고 한결같음)",
        "지속가능성 (미래 세대의 필요를 저해하지 않으면서 현재의 필요를 충족하는 것)",
        "공동체 (생활이나 운명 따위를 함께하는 조직체)",
        "화합 (뜻이 맞아 서로 친하게 어울림)",
        "성찰 (자기의 마음을 반성하고 살핌)"
    ]
}

# 5. 화면 UI 구성
st.title("✍️ 나만의 교육 소감문 작성 도우미")
st.markdown("교육 주제와 내가 느낀 핵심 키워드를 선택하면, **나만의 진정성 있는 소감문 초안**을 만들어 줍니다.")
st.divider()

# [입력 1] 교육 주제 및 희망 글자 수
st.subheader("1️⃣ 기본 정보 입력")
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input(
        "교육(행사) 주제를 입력하세요",
        placeholder="예: 학교폭력 예방 교육, 장애인식개선 교육, 기후위기와 환경보호 등",
        key=f"topic_input_{reset_id}"
    )

with col2:
    target_length = st.number_input(
        "희망 글자 수 (공백 포함)",
        min_value=100,
        max_value=2000,
        value=400,
        step=50,
        help="100자부터 2,000자까지 50자 단위로 설정할 수 있습니다.",
        key=f"target_length_input_{reset_id}"
    )

st.divider()

# [입력 2] 30개 핵심 단어 선택 (최소 5개 ~ 최대 20개)
st.subheader("2️⃣ 핵심 단어 선택 (5개 ~ 20개)")
st.caption("소감문에 꼭 담고 싶은 단어를 **최소 5개에서 최대 20개까지** 골라주세요.")

selected_items = []

for category, words in KEYWORDS_DICT.items():
    with st.expander(category, expanded=True):
        for word in words:
            if st.checkbox(word, key=f"kw_{reset_id}_{word}"):
                selected_items.append(word)

num_selected = len(selected_items)
if num_selected < 5:
    st.warning(f"현재 **{num_selected}개** 선택됨 (최소 **5개** 이상 선택해야 합니다. 앞으로 {5 - num_selected}개 더 골라주세요!)")
elif num_selected > 20:
    st.error(f"현재 **{num_selected}개** 선택됨 (최대 **20개**까지만 선택할 수 있습니다. {num_selected - 20}개를 해제해 주세요!)")
else:
    st.success(f"현재 **{num_selected}개** 선택됨 (적절한 개수입니다!)")

st.divider()

# [입력 3] 학생 개인의 생각 추가 입력
st.subheader("3️⃣ 나만의 경험 및 생각 추가 (선택 사항)")
extra_thought = st.text_area(
    "인상 깊었던 장면, 나의 전공/진로와의 연결점, 간단한 느낀 점 등을 자유롭게 적어주세요.",
    placeholder="예: 영상 속 피해 학생의 인터뷰가 가장 기억에 남았다. 앞으로 친구의 말에 더 귀 기울이는 태도를 가져야겠다고 생각했다.",
    height=100,
    key=f"extra_thought_input_{reset_id}"
)

st.divider()

# 6. 소감문 생성 버튼 및 결과 출력
generate_btn = st.button("✨ 소감문 생성하기", type="primary", use_container_width=True)

if generate_btn:
    if not topic.strip():
        st.error("❗ 교육 주제를 먼저 입력해 주세요.")
    elif num_selected < 5:
        st.error(f"❗ 핵심 단어를 최소 5개 이상 선택해 주세요. (현재 {num_selected}개 선택됨)")
    elif num_selected > 20:
        st.error(f"❗ 핵심 단어를 최대 20개 이하로 선택해 주세요. (현재 {num_selected}개 선택됨)")
    else:
        clean_keywords = [item.split(" (")[0] for item in selected_items]
        keywords_str = ", ".join(clean_keywords)

        prompt = f"""
당신은 학생의 눈높이에 맞춰 자연스럽고 진정성 있는 교육 소감문을 작성해 주는 글쓰기 도우미입니다.
아래 조건에 맞춰 학생이 직접 쓴 것처럼 자연스러운 소감문을 작성해 주세요.

[작성 조건]
1. 교육 주제: {topic}
2. 목표 글자 수: 공백 포함 약 {target_length}자 내외 (목표 글자 수의 ±15% 이내로 분량을 꼭 맞춰주세요.)
3. 반드시 포함할 핵심 단어 ({len(clean_keywords)}개): {keywords_str}
   - 위 핵심 단어들이 문맥 속에 억지스럽지 않고 자연스럽게 녹아들도록 작성하세요.
4. 학생이 추가로 입력한 내용: {extra_thought if extra_thought.strip() else "없음 (교육 주제와 핵심 단어를 바탕으로 자연스럽게 구성)"}
5. 문체 및 어조:
   - 학생이 학교 교육이나 특강을 들은 후 제출하는 소감문 어조('~했다', '~느꼈다', '~다짐했다' 등의 자연스러운 소감문 문체)를 사용하세요.
   - 너무 딱딱한 번역투나 AI가 쓴 티가 나는 과장된 표현은 피하고, 솔직하고 진정성 있게 작성하세요.
   - 제목이나 불필요한 인사말 없이 소감문 본문만 출력하세요.
"""

        with st.spinner("선택한 단어를 엮어 멋진 소감문을 작성하고 있습니다..."):
            try:
                max_retries = 3
                response = None

                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.7,
                            )
                        )
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if "503" in error_msg or "UNAVAILABLE" in error_msg:
                            if attempt < max_retries - 1:
                                time.sleep(2 * (attempt + 1))
                                continue
                        raise e

                st.session_state["generated_essay"] = response.text.strip()
                st.session_state["generated_target_length"] = target_length

            except Exception as e:
                st.error(f"소감문 생성 중 오류가 발생했습니다: {e}")

# 생성된 소감문이 있을 때 화면 출력 및 초기화 버튼 표시
if "generated_essay" in st.session_state and st.session_state["generated_essay"]:
    result_text = st.session_state["generated_essay"]
    saved_target = st.session_state.get("generated_target_length", target_length)

    st.subheader("📝 완성된 소감문")

    char_with_space = len(result_text)
    char_without_space = len(result_text.replace(" ", "").replace("\n", ""))

    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("공백 포함 글자 수", f"{char_with_space}자", f"목표 {saved_target}자")
    col_stat2.metric("공백 제외 글자 수", f"{char_without_space}자")

    st.info("💡 아래 박스 **오른쪽 위의 복사 아이콘(📋)**을 누르면 전체 내용이 한 번에 복사됩니다!")

    st.code(result_text, language=None, wrap_lines=True)

    st.caption("⚠️ 생성된 글은 초안입니다. 복사한 뒤 자신의 생각과 표현으로 조금씩 다듬어 제출해 보세요!")

    if st.button("🔄 초기화하기", use_container_width=True):
        st.session_state["reset_id"] += 1
        st.session_state["generated_essay"] = ""
        st.rerun()
