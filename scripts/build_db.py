import os
import json
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv
from extract_text import get_all_text

# 1. API 키 로드
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 2. DB 연결 및 테이블 생성
def init_db():
    conn = sqlite3.connect("database/cert_problems.db")
    c = conn.cursor()
    # 문제 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS problems
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  subject TEXT,
                  question TEXT,
                  options TEXT,
                  answer TEXT,
                  explanation TEXT,
                  source_file TEXT)''')
    conn.commit()
    return conn

# 3. Gemini에게 문제 출제 요청
def generate_quiz_from_text(text):
    model = genai.GenerativeModel("gemini-pro")
    
    prompt = f"""
    너는 정보처리기사 자격증 문제 출제 위원이야.
    아래 텍스트를 분석해서 객관식 문제 3개를 만들어줘.
    
    [텍스트 내용]
    {text[:5000]}  # 너무 길면 자름
    
    [출력 형식]
    반드시 순수한 JSON 배열 형식으로만 답해줘. 마크다운(```json) 쓰지 마.
    형식 예시:
    [
        {{
            "subject": "과목명(예: 소프트웨어설계)",
            "question": "문제 내용",
            "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
            "answer": "정답(선택지 중 하나)",
            "explanation": "해설"
        }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        # 혹시 마크다운이 섞여 있으면 제거
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"⚠️ AI 변환 실패: {e}")
        return []

# 4. 메인 실행 함수
def run():
    # DB 초기화
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = init_db()
    cursor = conn.cursor()

    # 텍스트 추출
    docs = get_all_text("data")
    
    if not docs:
        print("❌ 처리할 데이터가 없습니다. data 폴더에 파일을 넣어주세요.")
        return

    print("🚀 Gemini가 문제를 생성 중입니다... (시간이 좀 걸립니다)")
    
    total_added = 0
    for doc in docs:
        print(f"   Processing: {doc['filename']}...")
        problems = generate_quiz_from_text(doc['text'])
        
        for p in problems:
            cursor.execute('''INSERT INTO problems (subject, question, options, answer, explanation, source_file)
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                              (p.get('subject', 'General'), 
                               p['question'], 
                               json.dumps(p['options'], ensure_ascii=False), # 리스트를 문자로 저장
                               p['answer'], 
                               p['explanation'],
                               doc['filename']))
            total_added += 1
            
    conn.commit()
    conn.close()
    print(f"\n🎉 총 {total_added}개의 문제가 DB에 저장되었습니다!")

if __name__ == "__main__":
    run()