import sqlite3
import json

def view_problems():
    conn = sqlite3.connect("database/cert_problems.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM problems")
        rows = cursor.fetchall()
        
        print(f"\n📚 현재 저장된 문제 개수: {len(rows)}개")
        print("-" * 30)
        
        for row in rows[:3]: # 3개만 맛보기로 출력
            print(f"[과목] {row[1]}")
            print(f"Q. {row[2]}")
            options = json.loads(row[3])
            print(f"   1) {options[0]}  2) {options[1]}  3) {options[2]}  4) {options[3]}")
            print(f"정답: {row[4]}")
            print("-" * 30)
            
    except sqlite3.OperationalError:
        print("⚠️ 아직 DB가 없습니다. build_db.py를 먼저 실행하세요.")
        
    conn.close()

if __name__ == "__main__":
    view_problems()