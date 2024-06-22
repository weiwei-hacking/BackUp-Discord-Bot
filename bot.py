import psutil
import discord
import os
import time
import json
import asyncio
from discord import app_commands, Interaction, Embed, ui
from discord.errors import HTTPException
from discord.ext import tasks

intents = discord.Intents.all()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
all_permissions = [name for name, _ in discord.Permissions.VALID_FLAGS.items()]

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
    embed = discord.Embed(title="連結列表", description="[點我把我邀進你的伺服器](https://discord.com/oauth2/authorize?client_id=1246709247945867284)\n[我們的官方伺服器](https://discord.gg/daFQhVFGKj)", color=0x5a5fcf)
    await ctx.response.send_message(embed=embed)

@tree.command(name="幫助", description="顯示該機器人的幫助介面")
async def help_command(ctx):
    embed = discord.Embed(title="備份機器人幫助介面", description="需要幫助嗎? 加入我們的 [Discord](https://discord.gg/daFQhVFGKj) 並開啟一個票單來與客服人員對談。", color=0x5a5fcf)
    embed.add_field(name="主要功能", value="/創建 - 創建伺服器備份檔\n/讀取 - 讀取伺服器備份檔", inline=False)
    await ctx.response.send_message(embed=embed)








async def create_archive(server):
    current_time = int(time.time())
    folder_name = f"save/{server.id}_{current_time}"
    os.makedirs(folder_name, exist_ok=True)

    # 建立 settings.json
    settings = {
        "server_name": server.name,
        "inactive_channels": [],
        "system_messages": True,
        "default_notifications": "@everyone"
    }
    with open(f"{folder_name}/settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

    # 建立 roles.json
    roles = []
    for role in server.roles:
        # 跳過機器人自己生成的身分組
        if role.is_bot_managed():
            continue
        role_data = {
            "name": role.name,
            "color": role.color.value,
            "permissions": role.permissions.value
        }
        roles.append(role_data)
    with open(f"{folder_name}/roles.json", "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=4)

    # 建立 channels.json
    channels = []
    categories = []
    for channel in server.channels:
        if isinstance(channel, discord.CategoryChannel):
            category_data = {
                "name": channel.name,
                "channels": []
            }
            categories.append(category_data)
        elif not isinstance(channel, discord.StageChannel) and not isinstance(channel, discord.ForumChannel):
            if not categories:
                categories.append({"name": "Uncategorized", "channels": []})
            channel_data = {
                "name": channel.name,
                "type": channel.type.name
            }
            categories[-1]["channels"].append(channel_data)
    channels.extend(categories)
    with open(f"{folder_name}/channels.json", "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)

    # 儲存 server icon
    if server.icon:
        icon_bytes = await server.icon.read()
        with open(f"{folder_name}/icon.png", "wb") as f:
            f.write(icon_bytes)

    return folder_name

# 定義 /create 指令
@tree.command(name="創建", description="創建一個伺服器的備份檔")
@app_commands.checks.has_permissions(administrator=True)
async def create(interaction: Interaction):
    server = interaction.guild

    # 回覆使用者,告知存檔建立中
    embed = Embed(title="伺服器存檔建立中", description=f"伺服器的存檔正在建立中...\n機器人將會私訊進度給: {interaction.user.mention}", color=0x5a5fcf)
    embed.add_field(name="\n請務必將啟用 `隱私 & 安全` 中的 `允許來自伺服器成員的私人訊息`\n若未啟用，該功能將無法運作", value="")
    await interaction.response.send_message(embed=embed)


    embed = Embed(title="伺服器存檔創建中...", color=0x5a5fcf)
    embed.add_field(name=f"""
> 伺服器名稱: {server.name}
> 伺服器ID: {server.id}
> 開始建立時間: <t:{int(time.time())}>""", value="", inline=False)
    await interaction.user.send(embed=embed)



    # 私訊使用者存檔進度
    progress_embed = Embed(title="", description="[⌛] 存檔中 | [✅] 已存檔", color=0x5a5fcf)
    progress_message = await interaction.user.send(embed=progress_embed)

    # 真實存檔進度
    step_names = ["伺服器設定檔", "伺服器身分組", "分類及頻道", "伺服器圖標"]
    for i, step in enumerate(step_names):
        await progress_message.edit(embed=progress_embed.add_field(name=step, value="⌛", inline=False))
        # 執行對應的存檔操作
    folder_name = await create_archive(server)
    for i, step in enumerate(step_names):
        progress_embed.set_field_at(i, name=step, value="✅", inline=False)
        await progress_message.edit(embed=progress_embed)

    # 私訊使用者存檔完成訊息
    embed = Embed(title="", description=f":white_check_mark: | :regional_indicator_b: :regional_indicator_a: :regional_indicator_c: :regional_indicator_k: :regional_indicator_u: :regional_indicator_p: :regional_indicator_c: :regional_indicator_r: :regional_indicator_e: :regional_indicator_a: :regional_indicator_t: :regional_indicator_e: :regional_indicator_d:" ,color=0x5a5fcf)
    embed.add_field(name=f"""
» **{server.name} (ID: {server.id})** 伺服器存檔已建立完成!

» 如果你要還原伺服器的存檔請使用 `/讀取`
» 請不要洩漏伺服器還原ID碼，因為這包含了伺服器的內容

» 還原ID: ||{folder_name.split('/')[-1]}||""", value="", inline=False)
    await interaction.user.send(embed=embed)





class ConfirmView(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        self.value = True
        self.stop()
        await interaction.response.send_modal(BackupIDModal())

    @ui.button(label="否", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        self.value = False
        self.stop()
        await interaction.response.send_message("操作已取消。", ephemeral=True)

class BackupIDModal(ui.Modal, title="輸入備份 ID"):
    backup_id = ui.TextInput(label="備份 ID", placeholder="請輸入備份 ID")

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()
        await load_backup(interaction, self.backup_id.value)

def is_community_channel(channel):
    if isinstance(channel, discord.TextChannel):
        if channel.is_news():
            return True
        if channel.guild.rules_channel == channel or channel.guild.public_updates_channel == channel:
            return True
        if channel.name.lower() in ['rules', 'community-updates']:
            return True
    return False

async def is_ratelimited(exception):
    if isinstance(exception, HTTPException) and exception.status == 429:
        return True
    return False

async def delete_channel(channel):
    try:
        await channel.delete()
        return True
    except Exception as e:
        if await is_ratelimited(e):
            return 'ratelimited'
        print(f"無法刪除頻道 {channel.name}: {str(e)}")
        return False

async def delete_role(role):
    try:
        await role.delete()
        return True
    except Exception as e:
        if await is_ratelimited(e):
            return 'ratelimited'
        print(f"無法刪除身分組 {role.name}: {str(e)}")
        return False

async def delete_existing_content(guild, interaction):
    
    while True:
        channels_to_delete = [c for c in guild.channels if not isinstance(c, discord.CategoryChannel) and not is_community_channel(c)]
        roles_to_delete = [r for r in guild.roles if r != guild.default_role and not r.managed and r < guild.me.top_role]
        
        if not channels_to_delete and not roles_to_delete:
            break
        
        ratelimited = False
        
        for channel in channels_to_delete:
            result = await delete_channel(channel)
            if result == 'ratelimited':
                ratelimited = True
                break
        
        if not ratelimited:
            for role in roles_to_delete:
                result = await delete_role(role)
                if result == 'ratelimited':
                    ratelimited = True
                    break
        
        if ratelimited:
            await interaction.user.send("機器人暫時被限速，將在30秒後繼續。")
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(1)  # 短暫休息以避免過度頻繁的請求
    
    # 刪除空的分類
    for category in guild.categories:
        if len(category.channels) == 0:
            try:
                await category.delete()
            except Exception as e:
                print(f"無法刪除分類 {category.name}: {str(e)}")

async def restore_channels(guild, folder_path):
    with open(f"{folder_path}/channels.json", "r", encoding="utf-8") as f:
        channels_data = json.load(f)

    for category_data in channels_data:
        try:
            category = await guild.create_category(category_data["name"])
            for channel_data in category_data["channels"]:
                if channel_data["type"] == "text":
                    await category.create_text_channel(channel_data["name"])
                elif channel_data["type"] == "voice":
                    await category.create_voice_channel(channel_data["name"])
        except Exception as e:
            print(f"無法還原分類或頻道: {str(e)}")

async def restore_roles(guild, folder_path):
    with open(f"{folder_path}/roles.json", "r", encoding="utf-8") as f:
        roles_data = json.load(f)

    for role_data in reversed(roles_data):
        try:
            await guild.create_role(
                name=role_data["name"],
                color=discord.Color(role_data["color"]),
                permissions=discord.Permissions(role_data["permissions"])
            )
        except Exception as e:
            print(f"無法還原身分組 {role_data['name']}: {str(e)}")

async def restore_settings(guild, folder_path):
    with open(f"{folder_path}/settings.json", "r", encoding="utf-8") as f:
        settings_data = json.load(f)

    try:
        await guild.edit(name=settings_data["server_name"])
    except Exception as e:
        print(f"無法還原伺服器設定: {str(e)}")

async def restore_icon(guild, folder_path):
    icon_path = f"{folder_path}/icon.png"
    if os.path.exists(icon_path):
        try:
            with open(icon_path, "rb") as f:
                icon = f.read()
            await guild.edit(icon=icon)
        except Exception as e:
            print(f"無法還原伺服器圖標: {str(e)}")

async def load_backup(interaction: Interaction, backup_id: str):
    folder_path = f"save/{backup_id}"
    if not os.path.exists(folder_path):
        await interaction.user.send("無效的備份 ID。請檢查並重試。")
        return

    guild = interaction.guild
    progress_embed = Embed(title="還原進度", description="[⌛] 進行中 | [✅] 已完成", color=0x5a5fcf)
    progress_message = await interaction.user.send(embed=progress_embed)

    steps = ["刪除現有內容", "還原分類和頻道", "還原身分組", "還原伺服器設定", "還原伺服器圖標"]
    for i, step in enumerate(steps):
        progress_embed.add_field(name=step, value="⌛", inline=False)
        await progress_message.edit(embed=progress_embed)

        try:
            if step == "刪除現有內容":
                await delete_existing_content(guild, interaction)
            elif step == "還原分類和頻道":
                await restore_channels(guild, folder_path)
            elif step == "還原身分組":
                await restore_roles(guild, folder_path)
            elif step == "還原伺服器設定":
                await restore_settings(guild, folder_path)
            elif step == "還原伺服器圖標":
                await restore_icon(guild, folder_path)

        except Exception as e:
            error_message = f"在 {step} 步驟中發生錯誤: {str(e)}\n"
            error_message += f"錯誤類型: {type(e).__name__}\n"
            error_message += f"錯誤詳情: {str(e)}"
            await interaction.user.send(error_message)
            print(error_message)  # 在控制台也輸出錯誤信息
            continue

        progress_embed.set_field_at(i, name=step, value="✅", inline=False)
        await progress_message.edit(embed=progress_embed)

    try:
        await guild.edit(name=f"[還原完成] {guild.name}")
    except Exception as e:
        await interaction.user.send(f"無法更改伺服器名稱: {str(e)}")

    await interaction.user.send(f"伺服器 {guild.name} (ID: {guild.id}) 的備份已還原完成。")

@tree.command(name="讀取", description="讀取伺服器備份")
async def load(interaction: Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("只有伺服器擁有者可以使用此命令。", ephemeral=True)
        return

    embed = Embed(title="讀取伺服器備份", description="你確定要讀取伺服器備份嗎？這將會刪除大部分現有的頻道、分類和身分組。", color=0x5a5fcf)
    view = ConfirmView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)





client.run("機器人Token貼這裡")
