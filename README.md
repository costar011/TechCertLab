# TechCertLab  
기술 자격증 AI 학습 연구소

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-74aa9c?style=for-the-badge&logo=openai&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

> 국가기술자격(기사·산업기사) 준비를 위한 **AI 기반 개인화 학습 플랫폼**  
> PDF/PPT 기출·교재 자료 자동 파싱 → 문제 은행 DB 구축 → 오답노트·약점 분석·인터랙티브 퀴즈까지  

## 프로젝트 개요

**TechCertLab**은 국가기술자격 시험 준비를 체계화·효율화하기 위해 개발한 **AI 보조 학습 시스템**입니다.

**핵심 목표**
- 기출문제·교재 PDF/PPT 대량 수집 및 자동 텍스트 추출
- OpenAI API를 활용한 문제·선택지·정답·해설 자동 파싱 및 생성
- 오답노트 자동 기록 + AI 추가 해설 생성

**초기 타겟**: 정보처리기사 (필기 + 실기)

## 폴더 및 파일 구조

```plaintext
TechCertLab/
├── data/                     # 기출·교재 PDF, PPT 파일 저장
│   ├── 정보처리기사_필기_기출/
│   ├── 정보처리기사_실기_요약/
│   └── 다른_종목/            # 나중 확장용 
├── database/                 # SQLite DB 파일
│   └── cert_problems.db
├── scripts/                  # 핵심 Python 스크립트
│   ├── extract_text.py       # PDF/PPT 텍스트 추출
│   ├── build_db.py           # AI 파싱 → DB 저장
│   ├── wrong_note.py         # 오답노트 추가 & AI 해설 생성
│   ├── weak_analysis.py      # 약점 분석 + 그래프 출력
│   └── quiz_app.py           # Streamlit 기반 퀴즈 웹앱
├── requirements.txt          # 필요한 패키지 목록
├── .env                      # OpenAI API 키 (Git 무시)
├── .gitignore                # Git 무시 파일
├── README.md
└── docs/                     # 추가 문서·스크린샷·사용 가이드