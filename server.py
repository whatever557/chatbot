import openai
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  # Flutter 연동 위해 CORS 허용

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

@app.route('/edt_type', methods=['POST'])
def edt_type_analysis():
    data = request.json
    answers = data['answers']  # 사용자의 문항 응답 리스트

    user_responses = "\n".join([f"{i+1}. {q}" for i, q in enumerate(answers)])

    messages = [
        {
            "role": "system",
            "content": "당신은 학생의 학습 유형을 분석하는 전문가입니다. 주어진 질문에 대한 응답을 바탕으로 EDT(인지, 동기, 행동) 학습유형을 분석하세요."
        },
        {
            "role": "user",
            "content": f"""다음은 학생의 학습유형 간편검사 응답입니다:
{user_responses}

이 응답을 바탕으로 이 학생의 학습유형을 '인지적(Cognitive)', '동기적(Motivational)', '행동적(Behavioral)' 관점에서 분석하고,
해당 유형의 특징과 그에 맞는 학습 전략도 함께 알려주세요."""
        }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )
        result = response.choices[0].message.content.strip()
        return jsonify({"edt_analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
