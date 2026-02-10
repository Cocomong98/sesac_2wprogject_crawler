import time
import subprocess
from datetime import datetime, timezone

# --- 설정 구간 ---
TARGET_HOUR_UTC = 9  # 실행하고 싶은 UTC 시간 (예: 09:00)
TARGET_MINUTE_UTC = 0
# ----------------

print(f"UTC 스케줄러 시작 (설정 시간: {TARGET_HOUR_UTC:02d}:{TARGET_MINUTE_UTC:02d} UTC)")

while True:
    now_utc = datetime.now(timezone.utc)
    
    # 설정한 시(Hour)와 분(Minute)이 일치하고, 초가 0초일 때 실행
    if now_utc.hour == TARGET_HOUR_UTC and now_utc.minute == TARGET_MINUTE_UTC:
        print(f"[{now_utc}] 작업 시작!")
        
        # uv를 이용해 같은 폴더의 main.py 실행
        # shell=True를 쓰면 시스템 경로의 uv를 바로 잡습니다.
        subprocess.run(["uv", "run", "main.py"], shell=True)
        
        # 한 번 실행 후 61초 동안 대기 (중복 실행 방지)
        time.sleep(61)
    
    # 10초마다 현재 시간 체크 (CPU 사용률을 낮춤)
    time.sleep(10)