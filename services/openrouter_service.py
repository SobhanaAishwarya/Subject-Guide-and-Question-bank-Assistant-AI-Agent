import requests
import json
from config import Config

class OpenRouterService:
    @staticmethod
    def complete(messages: list, stream: bool = False):
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8501",
            "X-Title": "EduMind AI Platform"
        }
        payload = {
            "model": Config.DEFAULT_MODEL,
            "messages": messages,
            "stream": stream
        }
        
        try:
            response = requests.post(
                f"{Config.BASE_URL}/chat/completions",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"API Processing Interface Error: Code {response.status_code} - {response.text}"
        except Exception as e:
            return f"Runtime Backend Connection Exception: {str(e)}"