import asyncio
import os
import sys

# Ensure the 'backend' directory is in the python path at the very beginning
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.product_analyzer import ProductAnalyzer
from dotenv import load_dotenv

load_dotenv()

async def run_test_cases():
    analyzer = ProductAnalyzer()
    
    test_scenarios = [
        {
            "query": "Dyson V15",
            "products": [
                {"id": "v15_1", "title": "Dyson V15 Detect Kablosuz Süpürge"},
                {"id": "v15_2", "title": "Dyson V15 Hepa Filtre Yedek Parça"},
                {"id": "v15_3", "title": "Dyson V15 Boş Kutu ve Kullanım Kılavuzu"}
            ]
        },
        {
            "query": "RTX 4090",
            "products": [
                {"id": "gpu_1", "title": "MSI GeForce RTX 4090 Suprim X 24G"},
                {"id": "gpu_2", "title": "RTX 4090 Ekran Kartı Destek Aparatı"},
                {"id": "gpu_3", "title": "RTX 4090 12VHPWR Power Kablosu"}
            ]
        },
        {
            "query": "Lancome Idole Parfüm",
            "products": [
                {"id": "cos_1", "title": "Lancome Idole EDP 100 ml Kadın Parfüm"},
                {"id": "cos_2", "title": "Lancome Idole Parfüm Boş Şişe 50ml (Koleksiyonluk)"},
                {"id": "cos_3", "title": "Lancome Idole Vücut Losyonu 200ml"}
            ]
        },
        {
            "query": "Bosch Fırın",
            "products": [
                {"id": "app_1", "title": "Bosch HBF113BR0T Ankastre Fırın"},
                {"id": "app_2", "title": "Bosch Uyumlu Fırın Tepsisi 45cm"},
                {"id": "app_3", "title": "Bosch Fırın Düğmesi Seti (6 Adet)"}
            ]
        }
    ]

    print("=== UNIVERSAL PRODUCT ANALYZER TEST START ===\n")

    if not os.getenv("LLM_API_KEY"):
        print("!!! ERROR: LLM_API_KEY not found in environment variables. !!!")
        print("Please add 'LLM_API_KEY=your_key' to your .env file.\n")

    for scenario in test_scenarios:
        query = scenario["query"]
        products = scenario["products"]
        
        print(f"--- Scenario: Searching for '{query}' ---")
        results = await analyzer.analyze_products(query, products)
        
        for res in results:
            status = "✅ MAIN" if res.is_main_product else "❌ NOT MAIN"
            print(f"[{res.relevance_score}/100] {status} | {res.product_name}")
            print(f"    - Category: {res.category} / {res.sub_category}")
            print(f"    - Reason: {res.reason}\n")
        
        print("-" * 50)

    await analyzer.close()

if __name__ == "__main__":
    asyncio.run(run_test_cases())
