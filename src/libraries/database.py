# 包含与数据库相关的操作

import sqlite3
import os
import requests
import datetime, pytz
# 数据库文件夹所在的路径
dbFolderPath = 'src/database'
# sql文件的路径
sqlFilePath = 'src/libraries/sql_conf'
# 难度索引
diffList = ['basic', 'advanced', 'expert', 'master', 'reMaster']



class DBInit(object):
    def __init__(self, rebuild: bool = False) -> None: # rebuild参数会强制删除已存在的数据库并重建
        currentPath = os.getcwd()
        # 搜集sql文件
        os.chdir(sqlFilePath)
        sqlFileList = os.listdir()
        # 切换回工作目录
        os.chdir(currentPath)
        for sqlFile in sqlFileList:
            fileName = sqlFile.split('.')[0]
            # 在如果无法新建，就是因为对应文件
            dbPath = f'{dbFolderPath}/{fileName}.sqlite'
            # 判断数据库文件是否已经生成
            if os.path.exists(dbPath):
                if rebuild:
                    os.remove(dbPath)
                else:
                    print(f'Existed database {fileName}.sqlite')
                try:
                    self.createDB(sqlFilePath + '/' + sqlFile, fileName, dbFolderPath)
                except:
                    pass


    def createDB(self, sqlPath, dbName, dbFolderPath):
        # 读取sql文件的指令
        sql = open(sqlPath, 'r')
        sqlCmd = sql.readlines()
        sql.close()
        sqlCmd = "".join(sqlCmd)

        # 创建数据库
        conn = sqlite3.connect(dbFolderPath + '/' + dbName + '.sqlite')
        cur = conn.cursor()
        cur.executescript(sqlCmd)
        conn.commit()
        conn.close()


