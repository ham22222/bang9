import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from bs4 import BeautifulSoup

# ✅ 페이지 설정 (PC 화면 꽉 차게)
st.set_page_config(
    page_title="수입 원가 계산기",
    page_icon="📦",
    layout="wide"
)

# ✅ 스타일 조정 (모바일 + PC 대응)
st.markdown("""
<style>
    body, div, input, label {
        font-size: 16px !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
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
        title_elem = row.select_one("td.tit span")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
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
    st.rerun()

rates = st.session_state.exchange_rates
st.markdown("### 💱 네이버 기준 실시간 환율: " + " | ".join([f"1 {cur} = {val} KRW" for cur, val in rates.items()]))

st.markdown("---")
st.header("📦 제품 수입 원가 계산기 (옵션별 상세 입력 가능)")

examples = pd.DataFrame([
    {"브랜드": "브랜드A", "상품명": "가방", "옵션": "블랙", "EXW 통화": "USD", "EXW": 50.0, "판매가(KRW)": 120000,
     "수량": 1, "조건": "EXW", "제조국": "중국", "출발국": "중국", "비고": "옵션1",
     "원화단가": 0, "제품원가율(%)": 0, "운송비": 10000, "배송비": 5000,
     "광고비": 8000, "수수료": 5000, "판관비": 7000, "목표수량": 100},

    {"브랜드": "브랜드B", "상품명": "지갑", "옵션": "브라운", "EXW 통화": "EUR", "EXW": 30.0, "판매가(KRW)": 85000,
     "수량": 1, "조건": "EXW", "제조국": "이탈리아", "출발국": "이탈리아", "비고": "옵션2",
     "원화단가": 0, "제품원가율(%)": 0, "운송비": 8000, "배송비": 4000,
     "광고비": 6000, "수수료": 4000, "판관비": 6000, "목표수량": 80}
])

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
        exw = row["EXW"]
        currency = row["EXW 통화"]
        terms = row["조건"]
        qty = row["수량"]
        price = row["판매가(KRW)"]
        ads = row["광고비"]
        fee = row["수수료"]
        sgna = row["판관비"]
        shipping = row["운송비"]
        delivery = row["배송비"]
        rate = rates.get(currency, 1350)

        inland = 100 if terms == "EXW" else 0
        freight = 300
        insurance = round((exw + inland + freight) * 0.003, 2)
        cif_value = exw + inland + freight + insurance
        fob_value = exw + inland
        cif_krw = cif_value * rate
        duty = cif_krw * 0.08
        vat = (cif_krw + duty) * 0.1
        total_cost_sum = cif_krw + duty + vat + ads + fee + sgna + shipping + delivery
        total_cost_unit = total_cost_sum / qty if qty else 0
        margin = price - total_cost_unit
        margin_rate = margin / price if price else 0
        product_cost_rate = (total_cost_unit / price * 100) if price else 0
        target_qty = row["목표수량"]
        target_sales = target_qty * price if target_qty else 0
        est_ads = target_sales * 0.1
        est_profit = target_sales - (total_cost_sum * target_qty / qty) if qty else 0
        est_profit_rate = (est_profit / target_sales * 100) if target_sales else 0

        results.append({
            "상품명": row["상품명"],
            "옵션": row["옵션"],
            "CIF (₩)": round(cif_krw),
            "FOB (₩)": round(fob_value * rate),
            "관세": round(duty),
            "부가세": round(vat),
            "운송비": round(shipping),
            "배송비": round(delivery),
            "광고비": round(ads),
            "수수료": round(fee),
            "판관비": round(sgna),
            "총 원가(₩)": round(total_cost_unit),
            "제품원가율(%)": f"{product_cost_rate:.1f}%",
            "마진(₩)": round(margin),
            "마진율": f"{margin_rate * 100:.1f}%",
            "목표수량": target_qty,
            "목표매출": round(target_sales),
            "예상광고비": round(est_ads),
            "예상영업이익": round(est_profit),
            "예상이익률": f"{est_profit_rate:.1f}%"
        })

    result_df = pd.DataFrame(results)
    st.subheader("📋 계산 결과")
    st.markdown("<style>thead th { font-weight: bold !important; } tbody td { font-weight: 600; }</style>", unsafe_allow_html=True)
    st.dataframe(result_df, use_container_width=True)

    if not result_df.empty:
        st.subheader("📈 옵션별 마진율 비교")
        try:
            result_df["마진율(%)"] = result_df["마진율"].str.replace('%', '').astype(float)
            fig = px.bar(result_df, x="옵션", y="마진율(%)", color="옵션", title="옵션별 마진율")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"마진율 차트 생성 오류: {e}")

        st.subheader("📊 원가 구성 비교")
        try:
            fig2 = px.bar(result_df, x="옵션", y=["광고비", "수수료", "판관비", "운송비", "배송비"], title="옵션별 원가 구성", barmode="stack")
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"원가 구성 차트 생성 오류: {e}")

    csv = result_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 결과 다운로드 (CSV)", data=csv, file_name='import_cost_result.csv', mime='text/csv')

    st.markdown("---")
    st.subheader("💬 ChatGPT 홈페이지로 이동")
    st.markdown("[ChatGPT 바로가기](https://chat.openai.com) 🔗")
