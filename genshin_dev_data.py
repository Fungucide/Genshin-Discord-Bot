"""
class used to get data from https://api.genshin.dev
"""

from typing import Dict

import requests

class InvalidCharacterException(Exception):
    pass

class GenshinDevData:
    GENSHIN_DEV_URL = 'https://api.genshin.dev'

    def send_request(session: requests.Session, method: str, endpoint: str) -> Dict[str, any]:
        resp = session.request(method, GenshinDevData.GENSHIN_DEV_URL + endpoint, timeout=20)

        if resp.status_code != 200:
            raise requests.RequestException(f'Bad response code {resp.status_code}. Response: {resp.text}')

        return resp.json()

    """
    returns: dict with keys:
    [
        'talent-book', 
        'boss-material',
        'common-ascension-material',
        'crown'
    ]
    Values are lists of dictionaries guaranteed to have KVPS:
    {
        'name': <material-name>,
        'rarity': <material-rarity>,
    }
    """
    def get_character_talent_materials(character: str):
        ret = dict()

        session = requests.session()

        # get book
        books = GenshinDevData.send_request(session, 'get', '/materials/talent-book')

        for book, info in books.items():
            if character in info['characters']:
                ret['talent-book'] = info['items']
                break

        # get boss material
        boss_materials = GenshinDevData.send_request(session, 'get', '/materials/talent-boss')
        for material, info in boss_materials.items():
            if character in info['characters']:
                ret['boss-material'] = [{
                    'name': info['name'],
                    'rarity': 5,
                }]
                break

        # get common ascension material
        common_materials = GenshinDevData.send_request(session, 'get', '/materials/common-ascension')
        for material, info in common_materials.items():
            if character in info['characters']:
                ret['common-ascension-material'] = info['items']
                break

        if not ('talent-book' in ret and 'boss-material' in ret and 'common-ascension-material' in ret):
            raise InvalidCharacterException

        ret['crown'] = [{
            'name': 'Crown of Insight',
            'rarity': 5,
        }]

        return ret