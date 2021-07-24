import os

from dotenv import load_dotenv

from genshin_data import GenshinData

load_dotenv()
uid = int(os.getenv('GENSHIN_UID'))
token = os.getenv('GENSHIN_TOKEN')
data = GenshinData(uid, token)
print(data.get_info(46178811))
