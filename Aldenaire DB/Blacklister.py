import discord, datetime, pytz, asyncio
from json_admin import get_json, set_json
from discord.ext import commands
from discord import app_commands

CONFIG = {
    'BlackList File Name': 'list.json',
    'Bot Token': '',
    'WhiteList': []
}

BlackList = get_json(CONFIG["BlackList File Name"])

for i in range(len(CONFIG["WhiteList"])):
    if CONFIG["WhiteList"][i] in BlackList:
        del BlackList[CONFIG["WhiteList"][i]]

Intents = discord.Intents.default()
Intents.message_content = True
Intents.members = True
Intents.messages = True
Intents.bans = True

Bot = commands.Bot(command_prefix=':', intents=Intents)

@Bot.event
async def on_ready():
    try:
        synced = await Bot.tree.sync()
        print(f"Success Sync: Ordered {len(synced)}Commands")
    except Exception as e:
        print(f"Failed Sync: {e}")
    print(f"Intilizing Root Bot Server: {Bot.user}")

@Bot.tree.command(name="차단", description="연결된 엘덴에어 DB를 통해 확인된 인원을 차단합니다.")
@commands.bot_has_permissions(ban_members=True)
@app_commands.describe(모드="빠른 차단(서버 내 인원 기준)을 하거나 전체 차단(DB내 인원 기준)을 선택해주세요.")
@app_commands.choices(모드=[app_commands.Choice(name="빠른 차단", value=1), app_commands.Choice(name="전체 차단", value=0)])
async def blacklister(inter: discord.Interaction, 모드: int):
    await inter.response.defer()
    ban_count = 0
    if 모드 == True:
        guild_members = inter.guild.members
        for i in range(len(guild_members)):
            member = guild_members[i]
            if member.id in BlackList:
                try:
                    await member.ban(reason="엘덴에어DB 차단")
                    ban_count += 1
                except Exception as e:
                    print(e)
    else:
        temp = list(map(int, BlackList.keys()))
        for i in range(len(temp)):
            try:
                await inter.guild.ban(discord.Object(id=temp[i]), reason="엘덴에어DB 차단")
                ban_count += 1
            except Exception as e:
                print(e)
    
    embed = discord.Embed(title="차단 결과", timestamp=datetime.datetime.now(pytz.timezone('UTC')), color=0x10ff00)
    embed.add_field(name="차단 인원", value=str(ban_count))
    await inter.followup.send(embed=embed)
    return

Bot.run(token=CONFIG['Bot Token'])