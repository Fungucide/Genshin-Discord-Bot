import time
from typing import List, Dict

from discord.ext import commands
from discord.ext.commands import command

import util

# Fungucide#7029 -> 227541695225397250
admins = [227541695225397250]
# Genshin Bot Home -> 844307839488622662
control_server = [844307839488622662]


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id in admins and ctx.guild.id in control_server

    @command(name='serverid')
    async def server_id(self, ctx):
        await ctx.send(f'Guild ID: {ctx.guild.id}')

    @command(name='makeemojitable')
    async def make_emoji_table(self, ctx):
        util.db.make_emoji_table()
        await ctx.send('Created emoji table')

    @command(name='getemojis')
    async def get_emojis(self, ctx, *args: List[str]):
        added = []
        added.extend(util.get_character_emojis(True))
        await ctx.send(f'Obtained {len(added)} emojis:\n' + ', '.join(added))

    @command(name='addemojis')
    async def add_emojis(self, ctx, *args):
        reload = args and len(args) >= 1 and args[0] in ['-reload', '-r']
        if reload:
            args = args[1:]
        if not args:
            args = ['-category', 'character']
        added = 0
        await ctx.send("Starting Upload")
        if args[0] in ['-category', '-c']:
            args = args[1:]
            await self.add_emojis_category(ctx, args, reload)
        else:
            for item in args:
                emoji_info = util.db.get_emoji(item)
                await self._add_emoji(ctx, emoji_info, emoji_info['category'], reload)
                added += 1

        await ctx.send(f'Created {added} emojis.')

    async def _add_emoji(self, ctx, entry: Dict[str, str], category: str, reload: bool):
        time.sleep(10)
        if reload:
            file_name = util.download_images(entry['url'], entry['name'], category)
        else:
            file_name = f'{category}/{entry["name"]}.png'
        image = open(file_name, 'rb')
        emoji = await ctx.guild.create_custom_emoji(image=image.read(),
                                                    name=entry['name'].replace(' ', '').replace('-', ''))
        util.db.set_emoji_discord_id(entry['name'], f'<:{emoji.name}:{emoji.id}>')
        await ctx.send(f'{entry["name"]}: <:{emoji.name}:{emoji.id}>')

    async def add_emojis_category(self, ctx, categories: List[str], reload: bool):
        added = 0
        for category in categories:
            entries = util.db.get_category_emoji(category)
            for entry in entries:
                self._add_emoji(ctx, entry, category, reload)
                added += 1
        return added

    @command(name='clearemojis')
    async def clear_emoji(self, ctx):
        emojis = await ctx.guild.fetch_emojis()
        count = 0;
        for emoji in emojis:
            time.sleep(10)
            await emoji.delete()
            count += 1
        await ctx.send(f'Deleted {count} emojis.')

    @command(name='testaddemoji')
    async def test_add_emoji(self, ctx):
        image = open('emojis/amber.png', 'rb')
        await ctx.guild.create_custom_emoji(image=image.read(), name="amber")
