import pandas as pd
import json

def build_map_from_stacksample(csv_path):
    print("Veri seti okunuyor... (Bu biraz vakit alabilir)")
    df = pd.read_csv(csv_path)

    # 1. Popüler dilleri belirleyelim (Bunlar bizim ana kategorilerimiz olacak)
    main_techs = {'python', 'java', 'javascript', 'c#', 'php', 'c++', 'ruby', 'go', 'rust', 'dart', 'swift'}
    
    # 2. Aynı Id'ye sahip etiketleri grupla
    # Bu sayede hangi kütüphane hangi dille beraber kullanılmış bulacağız
    print("İlişkiler analiz ediliyor...")
    grouped = df.groupby('Id')['Tag'].apply(list)
    
    master_map = {}

    for tags in grouped:
        # Bu soruda geçen ana dilleri bul
        found_main_techs = [t for t in tags if t in main_techs]
        
        if found_main_techs:
            for tag in tags:
                if tag not in main_techs: # Kütüphane ise
                    if tag not in master_map:
                        master_map[tag] = set()
                    # Kütüphaneyi bulduğumuz ana dillerle eşleştir
                    master_map[tag].update(found_main_techs)

    # Set nesnelerini listeye çevir (JSON için)
    final_map = {k: list(v) for k, v in master_map.items()}

    # Sonucu kaydet
    with open("app/data/master_tech_map.json", "w", encoding="utf-8") as f:
        json.dump(final_map, f, indent=4)
    
    print(f"Bitti! {len(final_map)} adet kütüphane-dil ilişkisi çıkarıldı.")

build_map_from_stacksample("app/data/Tags.csv")