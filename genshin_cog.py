import os
from typing import List, Dict, Union

import discord
from discord.ext import commands
from discord.ext.commands import command
from dotenv import load_dotenv

import util
from genshin_data import GenshinData
from genshin_dev_data import GenshinDevData, InvalidCharacterException
from requests import RequestException

load_dotenv()
GENSHIN_UID = int(os.getenv('GENSHIN_UID'))
GENSHIN_TOKEN = os.getenv('GENSHIN_TOKEN')

genshin_data = GenshinData(GENSHIN_UID, GENSHIN_TOKEN)

separate_line = '----------------------------------------------'


class GenshinCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @command(name='stats', aliases=['s'], help='Fetches general stats about a player')
    async def stats_command(self, ctx, *args:str):
        uid, args = await _identify(ctx, args)
        info = await get_info(ctx, uid)
        if not info:
            return
        await ctx.send(embed=create_stats_embed(ctx, info))

    @command(name='characters', aliases=['character', 'c'],
             help='Fetches all the players characters or specific information about certain characters')
    async def characters_command(self, ctx, *args:str):
        uid, args = await _identify(ctx, args)
        if not uid:
            await ctx.send(f'No user found')
            return
        if len(args) == 0:
            info = await get_info(ctx, uid)
            if not info:
                return
            await ctx.send(embed=create_characters_embed(ctx, info))
        else:
            record_card = await get_record_card(ctx, uid)
            if not record_card:
                return
            nick = record_card['nickname']
            uid = record_card['game_role_id']
            characters = genshin_data.get_player_character(uid, args)
            for character in args:
                if character.title() in characters:
                    for embed in create_player_character_embeds(ctx, nick, characters[character]):
                        await ctx.send(embed=embed)

    @command(name='search', aliases=['uid'], help='Searches for a player based on their community UID')
    async def search_command(self, ctx, name: str):
        result = genshin_data.search(name)
        if result:
            for user in result:
                embed = create_profile_card(ctx,user)
                await ctx.send(embed=embed)

    @command(name='talents', aliases=['t'], help='Gets talent info associated with a character')
    async def talents_command(self, ctx, character: str):
        character = character.lower()

        talent_materials = None
        try:
            talent_materials = GenshinDevData.get_character_talent_materials(character)
        except InvalidCharacterException:
            await ctx.send(content=f'Unable to get complete talent info for character {character.capitalize()}')
            return
        except RequestException as e:
            await ctx.send(content=f'Error requesting talent data for character {character.capitalize()}: {str(e)}')
            return

        await ctx.send(embed = create_talents_embed(ctx, character, talent_materials))

    @command(name='abyss', aliases=['a'], help='Gets current spiral abyss information for a player')
    async def abyss_command(self, ctx, *args: str):
        uid, args = await _identify(ctx, args)

        if not uid:
            await ctx.send(f'No user found')
            return

        info = await get_info(ctx, uid)
        if not info:
            return

        await ctx.send(embed=create_spiral_abyss_embed(ctx, info['uid'], info['nickname']))


def create_profile_card(ctx, info: Dict[str, any]):
    embed = discord.Embed(title=f'{info["nickname"]}\'s Mihoyo Lab Profile')
    if info["introduce"]:
        embed.add_field(name="Introduction", value=info["introduce"], inline=False)
    embed.add_field(name="Link", value=f'https://www.hoyolab.com/genshin/accountCenter/postList?id={info["uid"]}', inline=False)
    field_helper(['UID'], True, embed, info)
    embed.set_thumbnail(url=info["avatar_url"])
    return embed


async def _identify(ctx, args: list):
    if args[0] in '-uid':
        uid = int(args[1])
        args = args[2:]
    elif args[0].isdigit():
        uid = int(args[0])
        args = args[1:]
    else:
        res = genshin_data.search(args[0])
        if not res:
            return None, None
        if len(res) > 1:
            await ctx.send(
                f'Found {len(res)} users matching name {args[0]}\n '
                f'Results will use the first result.\n'
                f'To see all results type `!search {args[0]}`')
        uid = int(res[0]['uid'])
        args = args[1:]
    # Maybe do something to verify uid :)
    return uid, args


async def get_info(ctx, uid: int):
    if not uid:
        await ctx.send(f'No user found')
    info = genshin_data.get_info(uid)
    if not info:
        await ctx.send(f'No user found with community uid {uid}.\nProfile could be private.')
    return info


