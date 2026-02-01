import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai

# 스크립트 기준 경로: 프로젝트 루트 = scripts의 상위
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import extract_text as extract_text_module

# .env 로드 (프로젝트 루트 기준)
load_dotenv(PROJECT_ROOT / ".env")

# 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PATH = PROJECT_ROOT / "database" / "cert_problems.db"
DATA_DIR = PROJECT_ROOT / "data"
CHOICE_SEP = "|||"
MAX_CHARS_PER_CHUNK = 4000
SUPPORTED_EXTENSIONS = (".pdf", ".pptx", ".ppt")


def ensure_gemini():
    """Gemini API 키 검사 및 모델 반환."""
    if not GEMINI_API_KEY:
        print("오류: .env 파일에 GEMINI_API_KEY가 없습니다.")
        sys.exit(1)
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-1.5-flash")


def init_database():
    """DB 디렉터리와 problems 테이블 생성."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
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
    """)
    conn.commit()
    conn.close()
    print(f"SQLite DB 준비 완료: {DB_PATH}")


def get_supported_files(dir_path: Path):
    """지원 확장자를 가진 파일 목록 반환 (재귀 없이 data/ 직하위만)."""
    if not dir_path.is_dir():
        return []
    return [
        p for p in dir_path.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def chunk_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK):
    """긴 텍스트를 max_chars 이하 크기로 나눔. 문단(두 줄바꿈) 경계를 우선 존중."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        # 문단 경계 찾기
        chunk = text[start:end]
        last_para = chunk.rfind("\n\n")
        if last_para > max_chars // 2:
            end = start + last_para + 1
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end
    return [c for c in chunks if c]


def parse_text_with_gemini(model, text_chunk: str, source_file: str = ""):
    """
    Gemini로 텍스트에서 문제/선택지/정답/해설 추출.
    반환: (question, choices, answer, explanation) 또는 (None, None, None, None)
    """
    prompt = f"""
당신은 정보처리기사(또는 다른 기사 자격증) 기출문제 파싱 전문가입니다.
아래 텍스트에서 다음 항목을 정확히 추출해서 **정확히** 아래 형식으로만 답변해주세요.
다른 말은 절대 하지 마세요.

형식 (구분자는 {CHOICE_SEP} 사용):
문제 내용{CHOICE_SEP}선택지1{CHOICE_SEP}선택지2{CHOICE_SEP}선택지3{CHOICE_SEP}선택지4{CHOICE_SEP}정답 (예: 3번 또는 정답 내용){CHOICE_SEP}해설 내용

- 만약 4지선다가 아니면 선택지를 가능한 한 맞춰서 채우거나 빈 칸으로 두세요.
- 정답은 번호나 내용 그대로.
- 해설은 자세히 설명.

텍스트:
{text_chunk[:MAX_CHARS_PER_CHUNK]}

답변은 위 형식 한 줄로만 주세요.
"""
    try:
        response = model.generate_content(prompt)
        content = (response.text or "").strip()
        if CHOICE_SEP not in content:
            print("Gemini 응답 형식 오류:", content[:200])
            return None, None, None, None

        parts = content.split(CHOICE_SEP)
        while len(parts) < 7:
            parts.append("")

        question = parts[0].strip()
        choices = CHOICE_SEP.join(parts[1:5]).strip()
        answer = parts[5].strip()
        explanation = parts[6].strip()

        print(f"  파싱 성공 (source: {source_file}) — 질문: {question[:60]}...")
        return question, choices, answer, explanation
    except Exception as e:
        print(f"  Gemini API 오류: {e}")
        return None, None, None, None


def insert_problem(conn, subject: str, question: str, choices: str, answer: str, explanation: str, source: str):
    """DB에 문제 1건 삽입 (conn은 열려 있어야 함)."""
    if not question or not answer:
        return False
    conn.execute("""
        INSERT INTO problems (subject, question, choices, answer, explanation, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (subject, question, choices or "", answer, explanation or "", source or ""))
    return True


def subject_from_filename(file_path: Path) -> str:
    """파일명에서 과목명 후보 추출 (예: 2026_정보처리기사_필기_기출.pdf → 정보처리기사)."""
    name = file_path.stem
    # 숫자·언더스코어 제거 후 첫 번째 의미 단어 사용 등 간단 휴리스틱
    cleaned = re.sub(r"^\d+_?", "", name)
    cleaned = re.sub(r"_(필기|기출|실기|요약)$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.replace("_", " ") or "기출문제"


def extract_text_from_file(file_path: Path) -> str:
    """파일 확장자에 따라 extract_text 모듈로 텍스트 추출."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_module.extract_pdf_text(str(file_path))
    if suffix in (".pptx", ".ppt"):
        return extract_text_module.extract_ppt_text(str(file_path))
    return ""


def process_file(model, file_path: Path, subject: Optional[str] = None):
    """파일 하나를 열어 텍스트 추출 → 청크별 Gemini 파싱 → DB 저장."""
    source_name = file_path.name
    sub = subject or subject_from_filename(file_path)
    text = extract_text_from_file(file_path)
    if not text.strip():
        print(f"  건너뜀 (텍스트 없음): {source_name}")
        return 0

    chunks = chunk_text(text)
    inserted = 0
    conn = sqlite3.connect(str(DB_PATH))
    try:
        for i, chunk in enumerate(chunks):
            q, ch, ans, exp = parse_text_with_gemini(model, chunk, source_name)
            if insert_problem(conn, sub, q or "", ch or "", ans or "", exp or "", source_name):
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    print(f"  저장: {source_name} → {inserted}건")
    return inserted


def main():
    model = ensure_gemini()
    init_database()

    files = get_supported_files(DATA_DIR)
    if not files:
        print(f"처리할 파일이 없습니다. {DATA_DIR}에 .pdf, .pptx, .ppt 파일을 넣어주세요.")
        return

    print(f"총 {len(files)}개 파일 처리 시작.")
    total = 0
    for path in sorted(files):
        print(f"\n처리 중: {path.name}")
        try:
            total += process_file(model, path)
        except Exception as e:
            print(f"  오류: {e}")
    print(f"\n완료. 총 {total}건 저장됨.")


if __name__ == "__main__":
    main()
