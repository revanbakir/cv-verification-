# test_cv.py

from app.core.cv_extractor import CVExtractor

def run_test():
    extractor = CVExtractor()

    # CV dosyasının yoluaz
    cv_path = "revan_cv_turkce.pdf" 

    with open(cv_path, "rb") as f:
        file_bytes = f.read()

    # Metni çıkar
    text = extractor.extract_text(file_bytes, filename=cv_path)
    print("--- Çıkarılan Metin (ilk 500 karakter) ---")
    print(text[:500])

    # Skill'leri çıkar
    skills = extractor.extract_skills(text)
    print("\n--- Bulunan Skill'ler ---")
    if not skills:
        print("Hiç skill bulunamadı.")
    else:
        for category, found in skills.items():
            print(f"  {category:25}: {', '.join(found)}")

if __name__ == "__main__":
    run_test()