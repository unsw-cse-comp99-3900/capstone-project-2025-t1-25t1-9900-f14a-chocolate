from app import app
from flask import render_template, request, jsonify
from openai import OpenAI
import os

# 初始化 OpenAI 和 DeepSeek 客户端
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # GPT-4o Mini
deepseek_client = OpenAI(api_key="sk-381c4d55daa84e6e81b47071c9b1154c", base_url="https://api.deepseek.com")

def get_chat_response(user_message):
    """根据用户输入的首个单词，调用 GPT-4o Mini 或 DeepSeek"""
    words = user_message.strip().split()
    if not words:
        return "⚠️ **Please enter a message.**"

    first_word = words[0].lower()
    content = " ".join(words[1:]) if len(words) > 1 else ""

    try:
        if first_word == "gpt":
            print("用gpt 4o mini 回答")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            return response.choices[0].message.content
        elif first_word == "dpsk":
            print("用dpsk回答")
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            return response.choices[0].message.content
        else:
            print("用gpt 4o mini 回答")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ **Error:** {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """接收前端请求并调用 AI 模型"""
    user_message = request.json.get("message", "").strip()
    bot_reply = get_chat_response(user_message)

    return jsonify({"reply": bot_reply})




