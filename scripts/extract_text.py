import PyPDF2
from pptx import Presentation
import os

def extract_pdf_text(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"PDF 오류: {e}")
    return text

def extract_ppt_text(ppt_path):
    text = ""
    try:
        prs = Presentation(ppt_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
    except Exception as e:
        print(f"PPT 오류: {e}")
    return text

# 테스트용: data 폴더에 PDF나 PPT 하나 넣고 실행
if __name__ == "__main__":
    # 예시 경로 바꿔서 테스트!
    sample_file = "data/2026_정보처리기사_필기_기출.pdf"  # 실제 파일명으로 변경
    
    if os.path.exists(sample_file):
        if sample_file.lower().endswith(".pdf"):
            extracted = extract_pdf_text(sample_file)
        elif sample_file.lower().endswith((".pptx", ".ppt")):
            extracted = extract_ppt_text(sample_file)
        else:
            print("지원하지 않는 파일 형식입니다.")
            extracted = ""
        
        print("추출된 텍스트 미리보기 (앞 500자):")
        print(extracted[:500])
        print(f"\n전체 길이: {len(extracted)}자")
    else:
        print("파일이 없습니다! data 폴더에 PDF나 PPT 넣어주세요.")