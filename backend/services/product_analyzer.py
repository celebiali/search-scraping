import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

# Explicitly load .env from the backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

class ProductAnalysis(BaseModel):
    id: str
    product_name: str
    is_main_product: bool = True
    category: Optional[str] = "Unknown"
    sub_category: Optional[str] = "Unknown"
    gender: Optional[str] = "N/A"
    brand: Optional[str] = "Unknown"
    condition: Optional[str] = "New"
    relevance_score: float = 50.0
    reason: Optional[str] = ""

UNIVERSAL_SYSTEM_PROMPT = """
You are the ultimate E-commerce Intelligence and Intent Analysis Engine.
Analyze product titles to distinguish between Core Products, Accessories, Refills, and Noise.

### MASTER CATEGORY & INTENT LOGIC:
1. Electronics (Devices vs Accessories/Cables).
2. Home Appliances (Units vs Parts/Remotes).
3. Audio (Headphones vs Ear tips/Cases).
4. Pet Shop (Food vs Bowls/Leashes).
5. Fitness, Musical Instruments, Fashion, etc.

### TURKISH HEURISTICS:
- Flag 'Boş Kutu', 'Teşhir', 'Arızalı' as is_main_product: false.
- relevance_score MUST be an integer between 0 and 100.

Return a valid JSON array of objects with keys: id, product_name, is_main_product, category, sub_category, gender, brand, condition, relevance_score, reason.
"""

class ProductAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def analyze_products(self, query: str, products: List[Dict[str, Any]]) -> List[ProductAnalysis]:
        if not self.api_key:
            print("Warning: LLM_API_KEY not found.")
            return [self._default_analysis(p) for p in products]

        product_list_str = "\n".join([f"ID: {p['id']} | Title: {p['title']}" for p in products])
        
        # Native Gemini payload structure
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{UNIVERSAL_SYSTEM_PROMPT}\n\nSearch Query: '{query}'\n\nProducts:\n{product_list_str}\n\nReturn JSON array only."
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}"

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content_text = result['candidates'][0]['content']['parts'][0]['text']
            data = json.loads(content_text)
            
            # Handle potential list wrap
            if isinstance(data, dict) and "products" in data:
                data = data["products"]

            return [ProductAnalysis(**item) for item in data]

        except Exception as e:
            if hasattr(e, 'response'):
                print(f"Gemini API Error Body: {e.response.text}")
            print(f"Gemini API Error: {e}")
            return [self._default_analysis(p) for p in products]

    def _default_analysis(self, product: Dict[str, Any]) -> ProductAnalysis:
        return ProductAnalysis(
            id=str(product.get('id')),
            product_name=product.get('title', 'Unknown'),
            is_main_product=True,
            category="Unknown",
            sub_category="Unknown",
            gender="N/A",
            brand="Unknown",
            condition="Unknown",
            relevance_score=50,
            reason="Analysis failed."
        )

    async def close(self):
        await self.client.aclose()
