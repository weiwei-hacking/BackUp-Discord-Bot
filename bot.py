import os
import json
import discord
import psutil
from discord.ext import tasks
from discord import app_commands

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"目前登入身份 --> {client.user.name}")
    await load_all_members()
    await update_status.start()

@tasks.loop(seconds=15)
async def update_status():
    total_members = 0
    for guild in client.guilds:
        total_members += guild.member_count

    status = f"{len(client.guilds)} 個伺服器  |  總人數 {total_members}"
    await client.change_presence(activity=discord.Game(name=status))

async def load_all_members():
    for guild in client.guilds:
        async for member in guild.fetch_members(limit=None):
            pass

class Basic(app_commands.Group):
    ...
basic = Basic(name="基礎版", description="基礎版功能")
tree.add_command(basic)

@tree.command(name="狀態", description="查詢機器人狀態")
async def status(ctx):
    latency = client.latency * 1000  # 將延遲轉換為毫秒
    cpu_percent = psutil.cpu_percent()
    owner_id = (await client.application_info()).owner.id
    total_members = 0
    for guild in client.guilds:
        total_members += guild.member_count
    embed = discord.Embed(title="機器人狀態", color=0x00ff00)
    embed.add_field(name="延遲", value=f"{latency:.2f} ms", inline=True)
    embed.add_field(name="CPU 使用率", value=f"{cpu_percent:.2f}%", inline=True)
    embed.add_field(name="RAM 使用率", value=f"{psutil.virtual_memory().percent}%", inline=True)
    embed.add_field(name="伺服器總數", value=f"**{len(client.guilds)}** 個伺服器", inline=True)
    embed.add_field(name="伺服器人數", value=f"**{total_members}** 個人", inline=True)
    embed.add_field(name="機器人擁有者", value=f"<@{owner_id}> ({owner_id})", inline=True)
    await ctx.response.send_message(embed=embed)

@tree.command(name="邀請", description="把我邀請製你的伺服器")
async def invite(ctx):
    embed = discord.Embed(title="連結列表", description="[點我把我邀進你的伺服器](https://discord.com/oauth2/authorize?client_id=1246709247945867284)\n[我們的官方伺服器](https://discord.gg/daFQhVFGKj)", color=0x3498DB)
    await ctx.response.send_message(embed=embed)

@tree.command(name="幫助", description="顯示該機器人的幫助介面")
async def help_command(ctx):
    embed = discord.Embed(title="備份機器人幫助介面", description="需要幫助嗎? 加入我們的 [Discord](https://discord.gg/daFQhVFGKj) 並開啟一個票單來與客服人員對談。", color=0x00bbff)
    embed.add_field(name="通用功能", value="""</幫助:1251343415082352673> 顯示這個機器人的指令列表
                                                        </狀態:1251343415082352671> 查詢目前機器人的延遲、CPU和RAM使用率、擁有者ID等
                                                        </邀請:1251343415082352672> 取得這個機器人的邀請連結
                                                        """, inline=False)
    embed.add_field(name="主要功能", value="""</基礎版 備份:1251343415082352670> 備份伺服器的分類、頻道、身分組
                                                         </基礎版 還原:1251343415082352670> 還原伺服器的分類、頻道、身分組 (讀取備份過的數據)
                                                        """, inline=False)
    await ctx.response.send_message(embed=embed)


