import discord
from discord import app_commands
import random
import os

# RenderのEnvironmentで設定したトークンを読み込む
TOKEN = os.environ.get("DISCORD_TOKEN")

class MyBot(discord.Client):
    def __init__(self):
        # 標準的な権限設定
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # スラッシュコマンドをDiscordに反映させる
        await self.tree.sync()

client = MyBot()

@client.event
async def on_ready():
    print(f"ログイン成功: {client.user.name}")

@client.tree.command(name="lotto", description="ロト7の数字をランダムに7個出します")
async def lotto(interaction: discord.Interaction):
    # 1から38の間で、重複なしで7個選ぶ
    nums = sorted(random.sample(range(1, 39), 7))
    # 数字を見やすく整形 [1, 5, 12...]
    result = "  ".join([f"[{n}]" for n in nums])
    
    await interaction.response.send_message(f"🎰 **ロト7 予想番号** 🎰\n`{result}`\nこの番号を看板に書いてね！")

client.run(TOKEN)
