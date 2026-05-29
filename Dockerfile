FROM python:3.12-slim

# 시간대를 한국 시각으로 (RUN_HOUR 가 KST 기준으로 동작하도록)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 브리핑 HTML 저장 위치 (볼륨으로 마운트하면 컨테이너 재시작 후에도 보존됨)
ENV OUTPUT_DIR=/data
VOLUME /data

EXPOSE 8080

# server.py 는 웹 서버 + 내장 스케줄러를 함께 실행한다.
CMD ["python", "server.py"]
