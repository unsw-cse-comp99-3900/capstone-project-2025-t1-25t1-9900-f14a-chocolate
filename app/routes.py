from app import app
from flask import render_template, request, jsonify
from openai import OpenAI
import os
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),  # 日志写入文件
        logging.StreamHandler()  # 日志输出到终端
    ]
)

# 初始化 OpenAI 和 DeepSeek 客户端
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # GPT-4o Mini
openai_client = OpenAI(api_key="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")
deepseek_client = OpenAI(api_key="sk-381c4d55daa84e6e81b47071c9b1154c", base_url="https://api.deepseek.com")


# 统一的回答结尾
ENDING_NOTE = "\n\n🧑‍🏫 我是一个**来自9900F14A-Chocolate的辅导机器人。** 我为进入清洁能源行业或在清洁能源行业内晋升的个人提供量身定制的 STEM 见解、学术建议、再培训途径和技能提升机会，为不同人生阶段提供个性化的职业和教育指导。 "


def get_chat_response(user_message):
    """根据用户输入的首个单词，调用 GPT-4o Mini 或 DeepSeek"""
    words = user_message.strip().split()
    if not words:
        return "⚠️ **Please enter a message.**"

    first_word = words[0].lower()
    content = " ".join(words[1:]) if len(words) > 1 else ""

    try:
        if first_word == "gpt":
            logging.info(f"【GPT-4o Mini】收到用户输入: {content}")
            print("用gpt 4o mini 回答")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            bot_reply =  response.choices[0].message.content
        elif first_word == "dpsk":
            logging.info(f"【DeepSeek】收到用户输入: {content}")
            print("用dpsk回答")
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            bot_reply =  response.choices[0].message.content
        else:
            print("默认用gpt 4o mini 回答")
            logging.info(f"【默认 GPT-4o Mini】收到用户输入: {user_message}")
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": content}
                ]
            )
            bot_reply =  response.choices[0].message.content

        logging.info(f"【AI 回复】{bot_reply}")

        # 在回答后追加结尾语句
        return bot_reply + ENDING_NOTE
    except Exception as e:
        logging.error(f"⚠️ **Error:** {str(e)}")
        return f"⚠️ **Error:** {str(e)}"

@app.route('/')
def home():
    logging.info("【主页访问】用户访问了首页")
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """接收前端请求并调用 AI 模型"""
    user_message = request.json.get("message", "").strip()
    logging.info(f"【请求】用户输入: {user_message}")

    bot_reply = get_chat_response(user_message)
    logging.info(f"【响应】AI 回复: {bot_reply}")
    return jsonify({"reply": bot_reply})




