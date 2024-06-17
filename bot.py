import psutil
import discord
import os
import time
import json
from discord import app_commands, Interaction, Embed
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
    embed.add_field(name="", value="", inline=False)
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




client.run("機器人Token貼這裡")
