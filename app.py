from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import openai
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

@app.websocket("/chatbot")
async def chatbot_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # 챗봇 시작 메시지 전송
    await websocket.send_text("안녕하세요! 학습 방법을 추천해드릴 AI 챗봇입니다.")
    await websocket.send_text("일일 학습 시간은 얼마나 되나요? (예: 2시간)")

    try:
        while True:
            user_input = await websocket.receive_text()
            response = f"입력하신 값: {user_input} (추천을 생성하는 로직을 여기에 추가하세요)"
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("클라이언트 연결 종료됨")


@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 작동 중입니다!"}

# CORS 설정 (브라우저 요청 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# API 호출 제한
openai_api_calls = 0
max_openai_calls = 3  # OpenAI 하루 최대 호출 수

# OpenAI 호출 함수
def generate_recommendation(daily_study_time, weaknesses, preferred_media, subject):
    global openai_api_calls
    if openai_api_calls >= max_openai_calls:
        raise HTTPException(status_code=429, detail="OpenAI API 호출 한도를 초과했습니다.")

    openai_api_calls += 1
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"일일 학습 시간은 {daily_study_time}, 취약한 부분은 {weaknesses}, 선호하는 학습 매체는 {preferred_media}, 학습할 과목은 {subject}인 사람에게 추천할 수 있는 학습 방법을 논문과 공식 문서를 바탕으로 제시하세요."}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.5,
            top_p=1,
            request_timeout=5  # 최대 5초 대기 후 응답 없으면 오류 반환
        )
    except openai.error.Timeout as e:
        raise HTTPException(status_code=504, detail="OpenAI API 응답이 너무 느립니다.")

    return response['choices'][0]['message']['content'].strip()

# Google Custom Search 최적화 함수
def search_learning_resources(query: str):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "siteSearch": "scholar.google.com|khanacademy.org|coursera.org|edx.org|ted.com",
        "num": 5
    }

    response = requests.get(search_url, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Google 검색 API 호출 실패")

    results = response.json()
    resources = []
    
    if 'items' in results:
        for item in results['items']:
            resources.append({
                'title': item.get('title', 'No title available'),
                'link': item.get('link', 'No link available'),
                'snippet': item.get('snippet', 'No description available')
            })
    
    return resources

# 학습 방법 추천 API 엔드포인트
@app.post("/recommendation/")
def get_recommendation(daily_study_time: str, weaknesses: str, preferred_media: str, subject: str):
    recommendation = generate_recommendation(daily_study_time, weaknesses, preferred_media, subject)
    return {"recommendation": recommendation}

# 학습 자료 검색 API 엔드포인트
@app.get("/search/")
def get_learning_resources(query: str):
    resources = search_learning_resources(query)
    return {"resources": resources}

