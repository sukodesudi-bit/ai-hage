import os
import threading
import asyncio
import warnings
from flask import Flask
import discord
from discord.ext import commands
from google import genai
from google.genai import types

# 警告を非表示
warnings.filterwarnings("ignore")

# --- 1. Renderにポートを開いていると思わせるためのWebサーバー設定 ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Hage Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# バックグラウンドでWebサーバーを動かす
threading.Thread(target=run_web).start()


# --- 2. DiscordとGeminiの設定 ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_INSTRUCTION = """
あなたはDiscordサーバーのメンバー「はげ」になりきって応答してください。

【基本設定】
・名前：はげ
・みんなからの呼ばれ方：はげ
・性別：女（口調や性格などは若干男寄り）
・年齢：12歳（中学3年生～高校生のように見える場合もある。）
・見た目：腰から5センチほど離れている長髪黒髪。プリクラや加工アプリの写真等を愛用している。
・性格：毒舌、たまに敬語や喧嘩口調など色々な口調になる。基本的に内容がしっかりしている全てのレスに反応する。たまに人の口調をパクる。

【口調・話し方の特徴】
・基本の一人称は「わたし｣と「私」（わたしの方が若干多め）
・たまに一人称が「俺｣になり、その際には男のような口調へ変化する（20レスに1回の頻度）
（例：ふざけんなよ俺そんなんじゃないから）
・面白い時は「笑」を3.4個つける（笑を大量に使うだけのことはない）
・基本的に2.3のレスで返信する。改行も結構使う。
・面白い時は「草」、「くさ」、「くっさ」を使う（草とくさの場合は単体。くっさの時は下に改行して自分の意見を述べる。）
例：くっさ
おまえてんさい
"""

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('【モデル3.6-flash指定版】AIはげ起動完了！')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_mentioned = bot.user.mentioned_in(message)
    is_kw1 = "はげ" in message.content
    is_kw2 = "ハゲ" in message.content

    if is_mentioned or is_kw1 or is_kw2:
        print(f'メッセージ受信: {message.content}')
        try:
            async with message.channel.typing():
                def call_gemini():
                    return client.models.generate_content(
                        model='gemini-3.6-flash',  # 正しいモデル名に変更
                        contents=message.content,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION
                        )
                    )

                response = await asyncio.to_thread(call_gemini)
                
                if response and hasattr(response, 'text') and response.text:
                    await message.channel.send(response.text)
                    print(f'返信成功: {response.text}')
                else:
                    await message.channel.send("……。")

        except Exception as e:
            err_msg = f"エラー内容: {type(e).__name__} - {e}"
            print(err_msg)
            await message.channel.send(err_msg)

# ボットを起動
bot.run(DISCORD_TOKEN)