# maimai相关数据库的读写操作
class maimaiDB(object):
    def __init__(self, dbPath: str = 'src/database/SDGB.sqlite'):
        # 默认操作的是来自水鱼的数据库
        self.dbPath = dbPath


    def getDataFromDivingFish(self):
        # 获取谱面的基本信息
        rawData = requests.get('https://www.diving-fish.com/api/maimaidxprober/music_data').json()
        
        # 将数据格式化成上面函数可以接受的形式
        musicData = {} # 歌曲基本信息
        chartData = [] # 谱面信息
        chartTypeData = {} # 谱面种类信息（格式：[std谱面id，dx谱面id]）

        for singleData in rawData:
            chartid: str = singleData.get('id')
            # 一般来说谱面id和歌曲id是一致的，最多四位数，dx谱则是五位数，需要做下转换
            musicId = chartid
            if len(chartid) == 5:
                musicId = str(int(chartid[1:]))
            basicInfo = singleData.get('basic_info')
            title = basicInfo.get('title')
            artist = basicInfo.get('artist')
            genre = basicInfo.get('genre')
            bpm = basicInfo.get('bpm')
            isNew = basicInfo.get('is_new')
            # 数据库不认boolean，要转换成整数
            if isNew:
                isNew: int = 1
            else:
                isNew: int = 0
            addVersion = basicInfo.get('from')

            chartType = singleData.get('type')
            ds = singleData.get('ds')
            levels = singleData.get('level')
            
            charts = singleData.get('charts')
            
            # 遍历每一个难度的谱面
            for i in range(len(charts)):
                diff = diffList[i]
                notes = charts[i].get('notes')
                charter = charts[i].get('charter')
                singleLevel = levels[i]
                singleDs = ds[i]
                tap = notes[0]
                hold = notes[1]
                slide = notes[2]
                touch, bReak = 'NULL', 'NULL'
                # 判断有没有touch
                if len(notes) == 5:
                    touch = notes[3]
                    bReak = notes[4]
                else:
                    bReak = notes[3]
                
                chartInfo = [chartid, chartType, musicId, diff]
                for i in [singleLevel, singleDs, charter, tap, hold, slide, touch, bReak]:
                    chartInfo.append(i)
                chartData.append(chartInfo)
            
            # 更新歌曲信息
            musicData.update({musicId: [title, artist, genre, bpm, addVersion, isNew]})
            # 更新谱面类型信息
            if chartTypeData.get(musicId) == None:
                if chartType == 'SD':
                    chartTypeData.update({musicId: [chartid, 'NULL']})
                if chartType == 'DX':
                    chartTypeData.update({musicId: ['NULL', chartid]})
            else:
                original = chartTypeData.get(musicId)
                if chartType == 'SD':
                    chartTypeData.update({musicId: [chartid, original[1]]})
                if chartType == 'DX':
                    chartTypeData.update({musicId: [original[0], chartid]})
        
        # 合并歌曲信息和谱面类型
        for musicId, chartType in chartTypeData.items():
            musicInfo = musicData.get(musicId)
            musicData.update({musicId: musicInfo + chartType})
        
        return musicData, chartData
        
    # 更新数据库中存储的数据
    def update(self, musicData: dict = None, chartData: dict = None):
        # 获取歌曲和谱面信息
        musicData, chartData = self.getDataFromDivingFish()
        
        cmdList = [] # 需要执行的命令列表
        
        # 一个用来拼接出sql命令的小函数
        def joinCmd(id, info, targetTable):
            if id != None:
                data = f"\'{id}\'"
            else:
                data = ''
            for i in info:
                # 给str套单引号，不然sql不认为是TEXT类型
                if isinstance(i, str):
                    # 如果曲名中出现了单引号，就需要把单引号打两遍，第一个相当于转义符
                    i = i.replace('\'', r"''")
                    # 套引号
                    i = f"\'{i}\'"
                data += f', {i}'
            if id == None:
                data = data[1:]
            return f'INSERT INTO {targetTable} VALUES({data})'

        # musicInfo
        for musicId, musicInfo in musicData.items():
            cmdList.append(joinCmd(musicId, musicInfo, 'musicInfo'))

        # chartInfo
        for data in chartData:
            cmdList.append(joinCmd(None, data, 'chartInfo'))
        # dbInfo
        updateTime = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        cmdList.append(f"INSERT INTO dbInfo VALUES('{updateTime}')")
        # 执行命令
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 清空表
        cur.execute('DELETE FROM musicInfo')
        cur.execute('DELETE FROM chartInfo')
        cur.execute('DELETE FROM dbInfo')
        for cmd in cmdList:
            cur.execute(cmd)
            conn.commit()
        conn.close()
    

    # 对歌曲数据库进行搜索（支持同时检索两个元素，比如谱面id+谱面难度，歌曲id+歌曲类型等）
    def search(self, type: str, keyword: str, type2: str = None, keyword2: str = None, dbType: str = 'SDGB'):
        dbPath = f'{dbFolderPath}/{dbType}.sqlite'
        # 歌曲可供调用的搜索类型（这些都是数据库中已有的column）
        musicType = ['musicId', 'title', 'artist', 'genre', 'addVersion', 'isNew']
        # 谱面可供调用的搜索类型（这些都是数据库中已有的column）
        chartType = ['chartId', 'chartType', 'diff', \
            'tapCount', 'holdCount', 'slideCount', 'touchCount', 'breakCount'
        ]
        # 额外的谱面搜索关键字（数据库中没有对应column，需要额外代码支撑）
        chartTypeExtended = ['Level', 'Ds', 'Charter']
        conn = sqlite3.connect(dbPath)
        cur = conn.cursor()
        cmd = ''
        if type in musicType:
            cmd = f'SELECT * FROM musicInfo WHERE {type} LIKE \'%{keyword}%\''
            if type2 in musicType:
                cmd += f' AND {type2} LIKE \'%{keyword2}%\''
        elif type in chartType:
            cmd = f'SELECT * FROM chartInfo WHERE {type} LIKE \'%{keyword}%\''
            if type2 in chartType:
                cmd += f' AND {type2} LIKE \'%{keyword2}%\''
        # 定义一个用于返回数据的变量
        searchResult = []
        result = cur.execute(cmd)
        for row in result:
            searchResult.append(row)
        print(searchResult)
        
        

        
if __name__ == '__main__':
    # DBInit(rebuild=True)
    # maimaiDB().update()
    maimaiDB().search('chartId', '11173', 'diff', 'master')