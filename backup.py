import os
import json
import requests
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Upstage 클라이언트 설정
client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1/solar"
)

# --- 로컬 JSON 데이터 로드 ---
def load_stock_dict():
    """로컬 krx.json 파일을 읽어서 종목명-코드 매핑을 반환합니다."""
    try:
        with open("krx.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("krx.json 파일을 찾을 수 없습니다.")
        return {}

def get_naver_news(url):
    """네이버 증권 종목 뉴스(iframe 대응) 및 일반 뉴스 크롤러"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 중요: 종목 상세 뉴스 페이지인 경우, 실제 데이터가 있는 iframe 주소로 변경
    if "item/news.naver" in url:
        url = url.replace("item/news.naver", "item/news_news.naver")
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'euc-kr' # 네이버 금융은 EUC-KR
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_data = []
        
        # 종목 뉴스 전용 셀렉터: <td class="title"> 내의 <a> 태그
        # 일반 뉴스 페이지의 경우 .articleSubject a 등을 사용
        items = soup.select('td.title a, .articleSubject a, .title a')
        
        seen_titles = set()
        for item in items:
            title_text = item.get_text(strip=True)
            
            # 뉴스 제목이 아닌 것들(예: '속보' 등 짧은 텍스트) 필터링
            if len(title_text) < 5 or title_text in seen_titles:
                continue
                
            link = item['href']
            # 상대 경로를 절대 경로로 보정
            if link.startswith('/'):
                # 종목 뉴스 iframe 내 링크는 보통 /item/mainnews.naver... 형태임
                link = "https://finance.naver.com" + link
            elif not link.startswith('http'):
                link = "https://finance.naver.com/item/" + link
                
            news_data.append({
                "title": title_text,
                "link": link
            })
            seen_titles.add(title_text)
            
            if len(news_data) >= 7: # 7개까지만 가져오기
                break
                
        return news_data
    except Exception as e:
        print(f"Error: {e}")
        return []

def analyze_news(title):
    """Solar Pro 분석 (JSON 모드)"""
    try:
        response = client.chat.completions.create(
            model="solar-pro",
            messages=[
                {"role": "system", "content": "당신은 주식 분석 전문가입니다. 반드시 JSON으로만 응답하세요."},
                {"role": "user", "content": f"다음 뉴스 제목의 투자 심리를 분석해줘: {title}\n\n결과는 sentiment(긍정/부정/중립), sentiment_score(-1~1), summary(한 줄 요약) 포함."}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return None

# --- UI 구성 ---
st.set_page_config(page_title="Solar Stock News", layout="wide")
st.title("📈 Solar Pro 주식 뉴스 센터")

# 1. 사이드바: 종목 검색
st.sidebar.header("🔍 종목 뉴스 검색")
stock_dict = load_stock_dict()

# 종목명을 선택하거나 입력할 수 있게 함
search_name = st.sidebar.selectbox("종목을 선택하세요", list(stock_dict.keys()))

if st.sidebar.button("분석 실행"):
    code = stock_dict[search_name]
    stock_url = f"https://finance.naver.com/item/news.naver?code={code}"
    
    st.subheader(f"🏢 {search_name} ({code}) 최신 뉴스 분석")
    with st.spinner("뉴스를 분석 중입니다..."):
        specific_news = get_naver_news(stock_url)
        if not specific_news:
            st.warning("분석할 뉴스를 찾지 못했습니다.")
        
        for news in specific_news:
            res = analyze_news(news['title'])
            if res:
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.metric(res['sentiment'], f"{res['sentiment_score']}")
                with col2:
                    st.markdown(f"**[{news['title']}]({news['link']})**")
                    st.caption(res['summary'])
                st.divider()

# 2. 메인: 전체 시황 뉴스
st.header("🌍 실시간 시장 주요 뉴스")
if st.button("전체 시황 업데이트"):
    main_url = "https://finance.naver.com/news/mainnews.naver"
    with st.spinner("전체 시장 흐름 파악 중..."):
        market_news = get_naver_news(main_url)
        for news in market_news:
            res = analyze_news(news['title'])
            if res:
                with st.expander(f"{news['title']}"):
                    st.write(f"**AI 분석:** {res['sentiment']} (점수: {res['sentiment_score']})")
                    st.info(res['summary'])
                    st.markdown(f"[기사 본문 열기]({news['link']})")