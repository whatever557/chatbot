import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 허용

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# API 호출 제한
openai_api_calls = 0
max_openai_calls = 3  # OpenAI 하루 최대 호출 수

# 학습 방법 추천 함수
def generate_study_recommendation(daily_study_time, weaknesses, preferred_media, subject):
    global openai_api_calls
    if openai_api_calls >= max_openai_calls:
        return {"error": "OpenAI API 호출 한도를 초과했습니다. 나중에 다시 시도해주세요."}
    
    openai_api_calls += 1
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"일일 학습 시간은 {daily_study_time}, 취약한 부분은 {weaknesses}, 선호하는 학습 매체는 {preferred_media}, 학습할 과목은 {subject}인 사람에게 추천할 수 있는 학습 방법을 논문과 공식 문서를 바탕으로 제시하세요."}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1000,
        temperature=0.5,
        top_p=1,
    )
    
    return {"recommendation": response.choices[0].message.content.strip()}

# 과제 제작 툴 추천 함수
def generate_assignment_tool_recommendation(subject):
    tools = {
        "1": {"수학": "GeoGebra, Desmos, Wolfram Alpha, Mathway (한국어 지원)"},
        "2": {"영어": "Grammarly, Hemingway Editor, QuillBot, Papago 번역"},
        "3": {"과학": "PhET Simulations, Labster, Wolfram Alpha, K-MOOC (한국 온라인 강의)"},
        "4": {"프로그래밍": "Replit, Jupyter Notebook, Visual Studio Code, 코드잇 (한국어)"},
        "5": {"디자인": "Canva, Adobe Creative Cloud, Figma, 미리캔버스 (한국어)"},
    }
    return tools.get(subject, {"기본 추천": "Google Docs, Notion, Trello, 네이버 메모"})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API Server is running!"})


@app.route("/recommend/study", methods=["POST"])
def recommend_study():
    data = request.json
    daily_study_time = data.get("daily_study_time", "")
    weaknesses = data.get("weaknesses", "")
    preferred_media = data.get("preferred_media", "")
    subject = data.get("subject", "")
    
    result = generate_study_recommendation(daily_study_time, weaknesses, preferred_media, subject)
    return jsonify(result)

@app.route("/recommend/tool", methods=["POST"])
def recommend_tool():
    data = request.json
    subject = data.get("subject", "")
    
    result = generate_assignment_tool_recommendation(subject)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
