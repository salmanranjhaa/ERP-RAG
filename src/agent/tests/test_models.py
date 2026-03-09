import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    print("Testing Kimi (moonshotai/kimi-k2-instruct-0905)...")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say hello from Kimi!",
            }
        ],
        model="moonshotai/kimi-k2-instruct-0905",
    )
    print("Response:", chat_completion.choices[0].message.content)
except Exception as e:
    print("Kimi Error:", e)

try:
    print("\nTesting Llama (llama-3.3-70b-versatile)...")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say hello from Llama!",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("Response:", chat_completion.choices[0].message.content)
except Exception as e:
    print("Llama Error:", e)
