import datetime
from logging import ERROR
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from admin_cog import AdminCog
from genshin_cog import GenshinCog

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ERROR_CHANNEL_ID = int(os.getenv('DISCORD_BASE_ERROR_CHANNEL'))
bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='Genshin Impact'))
    print(f'{bot.user.name} has connected {datetime.datetime.now()}.')




@bot.event
async def on_command_error(ctx, error):
    error_channel = bot.get_channel(ERROR_CHANNEL_ID)
    await error_channel.send(error)



@bot.after_invoke
async def after_react(ctx: commands.Context):
    if not ctx.command_failed:
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    else:
        await ctx.message.add_reaction('\N{CROSS MARK}')


bot.add_cog(AdminCog(bot))
bot.add_cog(GenshinCog(bot))
bot.run(TOKEN)
