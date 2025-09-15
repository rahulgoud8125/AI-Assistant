import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    model = genai.GenerativeModel(model_name="models/gemini-pro")
    response = model.generate_content("What is the full form of SQL?")
    print(response.text)
except Exception as e:
    print("Error:", e)
