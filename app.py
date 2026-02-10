import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 설정 ---
NEWS_DIR = "news"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def setup_directory():
    """뉴스 저장 폴더가 없으면 생성합니다."""
    if not os.path.exists(NEWS_DIR):
        os.makedirs(NEWS_DIR)

def get_article_detail(url):
    """기사 상세 페이지에서 본문과 날짜를 추출합니다."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 배포 일자 추출
        date_tag = soup.select_one('.media_end_head_info_dateline_time, .date, .t11')
        date_str = date_tag.get_text(strip=True) if date_tag else "날짜 정보 없음"

        # 2. 본문 내용 추출
        content_tag = soup.select_one('#dic_area, #articleBodyContents, #newsEndContents')
        if content_tag:
            # 기사 내 불필요한 요소 제거
            for s in content_tag.select('script, style, span.end_photo_org'):
                s.decompose()
            content = content_tag.get_text("\n", strip=True)
        else:
            content = "본문을 가져올 수 없습니다."

        return date_str, content
    except:
        return "날짜 정보 없음", "기사 읽기 실패"

def fetch_stock_news_by_code(code):
    """입력받은 종목 코드를 기준으로 뉴스를 수집하고 코드를 파일명으로 저장합니다."""
    print(f"\n🚀 종목 코드 [{code}] 뉴스 수집 시작...")
    
    # 실제 뉴스 리스트가 있는 iframe 주소
    list_url = f"https://finance.naver.com/item/news_news.naver?code={code}"
    
    try:
        response = requests.get(list_url, headers=HEADERS)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.select('td.title a')
        
        if not links:
            print(f"❌ 해당 종목({code})의 뉴스를 찾을 수 없습니다. 코드를 확인해주세요.")
            return

        collected_news = []
        for link in links[:5]:  # 최신 5개 기사 수집
            title = link.get_text(strip=True)
            href = link['href']
            
            # 절대 경로 보정
            if href.startswith('/'):
                article_url = "https://finance.naver.com" + href
            else:
                article_url = href

            # 상세 페이지 정보 수집
            date, content = get_article_detail(article_url)
            
            collected_news.append({
                "title": title,
                "date": date,
                "content": content
            })
            print(f"   ✅ 수집 완료: {title[:25]}...")

        # JSON 저장 (파일명은 무조건 종목코드_날짜_시간.json)
        file_name = f"{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(NEWS_DIR, file_name)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(collected_news, f, ensure_ascii=False, indent=4)
        
        print(f"\n📂 저장 완료: {file_path}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    setup_directory()
    
    print("--- 실시간 종목 뉴스 수집기 ---")
    target_code = input("수집할 종목 코드 6자리를 입력하세요 (예: 005930): ").strip()
    
    # 6자리 숫자인지 간단히 체크
    if len(target_code) != 6 or not target_code.isdigit():
        print("❌ 올바른 종목 코드가 아닙니다. 6자리 숫자를 입력해주세요.")
        return

    fetch_stock_news_by_code(target_code)

if __name__ == "__main__":
    main()