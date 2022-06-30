# 这个文件包含了歌曲和谱面存储在本地数据的读取、更新、查找、分类功能

# 备注：难度、谱面颜色与内部id的转换
# Basic Advanced Expert Master Re:Master
# 绿    黄        红     紫     白
# 1     2        3      4      5


import json
import asyncio
import datetime, pytz
import requests
import re
import fnmatch
import shelve


# 用于数据处理的变量和函数
class musicData:
    update_time = ''
    music_data = []
    charts_data = {}
    music_dict = {} # 以id为索引建立歌曲信息的字典

    # 以各个歌曲信息为索引建立用于反向检索字典，降低时间复杂度
    name_id = {}  # '标题': [id]
    level_id = {} # '等级1': [[id1, diff1], [id2, diff2], …]
    ds_id = {} # '定数1': [[id1, diff1], [id2, diff2], …]
    artist_id = {} # '曲师': [id1, id2, …]
    charter_id = {} # '谱师': [[id1, diff1], [id2, diff2], …]
    bpm_id = {} # 'bpm': [id1, id2, …]
    


    def __init__(self):
        self.update_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        # 从水鱼的网站爬取相关数据
        self.music_data = requests.get('https://www.diving-fish.com/api/maimaidxprober/music_data').json()
        self.charts_data = requests.get('https://www.diving-fish.com/api/maimaidxprober/chart_stats').json()
        self.format()

    
    # 解析水鱼的json，并对数据进行格式化
    def format(self, music_data = None): # 可以在后期填入hdd中获取的json
        # 清空缓存的数据
        self.music_dict = {}
        self.name_id = {} 
        self.level_id = {}
        self.ds_id = {}
        self.artist_id = {}
        self.charter_id = {}
        self.bpm_id = {}
        
        if music_data is None:
            music_data = self.music_data
        if len(music_data) != 0:
            # 解析json中的数据
            for dic in music_data:
                id = dic.get('id')  # type: ignore
                name = dic.get('title')  # type: ignore
                levels = dic.get('level')  # type: ignore
                ds = dic.get('ds')
                
                charts = []
                charters = []
                for chart_dict in dic.get('charts'):  # type: ignore
                    charters.append(chart_dict.get('charter'))
                    charts.append(chart_dict.get('notes'))
                
                basic_info = dic.get('basic_info')  # type: ignore
                artist = basic_info.get('artist')
                genre = basic_info.get('genre')
                bpm = basic_info.get('bpm')
                add_version = basic_info.get('from')
                
                # 将各种数据update进字典
                self.music_dict.update({
                    id: {
                        'id': id,
                        'name': name,
                        'level': levels, # ['level1', 'level2', …]
                        'ds': ds,
                        'charts': charts, # [[tap1, hold1, slide1, touch1, break1], …]
                        'charters': charters, # ['charter1', 'charter2', …]
                        'artist': artist,
                        'genre': genre,
                        'bpm': bpm,
                        'add_version': add_version
                    }
                })
            
                # update反向检索的字典
                self.format_reverse(name, id, self.name_id) # 曲名
                for i in range(0, len(levels)): 
                    self.format_reverse(levels[i], [id, i + 1], self.level_id)
                    self.format_reverse(ds[i], [id, i + 1], self.ds_id)
                    if i >= 2: # 黄谱和绿谱没有记录谱师，直接略过
                        self.format_reverse(charters[i], [id, i + 1], self.charter_id)
                self.format_reverse(artist, id, self.artist_id)
                self.format_reverse(bpm, id, self.bpm_id)
 

    # 构建反向检索字典
    def format_reverse(self, data, id, target_dict: dict):
        if target_dict.get(data) == None: # 目标字典第一次加入这个key，可以直接加入
            target_dict.update({data: [id]})
        else: # 目标字典里面有想要加入的key，说明这个key对应多个乐曲id
            ids = list(target_dict.get(data))
            ids.append(id)
            target_dict.update({data: ids})

    
    # 以各种方式检索乐曲的id
    def search_id(self, data, type: str): # data是传入的key，type是对应的信息种类
        result_list = []
        if type == 'name': # 以歌曲名称查找id
            for name in self.name_id.keys(): # 遍历所有歌曲名称
                result = re.match(data, name, flags=re.I)
                if result is not None:
                    result_list.append(self.name_id.get(name))
        elif type == 'level': # 以等级查找id
            if self.level_id.get(data):
                result_list.append(self.level_id.get(data))
        elif type == 'ds': # 定数
            if self.ds_id.get(data):
                result_list.append(self.ds_id.get(data))
        elif type == 'charter': # 谱师
            if self.charter_id.get(data):
                result_list.append(self.charter_id.get(data))
        elif type == 'artist': # 曲师
            if self.artist_id.get(data):
                result_list.append(self.artist_id.get(data))
        elif type == 'bpm': # bpm
            if self.bpm_id.get(data):
                result_list.append(self.bpm_id.get(data))
        return result_list


    # 获取歌曲信息
    def get_info(self, id: str, *type): # type是可变参数，便于直接获取一个或几个歌曲信息
        result = {}
        info = self.music_dict.get(id)
        if info is not None:
            if type:
                for i in type:
                    try:
                        result.update({i: info.get(i)})
                    except:
                        pass
            else:
                result = info
        return result


# 更新本地保存的数据
def update_music_data():
    # 更新update时间
    musicData.update_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    
    # 从水鱼的网站爬取相关数据
    musicData.music_data = requests.get('https://www.diving-fish.com/api/maimaidxprober/music_data').json()
    musicData.charts_data = requests.get('https://www.diving-fish.com/api/maimaidxprober/chart_stats').json()

    # 重构内存中保存的值
    musicData().format()


if __name__ =='__main__':
    # update_music_data()
    print(musicData().name_id.get('トリドリ⇒モリモリ！Lovely fruits☆'))

