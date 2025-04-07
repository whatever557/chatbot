import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# API 호출 제한
openai_api_calls = 0
max_openai_calls = 3  # OpenAI 하루 최대 호출 수

# 📌 학습에 도움이 될만한 웹사이트 리스트
learning_sites = [
    {"title": "K-MOOC (한국 온라인 강의)", "link": "http://www.kmooc.kr/"},
    {"title": "edX", "link": "https://www.edx.org/"},
    {"title": "Coursera", "link": "https://www.coursera.org/"},
    {"title": "Khan Academy", "link": "https://www.khanacademy.org/"},
    {"title": "TED-Ed", "link": "https://ed.ted.com/"},
]

# 📌 Google Scholar 논문 검색
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
            paper_links.append(f"- [{title}]({link})")
    
    return papers, "\n".join(paper_links)

# 📌 학습 방법 추천 (논문 기반 또는 웹사이트 기반)
def generate_study_recommendation(daily_study_time, weaknesses, preferred_media, subject):
    global openai_api_calls
    if openai_api_calls >= max_openai_calls:
        print("⚠️ OpenAI API 호출 한도를 초과했습니다. 나중에 다시 시도해주세요.")
        return None, None
    
    # 🔍 Google Scholar에서 관련 논문 검색
    query = f"{subject} 공부 방법 {weaknesses} {preferred_media} site:scholar.google.com"
    scholar_results, paper_links = search_google_scholar(query)
    
    if not scholar_results:
        # 논문이 없을 경우, 학습에 도움이 될 만한 사이트 추천
        scholar_text = "📌 관련 논문을 찾을 수 없습니다.\n대신 다음 사이트를 참고하세요:\n"
        site_links = "\n".join([f"- [{site['title']}]({site['link']})" for site in learning_sites])
    else:
        scholar_text = "\n\n".join(scholar_results)
        site_links = paper_links
    
    # 📌 OpenAI API 호출
    openai_api_calls += 1
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
        return response.choices[0].message.content.strip(), site_links
    except Exception as e:
        print(f"⚠️ OpenAI API 요청 중 오류 발생: {e}")
        return None, site_links

# 📌 과제 제작 툴 추천
def generate_assignment_tool_recommendation(subject):
    tools = {
        "1": {"수학": "GeoGebra, Desmos, Wolfram Alpha, Mathway (한국어 지원)"},
        "2": {"영어": "Grammarly, Hemingway Editor, QuillBot, Papago 번역"},
        "3": {"과학": "PhET Simulations, Labster, Wolfram Alpha, K-MOOC (한국 온라인 강의)"},
        "4": {"프로그래밍": "Replit, Jupyter Notebook, Visual Studio Code, 코드잇 (한국어)"},
        "5": {"디자인": "Canva, Adobe Creative Cloud, Figma, 미리캔버스 (한국어)"},
    }
    return tools.get(subject, {"기본 추천": "Google Docs, Notion, Trello, 네이버 메모"})

# 사용자 입력 함수
def get_user_choice():
    print("\n📌 원하는 추천 서비스를 선택하세요.")
    print("1. 📖 학습 방법 추천 (논문 기반)")
    print("2. 🛠️ 과제 해결 툴 추천")
    print("3. ❌ 추천 서비스 종료")
    choice = input("번호를 입력하세요 (1, 2, 3): ")
    return choice

# 메인 실행 함수
def main():
    while True:
        choice = get_user_choice()
        
        if choice == "1":
            daily_study_time = input("📚 일일 학습 시간은 얼마나 되나요? (예: 2시간) ")
            weaknesses = input("🤔 학습 중 가장 어려운 부분은 무엇인가요? (예: 집중력, 암기력) ")
            preferred_media = input("🎥 선호하는 학습 매체는 무엇인가요? (예: 동영상, 책, 온라인 강의) ")
            subject = input("📖 학습할 과목은 무엇인가요? (예: 수학, 영어) ")
            
            recommendation, references = generate_study_recommendation(daily_study_time, weaknesses, preferred_media, subject)
            if recommendation:
                print(f"\n📖 추천된 학습 방법:\n{recommendation}")
                print("\n🔗 참고할 자료:\n" + references)
            else:
                print("추천이 생성되지 않았습니다.")
        
        elif choice == "2":
            print("🛠️ 과제 제작 도구 추천을 받을 과목을 선택하세요:")
            print("1. 수학")
            print("2. 영어")
            print("3. 과학")
            print("4. 프로그래밍")
            print("5. 디자인")
            subject = input("번호를 입력하세요 (1-5): ")
            tools = generate_assignment_tool_recommendation(subject)
            print("\n🛠️ 추천된 과제 제작 도구:")
            for category, tool_list in tools.items():
                print(f"- {category}: {tool_list}")
        
        elif choice == "3":
            print("🎉 추천 서비스를 종료합니다. 이용해 주셔서 감사합니다!")
            break
        
        else:
            print("⚠️ 올바른 번호를 입력해주세요.")

if __name__ == "__main__":
    main()
