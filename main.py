import openai
import requests
import os
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

# OpenAI 호출 함수
def generate_recommendation(daily_study_time, weaknesses, preferred_media, subject):
    global openai_api_calls
    if openai_api_calls >= max_openai_calls:
        print("OpenAI API 호출 한도를 초과했습니다. 나중에 다시 시도해주세요.")
        return None
    
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
    
    return response.choices[0].message.content.strip()

# Google Custom Search 최적화 함수
def search_learning_resources(query):
    search_url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "siteSearch": "scholar.google.com|khanacademy.org|coursera.org|edx.org|ted.com",
        "num": 5
    }

    response = requests.get(search_url, params=params)
    
    if response.status_code != 200:
        print(f"Google 검색 API 호출 실패: {response.status_code}")
        return []

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

# 사용자 입력 함수
def get_learning_habits():
    print("안녕하세요! 학습 방법을 추천해드릴 AI 챗봇입니다.")
    daily_study_time = input("일일 학습 시간은 얼마나 되나요? (예: 2시간) ")
    weaknesses = input("학습 중 어떤 부분이 가장 어렵나요? (예: 집중력, 암기력) ")
    preferred_media = input("선호하는 학습 매체는 무엇인가요? (예: 동영상, 책, 온라인 강의) ")
    subject = input("학습할 과목은 무엇인가요? (예: 수학, 영어) ")

    return daily_study_time, weaknesses, preferred_media, subject

# 메인 실행 함수
def main():
    daily_study_time, weaknesses, preferred_media, subject = get_learning_habits()
    
    recommendation = generate_recommendation(daily_study_time, weaknesses, preferred_media, subject)
    if recommendation:
        print(f"\n추천된 학습 방법: {recommendation}")
        
        search_query = f"{recommendation} 학습법 OR 강의 OR 공식 문서"
        resources = search_learning_resources(search_query)
        
        print("\n📚 관련 학습 자료:")
        for res in resources:
            print(f"- {res['title']}\n  링크: {res['link']}\n  설명: {res['snippet']}\n")

    else:
        print("추천이 생성되지 않았습니다.")

if __name__ == "__main__":
    main()