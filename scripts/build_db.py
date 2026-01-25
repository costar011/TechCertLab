import os
import sqlite3
import sys

from dotenv import load_dotenv
import google.generativeai as genai

# .env 로드
load_dotenv()

# Gemini API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("오류: .env 파일에 GEMINI_API_KEY가 없습니다.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# DB 경로
DB_PATH = "../database/cert_problems.db"

def init_database():
    """DB 파일과 테이블 생성/확인"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            question TEXT,
            choices TEXT,
            answer TEXT,
            explanation TEXT,
            wrong_count INTEGER DEFAULT 0,
            source TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"SQLite DB 준비 완료: {DB_PATH}")

def parse_text_with_gemini(text_chunk, source_file=""):
    """
    Gemini에게 텍스트를 주고 문제/선택지/정답/해설을 추출하게 함
    반환 형식: question, choices (||| 구분), answer, explanation
    """
    prompt = f"""
당신은 정보처리기사(또는 다른 기사 자격증) 기출문제 파싱 전문가입니다.
아래 텍스트에서 다음 항목을 정확히 추출해서 **정확히** 아래 형식으로만 답변해주세요.
다른 말은 절대 하지 마세요.

형식 (구분자는 ||| 사용):
문제 내용|||선택지1|||선택지2|||선택지3|||선택지4|||정답 (예: 3번 또는 정답 내용)|||해설 내용

- 만약 4지선다가 아니면 선택지를 가능한 한 맞춰서 채우거나 빈 칸으로 두세요.
- 정답은 번호나 내용 그대로.
- 해설은 자세히 설명.

텍스트:
{text_chunk[:4000]}  # 토큰 제한 대비 자름

답변은 위 형식 한 줄로만 주세요.
"""

    try:
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Gemini가 추가 텍스트를 붙일 수 있으니 안전하게 파싱
        if "|||" not in content:
            print("Gemini 응답 형식 오류:", content[:200])
            return None, None, None, None

        parts = content.split("|||")
        if len(parts) < 7:
            # 부족하면 채우기 시도
            while len(parts) < 7:
                parts.append("")

        question = parts[0].strip()
        choices = "|||".join(parts[1:5]).strip()  # 1~4번 선택지
        answer = parts[5].strip()
        explanation = parts[6].strip()

        print(f"파싱 성공 (source: {source_file})")
        print(f"질문 미리보기: {question[:80]}...")

        return question, choices, answer, explanation

    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return None, None, None, None

def insert_to_db(subject, question, choices, answer, explanation, source=""):
    """DB에 저장"""
    if not question or not answer:
        print("유효하지 않은 파싱 결과 → 저장 스킵")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO problems 
        (subject, question, choices, answer, explanation, source)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (subject, question, choices, answer, explanation, source))
    conn.commit()
    conn.close()
    print("DB에 1건 저장 완료")

def main():
    init_database()

    # Gemini로 파싱
    # TODO: test_text 변수를 정의하거나 파일에서 읽어와야 합니다
    # q, ch, ans, exp = parse_text_with_gemini(test_text, source_file="test_sample.txt")
    #
    # if q:
    #     insert_to_db(
    #         subject="소프트웨어 설계",
    #         question=q,
    #         choices=ch,
    #         answer=ans,
    #         explanation=exp,
    #         source="test_sample.txt"
    #     )
    # else:
    #     print("테스트 파싱 실패")
    pass


if __name__ == "__main__":
    main()