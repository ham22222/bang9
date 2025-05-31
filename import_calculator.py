import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from bs4 import BeautifulSoup

# ✅ 페이지 설정 (모바일 최적화 포함)
st.set_page_config(
    page_title="수입 원가 계산기",
    page_icon="📦",
    layout="centered"
)

# ✅ 모바일 대응 스타일
st.markdown("""
<style>
    body, div, input, label {
        font-size: 16px !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ✅ 비밀번호 입력
correct_password = "1004"
password = st.text_input("비밀번호를 입력하세요", type="password")
if password != correct_password:
    st.warning("올바른 비밀번호를 입력해야 앱을 사용할 수 있습니다.")
    st.stop()

st.info("※ 표 오른쪽 상단 메뉴는 영어로 표시될 수 있습니다. 우클릭 시 CSV 다운로드 등 사용 가능")

# ✅ 환율 크롤링 함수 (네이버 금융 기준)
def get_exchange_rates_from_naver():
    url = "https://finance.naver.com/marketindex/exchangeList.naver"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")
    code_map = {
        "미국 USD": "USD",
        "유럽연합 EUR": "EUR",
        "일본 JPY(100엔)": "JPY",
        "중국 CNY": "CNY",
        "홍콩 HKD": "HKD"
    }
    rates = {}
    rows = soup.select("table.tbl_exchange tbody tr")
    for row in rows:
        title = row.select_one("td.tit span").get_text(strip=True)
        value = row.select("td")[1].get_text(strip=True).replace(",", "")
        if title in code_map:
            rate = float(value)
            if title == "일본 JPY(100엔)":
                rate = round(rate / 100, 4)
            rates[code_map[title]] = rate
    return rates

if "exchange_rates" not in st.session_state or st.session_state.get("refresh", False):
    st.session_state.exchange_rates = get_exchange_rates_from_naver()
    st.session_state.refresh = False

if st.button("🔄 환율 새로고침"):
    st.session_state.refresh = True
    st.experimental_rerun()

rates = st.session_state.exchange_rates
st.markdown("### 💱 네이버 기준 실시간 환율: " + " | ".join([f"1 {cur} = {val} KRW" for cur, val in rates.items()]))

st.markdown("---")
st.header("📦 제품 수입 원가 계산기 (옵션별 상세 입력 가능)")

examples = pd.DataFrame([...])  # 생략된 샘플 데이터는 유지

input_df = st.data_editor(
    examples,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "EXW 통화": st.column_config.Column(width="small", help="브랜드 제공 단가 통화 기준"),
        "EXW": st.column_config.Column(width="small", help="브랜드 제공 단가 (EXW 조건)"),
        "판매가(KRW)": st.column_config.Column(width="small", help="소비자 대상 예상 판매가"),
        "옵션": st.column_config.Column(width="medium"),
    },
    key="input"
)

if st.button("📊 계산하기"):
    results = []
    for _, row in input_df.iterrows():
        ...  # 생략된 계산 로직은 기존 그대로 유지

    result_df = pd.DataFrame(results)
    st.subheader("📋 계산 결과")
    st.markdown("<style>thead th { font-weight: bold !important; } tbody td { font-weight: 600; }</style>", unsafe_allow_html=True)
    st.dataframe(result_df, use_container_width=True)

    if not result_df.empty:
        st.subheader("📈 옵션별 마진율 비교")
        try:
            result_df["마진율(%)"] = result_df["마진율"].str.replace('%', '').astype(float)
            fig = px.bar(result_df, x="옵션", y="마진율(%)", color="옵션", title="옵션별 마진율")
            fig.update_layout(width=360, height=300)
            st.plotly_chart(fig, use_container_width=False)
        except Exception as e:
            st.error(f"마진율 차트 생성 오류: {e}")

        st.subheader("📊 원가 구성 비교")
        try:
            fig2 = px.bar(result_df, x="옵션", y=["광고비", "수수료", "판관비", "운송비", "배송비"], title="옵션별 원가 구성", barmode="stack")
            fig2.update_layout(width=360, height=300)
            st.plotly_chart(fig2, use_container_width=False)
        except Exception as e:
            st.error(f"원가 구성 차트 생성 오류: {e}")

    csv = result_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 결과 다운로드 (CSV)", data=csv, file_name='import_cost_result.csv', mime='text/csv')

    st.markdown("---")
    st.subheader("💬 ChatGPT 홈페이지로 이동")
    st.markdown("[ChatGPT 바로가기](https://chat.openai.com) 🔗")