async def get_record_card(ctx, uid: int):
    if not uid:
        await ctx.send(f'No user Found')
    record_card = genshin_data.get_record_card(uid)
    if not record_card:
        await ctx.send(f'No user found with community uid {uid}.\nProfile could be private.')
    return record_card


def field_helper(names: Union[List[str], str], inline: bool, embed: discord.Embed, source: Dict[str, any]):
    if isinstance(names, str):
        names = [names]
    for name in names:
        embed.add_field(name=name, value=f'{source[name.lower().replace(" ", "_")]}', inline=inline)


def field_footer(ctx, embed: discord.Embed):
    embed.set_footer(text=f'Requested by {ctx.author.display_name}')

def get_emoji(character: str):
    emoji = util.db.get_emoji(character)
    if emoji:
        emoji = emoji["discord_id"]
    else:
        emoji = ''

    return emoji

def create_stats_embed(ctx, info: Dict[str, any]):
    stats_embed = discord.Embed(title=f'{info["nickname"]}\'s Stats')
    field_helper(['Nickname', 'Adventure Rank'], True, stats_embed, info)
    field_helper('Region', False, stats_embed, info)
    field_helper(['Achievements', 'Active Days'], True, stats_embed, info['stats'])
    field_footer(ctx, stats_embed)
    return stats_embed


def create_characters_embed(ctx, info: Dict[str, any]):
    # Pray this never goes over the character limit
    character_embed = discord.Embed(title=f'{info["nickname"]}\'s Characters')
    characters = info['characters']
    for character in characters:
        emoji = get_emoji(character['name'].lower())
        value = ':star:' * character['rarity'] \
                + '\n' + f'**Level**: {character["level"]}'.ljust(15) \
                + '\n' + f'**Friendship**: {character["friendship"]}'.rjust(16)
        character_embed.add_field(name=f'__{emoji}{character["name"]}__', value=value, inline=True)
    field_footer(ctx, character_embed)
    return character_embed

def create_weapon_embed(ctx, weapon: Dict[str, any]):
    weapon_embed = discord.Embed(title=f'__Weapon:__ {weapon["name"]}',
                                     description=f':star:' * weapon['rarity'] + '\n'
                                           + f'**Level:** {weapon["level"]}\n'
                                           + f'**Ascension:** {weapon["ascension"]}\n'
                                           + f'**Refinement:** {weapon["refinement"]}')
    weapon_embed.set_thumbnail(url=weapon['icon'])

    return weapon_embed

def create_artifacts_embeds(ctx, artifacts: List[Dict[str, any]], set_count: Dict[str, int], set_effect: Dict[str, str]):

    artifact_embeds = []

    artifact_title_embed = discord.Embed(title=f'__Artifacts__')
    artifact_embeds.append(artifact_title_embed)

    # individual artifacts
    for artifact in artifacts:
        set_name = artifact['set']['name']
        if set_name not in set_count:
            set_count[set_name] = 0
            set_effect[set_name] = artifact['set']['effects']
        set_count[set_name] += 1
        current_artifact_embed = discord.Embed(title=f'__{artifact["pos_name"].title()}:__ {artifact["name"]}',
                                         description=f':star:' * artifact['rarity'] + '\n'
                                               + f'**Set:** {set_name}\n'
                                               + f'**Level:** {artifact["level"]}')
        current_artifact_embed.set_thumbnail(url=artifact['icon'])
        artifact_embeds.append(current_artifact_embed)

    # artifact sets
    artifact_set_embed = discord.Embed(title=f'Artifact Set Bonus',
                                     description=f'**{separate_line}**')
    for set_name in set_count:
        for effect in set_effect[set_name]:
            if set_count[set_name] >= effect['pieces']:
                artifact_set_embed.add_field(name=f'__{effect["pieces"]}-Piece Set:__ {set_name}',
                                                 value=effect['effect'], inline=True)
    artifact_embeds.append(artifact_set_embed)

    return artifact_embeds
    

def create_character_embed(ctx, nick: str, character: Dict[str, any]):
    player_character_embed = discord.Embed(title=f'{nick}\'s {character["name"]}',
                                           description=':star:' * character['rarity'] + '\n'
                                                       + f'**Level**: {character["level"]}\n'
                                                       + f'**Friendship**: {character["friendship"]}\n'
                                                       + f'**Constellation**: {character["constellation"]}')
    player_character_embed.set_thumbnail(url=character['icon'])

    return player_character_embed

