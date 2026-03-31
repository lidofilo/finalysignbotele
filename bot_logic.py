from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME
from telegram import ReplyKeyboardMarkup

class FinalySignBot:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.system_prompt = "أنت المساعد الذكي لشركة FinalySign. تخصصنا: مواقع، تطبيقات، سوشيال ميديا."

    def main_keyboard(self):
        return ReplyKeyboardMarkup([['🌐 خدماتنا', '📞 طلب استشارة'], ['💬 موظف مختص', '📝 عن الشركة']], resize_keyboard=True)

    def get_ai_response(self, user_text):
        completion = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_text}]
        )
        return completion.choices[0].message.content