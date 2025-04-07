FROM python:3.13.0-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt requirements.txt
COPY . .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 환경 변수 설정
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# 포트 설정
EXPOSE 8080

# Flask 실행 (Gunicorn 사용)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]
