import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(
    page_title="공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 공영주차장 정보 제공 서비스")

st.markdown("""
CSV 파일을 업로드하면

- 주소 검색
- 주차요금 확인
- 지도 시각화
- 마우스를 올리면 상세정보 확인

기능을 사용할 수 있습니다.
""")

uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded_file is None:
    st.info("CSV 파일을 업로드하세요.")
    st.stop()

# ----------------------------------------
# 데이터 읽기
# ----------------------------------------

try:
    df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, encoding="cp949")

# 숫자로 변환
df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

df = df.dropna(subset=["위도", "경도"])

st.success(f"{len(df)}개의 주차장 정보를 불러왔습니다.")

# ----------------------------------------
# 주소 검색
# ----------------------------------------

st.header("🔍 주소 검색")

keyword = st.text_input(
    "주소를 입력하세요",
    placeholder="예) 강동구"
)

if keyword:

    result = df[
        df["주소"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

else:

    result = df

st.write(f"검색 결과 : {len(result)}개")

# ----------------------------------------
# 검색 결과
# ----------------------------------------

st.header("📋 검색 결과")

if len(result) == 0:

    st.warning("검색 결과가 없습니다.")

else:

    for _, row in result.iterrows():

        with st.expander(row["주차장명"]):

            st.write(f"📍 주소 : {row['주소']}")
            st.write(f"💰 기본요금 : {row['기본요금']}")
            st.write(f"➕ 추가요금 : {row['추가요금']}")

# ----------------------------------------
# 지도
# ----------------------------------------

st.header("🗺️ 지도")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=result,
    get_position="[경도, 위도]",
    get_radius=35,
    get_fill_color=[0, 120, 255, 180],
    pickable=True,
    auto_highlight=True,
)

tooltip = {
    "html": """
    <b>{주차장명}</b><br/>
    <b>주소</b> : {주소}<br/>
    <b>기본요금</b> : {기본요금}<br/>
    <b>추가요금</b> : {추가요금}
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black"
    }
}

view_state = pdk.ViewState(
    latitude=result["위도"].mean(),
    longitude=result["경도"].mean(),
    zoom=11
)

st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    ),
    use_container_width=True
)

# ----------------------------------------
# 원본 데이터
# ----------------------------------------

with st.expander("원본 데이터 보기"):

    st.dataframe(
        result,
        use_container_width=True
    )