@basic.command(name="備份", description="備份伺服器的頻道和身分組資訊")
async def basic_backup(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        embed = discord.Embed(description="> 您需要成為 `伺服器擁有者` 才能執行該指令", color=0xFF0000)
        embed.set_author(name="缺少權限")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild = interaction.guild
    guild_id = str(guild.id)
    backup_path = f"Servers/{guild_id}"

    if os.path.exists(backup_path):
        view = ConfirmView()
        embed = discord.Embed(description="> 該伺服器已存在一份備份檔，您是否要覆蓋並建立新的備份檔?", color=0xFF0000)
        embed.set_author(name="備份檔已存在")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if not view.value:
            await interaction.edit_original_response(content="操作已取消。")
            return
        await interaction.edit_original_response(content="正在進行備份...")
    else:
        os.makedirs(backup_path)
        await interaction.response.send_message("正在進行備份...")

    # 備份頻道和分類
    categories = []
    for category in guild.categories:
        cat_data = {
            "name": category.name,
            "position": category.position,
            "channels": []
        }
        for channel in category.channels:
            if not isinstance(channel, (discord.ForumChannel, discord.TextChannel)) or not channel.is_news():
                cat_data["channels"].append({
                    "name": channel.name,
                    "position": channel.position,
                    "type": str(channel.type)
                })
        categories.append(cat_data)

    with open(f"{backup_path}/categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

    # 備份身分組
    roles = []
    for role in guild.roles:
        if not role.managed and role.name != "@everyone":
            roles.append({
                "name": role.name,
                "color": role.color.value,
                "position": role.position
            })

    with open(f"{backup_path}/roles.json", "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=4)

    await interaction.edit_original_response(content="伺服器備份完成！")

    embed = discord.Embed(title="✅伺服器已備份完成 | 基礎版", color=0x00ff00)
    embed.add_field(name="頻道和分類 | ✅ 1/3", value="""> ✅ | 分類、頻道名稱
                                                          > ❌ | 分類、頻道權限
                                                          > ❌ | 分類、頻道概要""")
    embed.add_field(name="身分組 | ✅ 2/3", value="""> ✅ | 身分組名稱
                                                     > ✅ | 身分組顏色
                                                     > ❌ | 身分組權限""")
    embed.add_field(name="伺服器設定 | ✅ 0/2", value="""> ❌ | 伺服器名稱
                                                          > ❌ | 社群概要""")

    # 如果之前已經回應過互動（例如，在確認覆蓋時），使用 followup.send
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed)
    else:
        # 如果還沒有回應過互動，直接使用 response.send_message
        await interaction.response.send_message(embed=embed)

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="否", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()





@basic.command(name="還原", description="從備份檔案還原伺服器設置")
async def restore_backup(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        embed = discord.Embed(description="> 您需要成為 `伺服器擁有者` 才能執行該指令", color=0xFF0000)
        embed.set_author(name="缺少權限")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild = interaction.guild
    guild_id = str(guild.id)
    backup_path = f"Servers/{guild_id}"

    if not os.path.exists(backup_path):
        await interaction.response.send_message("沒有找到備份檔案,無法執行還原操作。", ephemeral=True)
        return

    view = ConfirmView()
    await interaction.response.send_message("是否要執行還原操作?\n該操作並不會刪除現有頻道分類身分組等", view=view, ephemeral=True)
    await view.wait()

    if not view.value:
        await interaction.edit_original_response(content="操作已取消。", view=None)
        return

    notify_view = NotifyView()
    await interaction.edit_original_response(content="是否需要通知您還原進度?", view=notify_view)
    await notify_view.wait()

    if notify_view.value:
        await interaction.user.send("正在執行還原操作...")

    await interaction.edit_original_response(content="正在執行還原操作...", view=None)

    # 還原頻道和分類
    with open(f"{backup_path}/categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    for category_data in categories:
        category = await guild.create_category(name=category_data["name"], position=category_data["position"])
        for channel_data in category_data["channels"]:
            channel_type = getattr(discord.ChannelType, channel_data["type"])
            if channel_type == discord.ChannelType.text:
                await category.create_text_channel(name=channel_data["name"], position=channel_data["position"])
            elif channel_type == discord.ChannelType.voice:
                await category.create_voice_channel(name=channel_data["name"], position=channel_data["position"])
            if notify_view.value:
                await interaction.user.send(f"已創建頻道: {channel_data['name']}")

    # 還原身分組
    with open(f"{backup_path}/roles.json", "r", encoding="utf-8") as f:
        roles = json.load(f)

    existing_roles = [role.name for role in guild.roles]
    for role_data in roles:
        if role_data["name"] not in existing_roles:
            await guild.create_role(name=role_data["name"], color=discord.Color(role_data["color"]))
            if notify_view.value:
                await interaction.user.send(f"已創建身分組: {role_data['name']}")

    await interaction.edit_original_response(content="伺服器還原完成!")

    if notify_view.value:
        await interaction.user.send("伺服器還原操作已完成!")

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="否", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

class NotifyView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = False

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="否", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.stop()




client.run("機器人Token貼這裡")
