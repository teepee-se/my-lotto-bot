import discord
from discord.ext import commands, tasks
import random
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
import threading

# --- 設定 ---
# トークンは直接書かず、Renderの管理画面（Environment）から設定します
TOKEN = os.environ.get("DISCORD_TOKEN")
# 発表したいDiscordチャンネルのIDをここに入力してください
CHANNEL_ID = 1480354347908071565  

# --- データ管理機能 ---
DATA_FILE = "kuji_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Flask Server (マイクラからの受信用) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/buy', methods=['POST'])
def buy_kuji():
    content = request.json
    mc_name = content.get("mc_name")
    nums = content.get("numbers")

    # 1-38の範囲外がないかチェック
    if not mc_name or len(nums) != 7 or any(n < 1 or n > 38 for n in nums):
        return jsonify({"status": "error", "message": "Invalid numbers"}), 400

    data = load_data()
    data[mc_name] = {"numbers": nums, "date": datetime.now().strftime("%Y-%m-%d %H:%M")}
    save_data(data)
    
    print(f"【購入成功】 {mc_name}: {nums}")
    return jsonify({"status": "success"}), 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- Discord Bot ---
class KujiBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        self.check_friday.start()
        await self.tree.sync()

    @tasks.loop(minutes=30)
    async def check_friday(self):
        now = datetime.now()
        # 金曜日 21:00 ~ 21:30 の間に抽選実行
        if now.strftime("%a") == "Fri" and now.hour == 21 and now.minute < 30:
            await self.lottery_draw()

    async def lottery_draw(self):
        data = load_data()
        if not data:
            return

        winning_nums = sorted(random.sample(range(1, 39), 7))
        winners = []

        for name, info in data.items():
            if set(info["numbers"]) == set(winning_nums):
                winners.append(name)

        channel = self.get_channel(CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="🎰 ロト7 当選発表！", color=0xFFD700)
            embed.add_field(name="本日の当選番号", value=" ".join([f"`{n}`" for n in winning_nums]), inline=False)
            
            result_msg = "、".join(winners) if winners else "当選者はいませんでした。"
            embed.add_field(name="🎊 当選者（全一致）", value=result_msg, inline=False)
            
            await channel.send(embed=embed)

        # 抽選後にデータをリセット
        save_data({})

client = KujiBot()

@client.event
async def on_ready():
    print(f"ログイン成功: {client.user.name}")

@client.tree.command(name="force_draw", description="今すぐ抽選を実行します")
@discord.app_commands.checks.has_permissions(administrator=True)
async def force_draw(interaction: discord.Interaction):
    await client.lottery_draw()
    await interaction.response.send_message("抽選を実行しました！", ephemeral=True)

# サーバー起動
threading.Thread(target=run_flask, daemon=True).start()
client.run(TOKEN)

