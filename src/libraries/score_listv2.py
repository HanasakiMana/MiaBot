import asyncio
import aiohttp
import math

from src.libraries.CONST import developer_token
from src.libraries.image_process import text_to_image
# from CONST import developer_token
# from image_process import text_to_image


# 一个用于获取用户名的函数
async def get_username(qq: str):
    async with aiohttp.ClientSession() as session:
            async with session.post(url="https://www.diving-fish.com/api/maimaidxprober/query/player", json={"qq": qq}) as resp:
                if resp.status == 400:
                    return None, 400
                if resp.status == 403:
                    return None, 403
                data = await resp.content.read()
                data = eval(str(data.decode('unicode_escape')).replace('null', 'None'))
                return data.get('username'), 200


class generateScoreList(object):
    def __init__(self, page: int, qq: str = None, username: str = None, level: str = None, ds: float = None):
        self.qq = qq
        self.username = username
        self.page = page
        self.level = level
        self.ds = ds

    
    async def getScoreList(self):
        username = ''
        if self.username is None:
            username, status = await get_username(self.qq)
            if status != 200:
                return None, 400
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"https://www.diving-fish.com/api/maimaidxprober/dev/player/records?username={username}", headers={"developer-token": developer_token})as resp:
                data = None
                if resp.status == 200:
                    data = await resp.content.read()
                    data = eval(str(data.decode()).replace('null', 'None'))
                
                filtered_records = []
                if self.level: 
                    for music_dict in data.get('records'):
                        if music_dict.get('level') == self.level:
                            filtered_records.append(music_dict)
                elif self.ds:
                    for music_dict in data.get('records'):
                        if music_dict.get('ds') == self.ds:
                            filtered_records.append(music_dict)

                filtered_records = sorted(filtered_records, key=lambda level: level.get('achievements'), reverse=True)
                return filtered_records[(self.page - 1)*40:min(self.page*40, len(filtered_records)-1)], len(filtered_records)
    

    async def generate(self):
        data = await self.getScoreList()
        scoreList, recordLength = data[0], data[1]
        output_text = ''
        for score in scoreList:
            achievement = str(format(score.get('achievements'), '.4f')) + '%'
            chartId = score.get('song_id')
            title = score.get('title')
            diff = score.get('level_label')
            output_text += f"{achievement}  {chartId}. {title} ({diff})\n"
        output_text += f"第{self.page}页，共{math.ceil(recordLength / 40)}页（每页最多展示40条）"
        return text_to_image(output_text, 10, (0, 0, 0), max_length=10000)



if __name__ == '__main__':
    asyncio.run(generateScoreList(1, 1179782321, level='12+').generate()).show()