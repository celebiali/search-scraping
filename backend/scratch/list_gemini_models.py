import os
import httpx
from dotenv import load_dotenv

# .env dosyasını yükle
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("LLM_API_KEY")

async def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("=== MEVCUT MODELLER ===")
            for m in models:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"- {m['name']} (Destekliyor)")
        else:
            print(f"Hata: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(list_models())
