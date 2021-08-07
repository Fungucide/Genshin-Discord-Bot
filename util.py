import os
from typing import List, Tuple

import requests
from PIL import Image
from dotenv import load_dotenv

from database import Database

load_dotenv()
ENDPOINT = os.getenv('GENSHIN_DEV_ENDPOINT')
ELEMENT_ENDPOINT = os.getenv('GENSHIN_DEV_ELEMENTS')
db_file = os.getenv('DATABASE_FILE')

if not ENDPOINT:
    raise Exception("Expected endpoint variable to be not None")
if not db_file:
    raise Exception("Expected db_file variable to be not None")

db = Database(db_file)


def get_character_list():
    res = requests.get(ENDPOINT + '/characters')
    if 200 < res.status_code or res.status_code >= 300:
        raise Exception(f"Request for character list returned with response code:{res.status_code}\n{res.text}")
        return None
    characters = res.json()
    characters[characters.index('traveler-anemo')] = 'traveler'
    return characters


def get_element_icon(element: str):
    return ENDPOINT + ELEMENT_ENDPOINT + element + '/icon'


def get_character_emojis(overwrite: bool = False) -> List[str]:
    character_list = get_character_list()
    added = []
    if character_list:
        for character in character_list:
            url = f'{ENDPOINT}/characters/{character}/icon'
            if db.add_emoji(character, 'character', url, overwrite):
                added.append(character)
    return added


def get_image(url: str, name: str):
    request = requests.get(url)
    open(name, 'wb').write(request.content)


def convert_img(path: str, name: str):
    im = Image.open(path).convert('RGBA')
    im.save(f'{name}.png', 'png')
    return f'{name}.png'


def download_images(url: str, name: str, category: str):
    if category:
        dest_name = f'{category}/raw/{name}'
        dest_final = f'{category}/{name}'
        dest_folder = f'{category}/raw'
    else:
        dest_name = f'raw/{name}'
        dest_final = {name}
        dest_folder = f'raw'
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    get_image(url, dest_name)
    return convert_img(dest_name, dest_final)

"""
amts_per_level: a list containing tuples, each in form (rarity, amount)
requires: rarities in amts_per_level are in non-decreasing order
returns: a list containing tuples, each in form (rarity, amount)
"""
def calculate_required_materials(current_level: int, desired_level: int, 
    amts_per_level: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    
    ret = []

    for i in range(current_level + 1, desired_level + 1):
        level_rarity = amts_per_level[i][0]
        level_amt = amts_per_level[i][1]

        if len(ret) == 0 or level_rarity != ret[-1][0]:
            ret.append((level_rarity, 0))

        ret[-1] = (ret[-1][0], ret[-1][1] + level_amt)

    return ret
