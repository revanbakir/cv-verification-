from pdfminer.high_level import extract_text
import docx
import os

class CVParser:

    def parse(self, file_path: str) -> str:

        extension = os.path.splitext(file_path)[1]

        if extension == ".pdf":
            return self.parse_pdf(file_path)
        
        elif extension == ".docx":
            return self.parse_docx(file_path)
        
        else:
            raise ValueError("Unsopported file format")
        
        
    def parse_pdf(self, file_path: str) -> str:
        return extract_text(file_path)
    
    def parse_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)

        text = []
        for para in doc.paragraphs:
            text.append(para.text)

        return "\n".join(text)