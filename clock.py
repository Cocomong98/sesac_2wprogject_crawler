import schedule
import time
import subprocess
from datetime import datetime, timezone

def job():
    # 현재 시간을 UTC 기준으로 출력 (기록용)
    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_utc} UTC] 작업 시작 (15분 간격 실행 중...)")
    
    try:
        # main.py 실행
        subprocess.run(["uv", "run", "main.py"], shell=True, check=True)
        print("--- 작업 완료 ---")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

# 1. 프로그램을 켜자마자 '즉시' 첫 번째 작업을 시작합니다.
job()

# 2. 그 시점부터 '15분 간격'으로 예약합니다. 
# (예: 1시 10분에 켰다면 1시 25분, 1시 40분... 순서로 실행)
schedule.every(15).minutes.do(job)

print("스케줄러가 활성화되었습니다. 15분마다 main.py를 실행합니다.")
print("종료하려면 이 창에서 Ctrl+C를 누르세요.")

while True:
    schedule.run_pending()
    time.sleep(1)