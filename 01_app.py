import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

st.set_page_config(page_title="입대 추천 계산기", page_icon="🪖")

st.title("🪖 입대 시기 추천 계산기")
st.write("예상 유격·혹한기 훈련 횟수를 바탕으로 가장 유리한 입대 시기를 추천합니다.")

birth = st.date_input(
    "생년월일을 입력하세요",
    value=date(2008, 1, 1),
    min_value=date(1990,1,1),
    max_value=date.today()
)

today = date.today()

age = today.year - birth.year
if (today.month, today.day) < (birth.month, birth.day):
    age -= 1

st.markdown(f"### 현재 나이 : **만 {age}세**")

# -----------------------------
# 함수
# -----------------------------

def count_trainings(enlist_date):

    basic_end = enlist_date + timedelta(weeks=5)
    discharge = enlist_date + relativedelta(months=18)

    cold = 0
    guerrilla = 0

    current = date(basic_end.year, basic_end.month, 1)

    while current <= discharge:

        # 혹한기
        if current.month in [1,2]:
            cold += 1

        # 유격
        if current.month in [5,6]:
            guerrilla += 1

        current += relativedelta(months=1)

    score = cold + guerrilla

    return cold, guerrilla, score, discharge


# -----------------------------
# 후보 생성
# -----------------------------

results = []

start = date(today.year + 1, 1, 1)

for i in range(36):

    enlist = start + relativedelta(months=i)

    cold, guerrilla, score, discharge = count_trainings(enlist)

    results.append({
        "입대일": enlist.strftime("%Y-%m"),
        "혹한기": cold,
        "유격": guerrilla,
        "총 훈련": score,
        "전역": discharge.strftime("%Y-%m")
    })

df = pd.DataFrame(results)
df = df.sort_values(
    ["총 훈련","혹한기","유격","입대일"]
).reset_index(drop=True)

# -----------------------------
# 추천 TOP5
# -----------------------------

st.header("🏆 추천 입대 시기 TOP 5")

for i in range(5):

    row = df.iloc[i]

    st.success(
f"""
### {i+1}위 : {row['입대일']}

✅ 예상 혹한기 : {row['혹한기']}회

✅ 예상 유격 : {row['유격']}회

⭐ 총 주요 훈련 : {row['총 훈련']}회

🎖️ 예상 전역 : {row['전역']}
"""
    )

st.header("전체 결과")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# 색상 표시
# -----------------------------

st.header("추천도")

def color(score):
    if score <= 2:
        return "🟢 매우 추천"
    elif score == 3:
        return "🟡 추천"
    elif score == 4:
        return "🟠 보통"
    else:
        return "🔴 비추천"

table = df.copy()
table["추천도"] = table["총 훈련"].apply(color)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)

st.caption("※ 실제 훈련 횟수는 부대, 군단, 사단, 연도별 훈련 계획에 따라 달라질 수 있으며 본 결과는 추정치입니다.")
