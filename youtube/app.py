import re
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
from googleapiclient.discovery import build
from wordcloud import WordCloud

# ---------------------------------------------------------
# 1. 한글 폰트 자동 설정 (Streamlit Cloud 환경 대응)
# ---------------------------------------------------------
FONT_PATH = "NanumGothic.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"

@st.cache_resource
def load_korean_font():
    """Streamlit Cloud 환경에서 한글 깨짐 방지를 위해 폰트 파일을 다운로드합니다."""
    if not os.path.exists(FONT_PATH):
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
    return FONT_PATH

font_p = load_korean_font()
plt.rc("font", family="NanumGothic")
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------
# 2. 유틸리티 함수 (유튜브 URL 파싱 및 API 호출)
# ---------------------------------------------------------
def extract_video_id(url: str) -> str:
    """다양한 유형의 유튜브 URL에서 Video ID를 추출합니다."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/|v\/|youtu.be\/|\/shorts\/)([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_comments(api_key: str, video_id: str, max_results: int) -> pd.DataFrame:
    """YouTube Data API v3를 활용해 최신 댓글을 수집합니다."""
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    next_page_token = None

    while len(comments) < max_results:
        fetch_count = min(100, max_results - len(comments))
        
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=fetch_count,
            pageToken=next_page_token,
            order="time"  # 최신순 수집
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": snippet.get("authorDisplayName"),
                "comment": snippet.get("textOriginal"),
                "published_at": snippet.get("publishedAt"),
                "like_count": snippet.get("likeCount", 0)
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    df = pd.DataFrame(comments)
    if not df.empty:
        df["published_at"] = pd.to_datetime(df["published_at"])
    return df

def analyze_sentiment_simple(text: str) -> str:
    """규칙 기반의 간단한 한글 반응도 분석 함수입니다."""
    positive_words = ["좋아", "최고", "감사", "대박", "유익", "사랑", "응원", "완벽", "재밌", "추천", "Good", "good", "짱"]
    negative_words = ["아쉽", "실망", "별로", "최악", "비추", "노잼", "왜이래", "불편", "쓰레기", "오류", "답답"]

    pos_score = sum(1 for word in positive_words if word in text)
    neg_score = sum(1 for word in negative_words if word in text)

    if pos_score > neg_score:
        return "긍정"
    elif neg_score > pos_score:
        return "부정"
    else:
        return "중립"

def generate_korean_wordcloud(text_data: pd.Series, font_path: str):
    """한글 정규식을 적용하여 워드클라우드를 생성합니다."""
    combined_text = " ".join(text_data.dropna())
    # 한글 및 공백 문자 추출
    korean_words = re.findall(r"[가-힣]{2,}", combined_text)
    
    # 불용어(Stopwords) 정의
    stopwords = {"너무", "진짜", "그냥", "완전", "약간", "이번", "오늘", "보고", "영상"}
    filtered_words = [word for word in korean_words if word not in stopwords]
    
    clean_text = " ".join(filtered_words)
    
    if not clean_text.strip():
        return None

    wc = WordCloud(
        font_path=font_path,
        background_color="white",
        width=800,
        height=400,
        max_words=100
    ).generate(clean_text)
    
    return wc

# ---------------------------------------------------------
# 3. Streamlit UI 구성
# ---------------------------------------------------------
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")

st.title("📊 YouTube 댓글 분석기")
st.caption("YouTube Data API v3 기반 실시간 댓글 수집, 시간대별 추이, 반응도 및 한글 워드클라우드 시각화")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 앱 설정")
    api_key = st.text_input("YouTube API Key", type="password", help="Google Cloud Console에서 발급받은 API 키를 입력하세요.")
    max_comments = st.slider("수집할 댓글 수", min_value=10, max_value=1000, value=200, step=10)

# 메인 입력부
video_url = st.text_input("YouTube 영상 링크를 입력하세요:", placeholder="https://www.youtube.com/watch?v=...")

if video_url:
    video_id = extract_video_id(video_url)
    
    if not video_id:
        st.error("올바른 YouTube URL 형식이 아닙니다.")
    else:
        # 영상 임베드 출력
        st.video(f"https://www.youtube.com/watch?v={video_id}")
        
        if st.button("댓글 분석 시작"):
            if not api_key:
                st.warning("사이드바에 YouTube API Key를 입력해주세요.")
            else:
                with st.spinner("댓글 데이터를 수집 및 분석 중입니다..."):
                    try:
                        df = fetch_youtube_comments(api_key, video_id, max_comments)
                        
                        if df.empty:
                            st.warning("수집된 댓글이 없거나, 댓글이 비활성화된 영상입니다.")
                        else:
                            st.success(f"총 {len(df)}개의 댓글 수집 완료!")
                            
                            # 1. 시간대별 댓글 작성 추이
                            st.subheader("📈 시간대별 댓글 작성 추이")
                            df_time = df.set_index("published_at").resample("D").size().reset_index(name="count")
                            fig_line = px.line(
                                df_time, 
                                x="published_at", 
                                y="count", 
                                labels={"published_at": "날짜", "count": "댓글 수"},
                                title="일별 댓글 작성량 변동"
                            )
                            st.plotly_chart(fig_line, use_container_width=True)
                            
                            # 2. 댓글 반응도 (감성 및 좋아요 분석)
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("🎭 댓글 감성 반응도")
                                df["sentiment"] = df["comment"].apply(analyze_sentiment_simple)
                                sentiment_counts = df["sentiment"].value_counts().reset_index()
                                sentiment_counts.columns = ["Sentiment", "Count"]
                                
                                fig_pie = px.pie(
                                    sentiment_counts, 
                                    names="Sentiment", 
                                    values="Count", 
                                    color="Sentiment",
                                    color_discrete_map={"긍정": "#2ecc71", "중립": "#95a5a6", "부정": "#e74c3c"}
                                )
                                st.plotly_chart(fig_pie, use_container_width=True)

                            with col2:
                                st.subheader("👍 가장 많은 공감을 받은 댓글 Top 5")
                                top_liked = df.sort_values(by="like_count", ascending=False).head(5)
                                for idx, row in top_liked.iterrows():
                                    st.markdown(f"**{row['author']}** (좋아요 {row['like_count']}개)")
                                    st.caption(f"{row['comment']}")
                                    st.divider()

                            # 3. 한글 워드클라우드
                            st.subheader("☁️ 댓글 한글 워드클라우드")
                            wc = generate_korean_wordcloud(df["comment"], font_p)
                            
                            if wc:
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.imshow(wc, interpolation="bilinear")
                                ax.axis("off")
                                st.pyplot(fig)
                            else:
                                st.info("워드클라우드를 생성할 의미 있는 한글 단어가 부족합니다.")
                                
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
