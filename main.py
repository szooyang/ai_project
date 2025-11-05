import streamlit as st
st.title('나의 첫 웹 서비스 만들기!')
a=st.text_input('이름을 입력해주세요')
b=st.selectbox('좋아하는 음식을 선택하세요!',['오페라케이크','된장찌개','까르보나라'])
if st.button('인사말 생성'):
  st.info(a+'님, 안녕하세요! 반갑습니다!')
  st.warning(b+'를 좋아하시는군요! 저도 좋아해요!')
  st.error('반가워요!!')
  st.balloons()
