import streamlit as st
import pandas as pd
import json
import random
import time
from pathlib import Path

# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="AI 타로 리딩",
    page_icon="🔮",
    layout="wide"
)

# --------------------------------------------------
# 경로
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

csv_path = BASE_DIR / "tarot_card_meanings.csv"
json_path = BASE_DIR / "tarot-images.json"

image_dir = BASE_DIR / "images"
card_back = image_dir / "card_back.jpg"

# --------------------------------------------------
# 데이터 로드
# --------------------------------------------------
@st.cache_data
def load_data():

    df = pd.read_csv(csv_path)

    with open(json_path, encoding="utf-8") as f:
        tarot_json = json.load(f)

    return df, tarot_json

df, tarot_json = load_data()

# --------------------------------------------------
# JSON 카드 정보
# --------------------------------------------------
image_map = {}
card_info = {}

for card in tarot_json["cards"]:
    image_map[card["name"]] = card["img"]
    card_info[card["name"]] = card

# --------------------------------------------------
# CSV 카드 정보
# --------------------------------------------------
csv_info = {}

for _, row in df.iterrows():
    csv_info[str(row["card_name"]).strip()] = row

# --------------------------------------------------
# 제목
# --------------------------------------------------
st.title("🔮 AI 타로 리딩")

st.markdown("""
질문을 입력한 뒤 카드를 선택하세요.

카드는 미래를 예언하지 않으며
자기성찰과 재미를 위한 도구입니다.
""")

# --------------------------------------------------
# 질문
# --------------------------------------------------
reading_type = st.selectbox(
    "질문 유형",
    ["일반", "연애", "진로"]
)

question = st.text_area(
    "무엇이 궁금한가요?",
    placeholder="예) 올해 진로는 어떻게 될까요?"
)

# --------------------------------------------------
# 세션 상태
# --------------------------------------------------
if "deck_cards" not in st.session_state:
    st.session_state.deck_cards = None

if "selected_positions" not in st.session_state:
    st.session_state.selected_positions = []

# --------------------------------------------------
# 셔플
# --------------------------------------------------
if st.button("🃏 카드 셔플 시작"):

    if not question.strip():
        st.warning("질문을 입력해주세요.")
        st.stop()

    with st.spinner("카드를 섞는 중..."):
        time.sleep(2)

    all_cards = list(image_map.keys())

    st.session_state.deck_cards = random.sample(
        all_cards,
        21
    )

    st.session_state.selected_positions = []

# --------------------------------------------------
# 카드 선택 화면
# --------------------------------------------------
if st.session_state.deck_cards is not None:

    st.divider()

    st.subheader("21장의 카드 중 3장을 선택하세요")

    selected = st.multiselect(
        "카드 번호 선택",
        list(range(1, 22)),
        default=st.session_state.selected_positions,
        max_selections=3
    )

    st.session_state.selected_positions = selected

    # ---------------------------
    # 카드 진열
    # ---------------------------
    for row in range(3):

        cols = st.columns(7)

        for col in range(7):

            idx = row * 7 + col

            with cols[col]:

                st.image(
                    str(card_back),
                    use_container_width=True
                )

                st.caption(f"{idx+1}번")

    # ---------------------------
    # 카드 공개
    # ---------------------------
    if len(selected) == 3:

        st.divider()

        st.header("✨ 선택된 카드")

        positions = ["과거", "현재", "미래"]

        reveal_cols = st.columns(3)

        summary = []

        for i in range(3):

            selected_idx = selected[i] - 1

            card_name = st.session_state.deck_cards[selected_idx]

            orientation = random.choice(
                ["정방향", "역방향"]
            )

            image_file = image_map.get(card_name)

            csv_card = csv_info.get(card_name)

            if csv_card is not None:

                if reading_type == "연애":

                    meaning = str(
                        csv_card["love_meaning"]
                    )

                elif reading_type == "진로":

                    meaning = str(
                        csv_card["career_meaning"]
                    )

                else:

                    if orientation == "정방향":

                        meaning = str(
                            csv_card["upright_meaning"]
                        )

                    else:

                        meaning = str(
                            csv_card["reversed_meaning"]
                        )

            else:

                meaning = "해석 정보가 없습니다."

            with reveal_cols[i]:

                st.subheader(
                    positions[i]
                )

                image_path = (
                    image_dir / image_file
                )

                if image_path.exists():
                    st.image(
                        str(image_path),
                        use_container_width=True
                    )

                st.markdown(
                    f"**{card_name}**"
                )

                st.write(
                    f"({orientation})"
                )

                st.info(meaning)

            summary.append(
                f"{positions[i]} : {meaning}"
            )

        # -----------------------
        # 종합 리딩
        # -----------------------
        st.divider()

        st.header("🔮 종합 리딩")

        reading = f"""
질문 : {question}

{summary[0]}

{summary[1]}

{summary[2]}

세 장의 카드는 현재의 흐름과 앞으로의 가능성을 보여줍니다.

중요한 것은 카드보다 자신의 선택이며,
카드는 그 선택을 돌아보게 하는 조언자 역할을 합니다.
"""

        st.success(reading)

        # -----------------------
        # 키워드
        # -----------------------
        st.header("🔑 카드 키워드")

        keyword_set = []

        for num in selected:

            card_name = (
                st.session_state.deck_cards[num-1]
            )

            card = card_info.get(
                card_name,
                {}
            )

            if "keywords" in card:

                keyword_set.extend(
                    card["keywords"][:4]
                )

        keyword_set = list(
            dict.fromkeys(keyword_set)
        )

        if len(keyword_set) > 0:

            st.write(
                " · ".join(keyword_set)
            )

        # -----------------------
        # 질문
        # -----------------------
        st.header(
            "💭 스스로에게 던져볼 질문"
        )

        for num in selected:

            card_name = (
                st.session_state.deck_cards[num-1]
            )

            card = card_info.get(
                card_name,
                {}
            )

            if "Questions to Ask" in card:

                q_list = card[
                    "Questions to Ask"
                ]

                if len(q_list) > 0:

                    st.markdown(
                        f"- {random.choice(q_list)}"
                    )

        st.divider()

        st.caption(
            "본 결과는 오락 및 자기성찰 목적으로만 활용하세요."
        )
