import datetime
import random
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

# 페이지 기본 설정
st.set_page_config(
    page_title="대한민국 축제 지도 & 룰렛",
    page_icon="🎉",
    layout="wide"
)

# API 키 로드 (Streamlit Secrets 활용)
API_KEY = st.secrets.get("TOUR_API_KEY", "")

# 지역 코드 매핑
AREA_CODES = {
    "전국": "",
    "서울": "1", "인천": "2", "대전": "3", "대구": "4",
    "광주": "5", "부산": "6", "울산": "7", "세종": "8",
    "경기": "31", "강원": "32", "충북": "33", "충남": "34",
    "전북": "35", "전남": "36", "경북": "37", "경남": "38", "제주": "39"
}

@st.cache_data(ttl=3600)
def fetch_festivals(start_date: str, area_code: str = ""):
    """한국관광공사 TourAPI 4.0 행사정보조회 API 호출"""
    if not API_KEY:
        st.error("API 키가 설정되지 않았습니다. Secrets 설정을 확인하세요.")
        return []

    # 공공데이터포털 특성에 따른 URL 파라미터 조립
    endpoint = "http://apis.data.go.kr/B551011/KorService1/searchFestival1"
    
    # URL 인코딩 중복 방지를 위한 직접 조립 방식 사용
    req_url = (
        f"{endpoint}?serviceKey={API_KEY}"
        f"&numOfRows=100&pageNo=1&MobileOS=ETC&MobileApp=StreamlitApp"
        f"&_type=json&listYN=Y&arrange=A&eventStartDate={start_date}"
    )
    if area_code:
        req_url += f"&areaCode={area_code}"

    try:
        response = requests.get(req_url, timeout=10)
        res_data = response.json()
        items = res_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        if isinstance(items, dict):
            items = [items]
        return items
    except Exception as e:
        st.error(f"데이터 수신 실패: {e}")
        return []

def calculate_dday(start_date_str):
    """YYYYMMDD 문자열 기준 D-Day 계산"""
    try:
        target_date = datetime.datetime.strptime(start_date_str, "%Y%m%d").date()
        today = datetime.date.today()
        diff = (target_date - today).days
        if diff == 0:
            return "🔥 오늘 개막!"
        elif diff > 0:
            return f"⏳ D-{diff}"
        else:
            return "🎈 진행 중"
    except Exception:
        return ""

# 메인 UI
st.title("🎉 대한민국 전국 축제 탐험대")
st.caption("한국관광공사 TourAPI 데이터 기반 축제 검색 및 랜덤 추천 서비스")

# 사이드바 필터
st.sidebar.header("🔍 검색 필터")
selected_region = st.sidebar.selectbox("지역 선택", list(AREA_CODES.keys()))
search_date = st.sidebar.date_input("기준 날짜 선택", datetime.date.today())

date_str = search_date.strftime("%Y%m%d")
region_code = AREA_CODES[selected_region]

# 데이터 호출
festivals = fetch_festivals(date_str, region_code)

if not festivals:
    st.info("해당 조건의 축제 정보가 존재하지 않거나 API 키 설정이 올바르지 않습니다.")
    st.stop()

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🎯 오늘의 랜덤 축제 룰렛", "🗺️ 전국 축제 지도", "📋 축제 목록 보기"])

# ----------------------------------------------------
# TAB 1: 재미 기능 - 축제 랜덤 룰렛
# ----------------------------------------------------
with tab1:
    st.subheader("🎲 어디 갈지 모르겠다면? 랜덤 룰렛!")
    st.write("버튼을 누르면 현재 조건에 맞는 축제 중 하나를 무작위로 추천해 드립니다.")
    
    if st.button("🎲 축제 추천받기", type="primary"):
        selected = random.choice(festivals)
        st.balloons()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            img_url = selected.get("firstimage") or "https://via.placeholder.com/400x300?text=No+Image"
            st.image(img_url, use_column_width=True)
        with col2:
            st.markdown(f"### {selected.get('title')}")
            dday = calculate_dday(selected.get('eventstartdate', ''))
            st.write(f"**상태:** {dday}")
            st.write(f"**기간:** {selected.get('eventstartdate')} ~ {selected.get('eventenddate')}")
            st.write(f"**주소:** {selected.get('addr1', '정보 없음')}")
            if selected.get('tel'):
                st.write(f"**문의:** {selected.get('tel')}")

# ----------------------------------------------------
# TAB 2: 지도 기반 시각화 (Folium)
# ----------------------------------------------------
with tab2:
    st.subheader("🗺️ 축제 위치 지도")
    
    # 좌표 정보가 있는 항목 필터링
    valid_coords = [
        f for f in festivals 
        if f.get('mapx') and f.get('mapy')
    ]
    
    if valid_coords:
        # 지도 중심점 설정 (첫 번째 결과 기준)
        avg_lat = float(valid_coords[0]['mapy'])
        avg_lng = float(valid_coords[0]['mapx'])
        
        m = folium.Map(location=[avg_lat, avg_lng], zoom_start=10)
        
        for f in valid_coords:
            lat = float(f['mapy'])
            lng = float(f['mapx'])
            title = f.get('title', '축제')
            addr = f.get('addr1', '')
            
            popup_html = f"<b>{title}</b><br>{addr}"
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=title,
                icon=folium.Icon(color="red", icon="star")
            ).add_to(m)
            
        st_folium(m, width=1000, height=500)
    else:
        st.warning("지도에 표시할 위치 정보(좌표)가 없습니다.")

# ----------------------------------------------------
# TAB 3: 그리드형 카드 목록
# ----------------------------------------------------
with tab3:
    st.subheader(f"📋 총 {len(festivals)}개의 축제가 검색되었습니다.")
    
    # 3열 카드 레이아웃
    cols = st.columns(3)
    for idx, f in enumerate(festivals):
        with cols[idx % 3]:
            st.markdown("---")
            img_url = f.get("firstimage") or "https://via.placeholder.com/300x200?text=No+Image"
            st.image(img_url, use_column_width=True)
            st.markdown(f"#### {f.get('title')}")
            
            dday = calculate_dday(f.get('eventstartdate', ''))
            st.caption(f"{dday} | {f.get('eventstartdate')} ~ {f.get('eventenddate')}")
            st.text(f.get('addr1', '주소 미제공'))
