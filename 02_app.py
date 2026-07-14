import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(
    page_title="Global Top 10 Stocks Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Global Market Cap Top10 Dashboard")
st.markdown("최근 1년간 글로벌 시가총액 Top10 기업의 주가를 확인할 수 있습니다.")

# 기업 목록
companies = {
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Apple": "AAPL",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Berkshire Hathaway": "BRK-B"
}

selected = st.multiselect(
    "기업 선택",
    list(companies.keys()),
    default=["Microsoft"]
)

if len(selected) == 0:
    st.warning("최소 한 개 이상의 기업을 선택하세요.")
    st.stop()

compare = st.checkbox("한 그래프에서 비교하기", value=False)

# -----------------------------
# 비교 그래프
# -----------------------------
if compare:

    fig = go.Figure()

    for company in selected:

        ticker = companies[company]

        data = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )

        if len(data) == 0:
            continue

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name=company
            )
        )

    fig.update_layout(
        title="최근 1년 주가 비교",
        template="plotly_white",
        height=650,
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Price"
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 개별 차트
# -----------------------------
else:

    for company in selected:

        ticker = companies[company]

        data = yf.download(
            ticker,
            period="1y",
            progress=False,
            auto_adjust=True
        )

        if len(data) == 0:
            continue

        data["MA20"] = data["Close"].rolling(20).mean()
        data["MA60"] = data["Close"].rolling(60).mean()

        latest = data.iloc[-1]

        st.subheader(company)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "현재가",
            f"${latest['Close']:.2f}"
        )

        col2.metric(
            "1년 최고가",
            f"${data['High'].max():.2f}"
        )

        col3.metric(
            "1년 최저가",
            f"${data['Low'].min():.2f}"
        )

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7,0.3]
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                name="Close",
                line=dict(width=2)
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["MA20"],
                name="MA20"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["MA60"],
                name="MA60"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["Volume"],
                name="Volume"
            ),
            row=2,
            col=1
        )

        fig.update_layout(
            height=700,
            template="plotly_white",
            hovermode="x unified"
        )

        fig.update_yaxes(title="Price", row=1, col=1)
        fig.update_yaxes(title="Volume", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)
