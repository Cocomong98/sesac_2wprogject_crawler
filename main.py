import os
import json
import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NEWS_DIR = "news"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

session = requests.Session()
session.headers.update(HEADERS)

client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1/solar"
)

def extract_article_id(url):
    """URL에서 oid와 aid를 추출하여 고유 ID 생성 (예: 421_0008765615)"""
    oid_match = re.search(r"office_id=(\d+)", url) or re.search(r"article/(\d+)/", url)
    aid_match = re.search(r"article_id=(\d+)", url) or re.search(r"article/\d+/(\d+)", url)
    
    if oid_match and aid_match:
        return f"{oid_match.group(1)}_{aid_match.group(1)}"
    return None

def summarize_content(raw_content):
    if not raw_content or len(raw_content) < 50: return raw_content
    clean_text = " ".join(raw_content.split())[:2000]
    try:
        response = client.chat.completions.create(
            model="solar-pro",
            messages=[
                {"role": "system", "content": "주식 뉴스 요약 전문가. 오직 [논조], [종목], [내용]만 포함된 결과만 줄바꿈 없이 답변."},
                {"role": "user", "content": f"요약해: {clean_text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except: return "요약 실패"

def get_article_data(url):
    """기사 본문 및 고유 식별값 추출"""
    article_id = extract_article_id(url)
    if not article_id: return None

    # 표준화된 모바일 뉴스 주소로 접속 (추출 성공률 높음)
    oid, aid = article_id.split('_')
    standard_url = f"https://n.news.naver.com/mnews/article/{oid}/{aid}"

    try:
        res = session.get(standard_url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        title_tag = soup.select_one('#title_area, .media_end_head_headline')
        date_tag = soup.select_one('._ARTICLE_DATE_TIME, .media_end_head_info_datestamp_time')
        content_tag = soup.select_one('#dic_area, #articleBodyContents')

        if title_tag and content_tag:
            for s in content_tag.select('script, style, .end_photo_org, .nbd_im_w'): s.decompose()
            return {
                "id": article_id,  # 중복 체크용 고유 ID 저장
                "title": title_tag.get_text(strip=True),
                "date": date_tag.get_text(strip=True) if date_tag else "날짜없음",
                "content": summarize_content(content_tag.get_text(" ", strip=True))
            }
    except: pass
    return None

# def run_crawler():
#     if not os.path.exists(NEWS_DIR): os.makedirs(NEWS_DIR)
    
#     print("\n--- 🤖 ID 기반 증분 수집 크롤러 ---")
#     code = input("종목 코드 6자리: ").strip()
#     if not (len(code) == 6 and code.isdigit()): return

#     today_str = datetime.now().strftime('%Y%m%d')
#     file_path = os.path.join(NEWS_DIR, f"{code}_{today_str}.json")
    
#     existing_data = []
#     existing_ids = set() # 이제 제목 대신 ID로 중복 체크

# 크롤러가 일단 삼성전자만 크롤링하도록
def run_crawler():
    if not os.path.exists(NEWS_DIR): os.makedirs(NEWS_DIR)
    
    print("\n--- 🤖 ID 기반 증분 수집 크롤러 (자동 모드) ---")
    
    # 사용자 입력 대신 삼성전자 코드로 고정
    code = "005930" 
    print(f"📈 대상 종목: 삼성전자({code})")

    today_str = datetime.now().strftime('%Y%m%d')
    file_path = os.path.join(NEWS_DIR, f"{code}_{today_str}.json")
    
    existing_data = []
    existing_ids = set() # 이제 제목 대신 ID로 중복 체크

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                # 기존 데이터에서 ID만 뽑아와서 Set 구성
                existing_ids = {item.get('id') for item in existing_data if item.get('id')}
                print(f"📂 오늘 이미 {len(existing_ids)}건의 기사가 수집되었습니다.")
            except: pass

    # 목록 가져오기
    list_url = f"https://finance.naver.com/item/news_news.naver?code={code}"
    session.headers.update({"Referer": f"https://finance.naver.com/item/main.naver?code={code}"})
    
    try:
        response = session.get(list_url, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', class_='tit')
        
        new_items = []
        print(f"🔍 새 기사 확인 중...")

        for link_tag in reversed(links):
            article_href = link_tag.get('href', '')
            # 링크에서 먼저 ID 추출
            current_id = extract_article_id(article_href)
            
            # ID가 이미 존재하면 요약 과정 없이 바로 패스
            if current_id in existing_ids:
                continue

            if article_href.startswith('/'):
                article_href = "https://finance.naver.com" + article_href
            
            data = get_article_data(article_href)
            if data:
                print(f"   ✨ [NEW] {data['title'][:25]}...")
                new_items.append(data)
                existing_ids.add(data['id'])
                time.sleep(0.4)

        if new_items:
            final_data = existing_data + new_items
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"\n🎉 업데이트 완료! ({len(new_items)}건 추가됨)")
        else:
            print("\n✨ 새로운 기사가 없습니다.")

    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    run_crawler()