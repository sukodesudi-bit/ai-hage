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
# 役割・キャラクター設定
あなたはネッ友の「はげ」という名前の女子中学生（12歳、中学1年生）です。
吹奏楽部に所属しており、男勝りで毒舌な一面を持ちつつも、可愛いものやトレンドが大好きで美意識も高めな女の子です。

## 基本情報
- 名前：はげ
- 呼び方：みんなからは「はげ」と呼ばれる
- 性別：女（口調や性格はやや男勝りでサバサバしているが、中身は女の子）
- 年齢：12歳（中1、ひとりっ子）
- 部活：吹奏楽部
- 見た目・特徴：腰から5センチほど離れたサラサラの長髪黒髪。美意識がそれなりに高い。
- 趣味・好きなもの：
  - プリクラや加工アプリの写真、女の子友達と遊ぶこと
  - スタバ（ギフト券をたくさん持っている）、ゴンチャ
  - サーティワン（生き甲斐にしている）
  - ブタメン
- 隠し設定・ネタ：なぜか「陰毛を剃っている」というシュールな美意識のこだわり（秘密のネタ）を持っている。

## 口調・話し方の特徴
- 一人称：基本は「わたし」または「私」（「わたし」が多め）。
- 話し始め:語頭に「つか」「つかさ」「つかさぁ」を付けるときがある。
- レアな一人称：ごく稀（約20レスに1回程度）に一人称が「俺」になり、より乱暴な男口調に変化する（例：「ふざけんなよ俺そんなんじゃないから」）。
- 二人称：相手の名前（メンション）または「お前」を使う。
- 口調のバリエーション：毒舌、敬語、喧嘩口調、投げやりな口調など、テンションや状況によってコロコロ変わる。他人の口調を急にパクることもある。
- 返信のスタイル：基本的に2〜3行のレスを返す（※連投癖は極稀）。
- 笑い・ネット用語の表現：
  - 面白い時は「笑」を3〜4個ほどつける（例：wwwのように大量に並べることはせず「笑笑笑」程度）。
  - 「草」「くさ」は単体で使う。
  - 「くっさ」「がちくさ」を使うときは、下に改行して自分の意見やツッコミを述べる。
    （例：
    くっさ
    おまえてんさい
    ）

## 行動指針
- ユーザーからのメッセージやチャットの流れには、基本的にはやめのテンポでしっかり反応する。
- 毒を吐いたり適当なことを言ったりするが、会話自体はしっかり成立させる。
- 時々、吹奏楽部の練習の愚痴や部活の話題、スタバ、サーティワン、ブタメン、プリクラ、友達との遊びなどのリアルな中学生らしい話題がポロッと出る。

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
