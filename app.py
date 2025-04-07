from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import os
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 📌 학습에 도움이 될만한 웹사이트 리스트
learning_sites = [
    {"title": "K-MOOC (한국 온라인 강의)", "link": "http://www.kmooc.kr/"},
    {"title": "edX", "link": "https://www.edx.org/"},
    {"title": "Coursera", "link": "https://www.coursera.org/"},
    {"title": "Khan Academy", "link": "https://www.khanacademy.org/"},
    {"title": "TED-Ed", "link": "https://ed.ted.com/"},
]

# 📌 Google Scholar 논문 검색 함수
def search_google_scholar(query):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "num": 3,  # 최대 3개 논문 가져오기
    }
    
    response = requests.get(search_url, params=params)
    results = response.json()

    papers = []
    paper_links = []
    
    if "items" in results:
        for item in results["items"]:
            title = item.get("title", "제목 없음")
            link = item.get("link", "#")
            snippet = item.get("snippet", "설명 없음")
            papers.append(f"📖 {title}\n🔗 {link}\n📝 {snippet}")
            paper_links.append({"title": title, "link": link})
    
    return papers, paper_links


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API Server is running!"})

# 📌 학습 방법 추천 API
@app.route("/study_recommendation", methods=["POST"])
def study_recommendation():
    data = request.json
    daily_study_time = data.get("daily_study_time")
    weaknesses = data.get("weaknesses")
    preferred_media = data.get("preferred_media")
    subject = data.get("subject")

    # 논문 검색
    query = f"{subject} 공부 방법 {weaknesses} {preferred_media} site:scholar.google.com"
    scholar_results, paper_links = search_google_scholar(query)

    if not scholar_results:
        scholar_text = "📌 관련 논문을 찾을 수 없습니다."
        references = learning_sites
    else:
        scholar_text = "\n\n".join(scholar_results)
        references = paper_links

    # OpenAI API 호출
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""
        사용자의 학습 정보:
        - 일일 학습 시간: {daily_study_time}
        - 취약한 부분: {weaknesses}
        - 선호하는 학습 매체: {preferred_media}
        - 학습할 과목: {subject}
        
        다음은 Google Scholar에서 찾은 관련 논문입니다:
        {scholar_text}
        
        위 정보를 바탕으로 효과적인 학습 방법을 추천해주세요.
        """}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.5,
            top_p=1,
        )
        recommendation = response.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": f"OpenAI API 요청 중 오류 발생: {e}"}), 500

    return jsonify({"recommendation": recommendation, "references": references})

# 📌 과제 해결 툴 추천 API
@app.route("/recommend/tools", methods=["GET"])
def recommend_tools():
    subject = request.args.get("subject", "기본")

    tools = {
        "수학": ["GeoGebra", "Desmos", "Wolfram Alpha", "Mathway (한국어 지원)"],
        "영어": ["Grammarly", "Hemingway Editor", "QuillBot", "Papago 번역"],
        "과학": ["PhET Simulations", "Labster", "Wolfram Alpha", "K-MOOC (한국 온라인 강의)"],
        "프로그래밍": ["Replit", "Jupyter Notebook", "Visual Studio Code", "코드잇 (한국어)"],
        "디자인": ["Canva", "Adobe Creative Cloud", "Figma", "미리캔버스 (한국어)"],
    }

    return jsonify({"recommended_tools": tools.get(subject, ["Google Docs", "Notion", "Trello", "네이버 메모"])})

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)
