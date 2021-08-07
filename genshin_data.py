from functools import cmp_to_key
from typing import List

import genshinstats as gs

class GenshinData:
    # TODO: Cache data and implement rate limiting
    # TODO: Do something to get profile icon?

    DEFAULT_AVATAR = 'https://img-os-static.hoyolab.com/avatar/avatar1.png'

    def __init__(self, uid: int, token: str):
        gs.set_cookie(ltuid=uid, ltoken=token)
        try:
            gs.get_record_card(46178811)
        except gs.errors.GenshinStatsException:
            raise Exception("Login Failed: Bad credentials given")

    def search(self, name: str):
        results = gs.search(name)
        return results

    def get_record_card(self, uid: int):
        record_card = gs.get_record_card(uid)
        # Make sure we actually get valid results
        if not record_card or 'game_role_id' not in record_card:
            return None
        return record_card

    def get_info(self, uid: int):
        record_card = self.get_record_card(uid)
        if not record_card:
            return None
        genshin_uid = record_card['game_role_id']
        genshin_info = gs.get_user_stats(genshin_uid)
        if not genshin_info:
            return None

        full_data = {}
        # Copy certain values from the record card
        full_data['uid'] = genshin_uid
        full_data['nickname'] = record_card['nickname']
        full_data['adventure_rank'] = record_card['level']
        full_data['region'] = record_card['region_name']

        # Sort character data
        def cmp(x, y):
            if x['rarity'] != y['rarity']:
                return x['rarity'] - y['rarity']
            if x['level'] != y['level']:
                return x['level'] - y['level']
            if x['friendship'] != y['friendship']:
                return x['friendship'] - y['friendship']
            return 1 if x['name'] > y['name'] else (0 if x['name'] == y['name'] else -1)

        genshin_info['characters'] = sorted(genshin_info['characters'], key=cmp_to_key(cmp), reverse=True)

        # Copy values from genshin info
        for value in ['stats', 'characters', 'explorations']:
            full_data[value] = genshin_info[value]

        return full_data

    def get_player_character(self, uid: int, names: List[str]):
        characters = gs.get_characters(uid)
        res = {}
        for character in characters:
            if character['name'] in names or character['alt_name'] in names:
                res[character['name']] = character
                if character['alt_name']:
                    res[character['alt_name']] = character
        return res
        