def create_player_character_embeds(ctx, nick: str, character: Dict[str, any]):
    
    embeds = []

    embeds.append(create_character_embed(ctx, nick, character))
    embeds.append(create_weapon_embed(ctx, character['weapon']))

    set_count = {}
    set_effect = {}

    embeds += create_artifacts_embeds(ctx, character['artifacts'], set_count, set_effect)

    field_footer(ctx, embeds[-1])

    return embeds

# Assumes that in consecutive level intervals, the rarities of the required materials are consecutive
def create_talents_embed(ctx, character: str, talent_materials: Dict[str, any]):
    level_amts = {
        'talent-book': [(0, 0), (2, 3), (3, 2), (3, 4), (3, 6), (3, 9), (4, 4), (4, 6), (4, 12), (4, 16)],
        'boss-material': [(0, 0)] * 6 + [(5, 1), (5, 1), (5, 2), (5, 2)],
        'common-ascension-material': [(0, 0), (1, 6), (2, 3), (2, 4), (2, 6), (2, 9), (3, 4), (3, 6), (3, 9), (3, 12)],
        'crown': [(0, 0)] * 9 + [(5, 1)],
    }

    level_intervals = [(1, 2), (2, 6), (6, 10)]

    talents_embed = discord.Embed(title=f'Required talent materials for {character.capitalize()}:')
    
    for material_type in ['talent-book', 'boss-material', 'common-ascension-material', 'crown']:
        material_type_header = material_type.replace('-', ' ').capitalize()
        talents_embed.add_field(name=f'{separate_line}\n{material_type_header}',
            value=f'**{separate_line}**', inline = False)

        material_rarities = talent_materials[material_type]

        rarity_idx = 0
        for level_interval in level_intervals:
            start_level = level_interval[0]
            end_level = level_interval[1]
            required_amts = util.calculate_required_materials(start_level - 1, end_level - 1, level_amts[material_type])

            for rarity, amt in required_amts:
                if amt != 0:
                    material_rarity = material_rarities[rarity_idx]
                    talents_embed.add_field(
                        name=f'__{material_rarity["name"]}__:',
                        value=f':star:' * rarity + '\n'
                                + f'**Amount:** {amt}\n'
                                + f'**Levels:** {start_level} - {end_level}\n',
                        inline=True,
                    )

                    rarity_idx += 1

    field_footer(ctx, talents_embed)

    return talents_embed

def create_spiral_abyss_embed(ctx, uid: int, player_name: str):
    abyss_data = genshin_data.get_spiral_abyss(uid)

    abyss_embed = discord.Embed(
        title=f'Spiral Abyss season {abyss_data["season"]} info for {player_name}' + 
        f'\n{separate_line}',
        description=f'**Start Time:** {abyss_data["season_start_time"]}\n' + 
        f'**End Time:** {abyss_data["season_end_time"]}\n',
    )

    stats_str = ''
    for stat, value in abyss_data['stats'].items():
        stat_name = stat.replace('_', ' ').capitalize()
        stats_str += f'**{stat_name}:** {value}'
        if 'star' in stat:
            stats_str += ':star:'
        stats_str += '\n'

    for rank, characters in abyss_data['character_ranks'].items():
        if len(characters) == 0:
            break

        rank_name = rank.replace('_', ' ').capitalize()
        emoji = get_emoji(characters[0]['name'].lower())
        
        stats_str += f'{emoji} **{rank_name}:** {characters[0]["value"]}\n'

    abyss_embed.add_field(
        name=f'{separate_line}\nStats\n{separate_line}',
        value=stats_str,
        inline=False,
    )

    for floor in abyss_data['floors']:
        floor_str = ''

        for chamber in floor['chambers']:
            floor_str += f'**Chamber {chamber["chamber"]}**: '

            first_half, second_half = chamber['battles']
            first_half_emojis = [get_emoji(char['name'].lower()) for char in first_half['characters']]
            second_half_emojis = [get_emoji(char['name'].lower()) for char in second_half['characters']]

            floor_str += ' '.join(first_half_emojis) + ' '
            floor_str += ':star:' * chamber['max_stars'] + ' '
            floor_str += ' '.join(second_half_emojis)

            floor_str += '\n'

        abyss_embed.add_field(
            name=f'{separate_line}\nFloor {floor["floor"]}\n{separate_line}',
            value=floor_str,
            inline=False,
        )

    return abyss_embed
