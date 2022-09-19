# 包含与数据库相关的操作

import sqlite3
import os
from xmlrpc.client import Boolean
import requests
import datetime, pytz
from PIL import Image

# from CONST import plate_path, frame_path, tmp_path
# from image_process import scale, text_to_image
from src.libraries.CONST import plate_path, frame_path, tmp_path
from src.libraries.image_process import scale, text_to_image
from src.libraries.misc import getFileList

# 数据库文件夹所在的路径
dbFolderPath = 'src/database'
# sql文件的路径
sqlFilePath = 'src/libraries/sql_conf'
# 难度索引
diffList = ['basic', 'advanced', 'expert', 'master', 'reMaster']


class DBInit(object):
    def __init__(self, rebuild: bool = False) -> None: # rebuild参数会强制删除已存在的数据库并重建
        self.rebuild = rebuild
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
                    print(f'Failed to create database {fileName}.sqlite')
        self.miaInit(currentPath)


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


    # 获取plateId和frameId的列表
    def getIdList(self, folderPath):
        currentPath = os.getcwd()
        os.chdir(folderPath)
        fileList = os.listdir()
        idList = []
        for file in fileList:
            idList.append(f"{file.split('.')[0].split('_')[-1]}")
        idList.sort()
        os.chdir(currentPath)
        return idList

    # 生成姓名框/背景板索引，可以把所有样式合并在一张图片上并标上id
    def getImageIndex(self, type: str):
        if type in ['Plate', 'Frame']:
            if type == 'Plate':
                idList = self.getIdList(plate_path)
                folderPath = plate_path
                saveFolder = f'{tmp_path}/plate'
            else:
                idList = self.getIdList(frame_path)
                folderPath = frame_path
                saveFolder = f'{tmp_path}/frame'
            # 获取图像的宽和高
            img = Image.open(f'{folderPath}/UI_{type}_{idList[0]}.png')
            scaleRate = 0.5
            for i in range(len(idList)): # 粘贴图片
                img = Image.open(f'{folderPath}/UI_{type}_{idList[i]}.png')
                img = img.resize(scale(img.size, scaleRate))
                idImg = text_to_image(idList[i], 40, (0, 0, 0))
                img.paste(idImg, (int(img.size[0]/2 - idImg.size[0]/2), int(img.size[1]/2 - idImg.size[1]/2)), mask=idImg)
                img.save(f'{saveFolder}/{idList[i]}.png')
    # 初始化姓名框和背景板的id列表（记录在mia_custom.sqlite下）
    def miaInit(self, currentPath, dbPath: str = f'{dbFolderPath}/mia_custom.sqlite'):
        os.chdir(currentPath)
        plateIdList = self.getIdList(currentPath + '/' + plate_path)
        frameIdList = self.getIdList(currentPath + '/' + frame_path)
        os.chdir(currentPath)
        cmdList = []
        for i in plateIdList:
            cmdList.append(f'INSERT INTO plateIdList VALUES(\'{i}\')')
        for i in frameIdList:
            cmdList.append(f'INSERT INTO frameIdList VALUES(\'{i}\')')
        conn = sqlite3.connect(dbPath)
        cur = conn.cursor()
        cur.execute('DELETE FROM plateIdList')
        cur.execute('DELETE FROM frameIdList')
        for cmd in cmdList:
            cur.execute(cmd)
            conn.commit()
        conn.close()
        # 生成姓名框和背景板的预览图
        if self.rebuild:
            self.getImageIndex('Frame')
            self.getImageIndex('Plate')


# maimai相关数据库的读写操作
class maimaiDB(object):
    def __init__(self, dbPath: str = 'src/database/SDGB.sqlite'):
        # 默认操作的是用水鱼的数据生成的数据库
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
                    if i != 'NULL':
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
    

    # 对歌曲数据库进行搜索（支持同时检索两个元素，比如谱面id+谱面难度，歌曲id+歌曲类型等，第二个元素不是必须的）
    def search(self, type: str, keyword: str, type2: str = None, keyword2: str = None, dbType: str = 'SDGB'):
        dbPath = f'{dbFolderPath}/{dbType}.sqlite'
        # 歌曲可供调用的搜索类型（这些都是数据库中已有的column）
        musicType = ['musicId', 'title', 'artist', 'genre', 'addVersion', 'isNew']
        # 谱面可供调用的搜索类型（这些都是数据库中已有的column）
        chartType = ['chartId', 'chartType', 'chartLevel', 'chartDs', 'diff', 'charter',\
            'tapCount', 'holdCount', 'slideCount', 'touchCount', 'breakCount'
        ]
        modeType = ['like', 'equal']

        # 进行数据库操作
        conn = sqlite3.connect(dbPath)
        cur = conn.cursor()
        cmd = ''
        if type in musicType:
            if type in ['title', 'artist']:
                cmd = f'SELECT * FROM musicInfo WHERE {type} LIKE \'%{keyword}%\''
            else:
                cmd = f'SELECT * FROM musicInfo WHERE {type} = \'{keyword}\''
            if type2 in musicType:
                if type2 in ['title', 'artist']:
                    cmd += f' AND {type2} LIKE \'%{keyword2}%\''
                else:
                    cmd += f' AND {type2} = \'{keyword2}\''
        elif type in chartType:
            if type == 'chartDs':
                cmd = f'SELECT * FROM chartInfo WHERE {type} = {keyword}'
            else:
                cmd = f'SELECT * FROM chartInfo WHERE {type} = \'{keyword}\''
            if type2 in chartType:
                if type == 'chartDs':
                    cmd += f' AND {type2} = {keyword2}'
                else:
                    cmd += f' AND {type2} = \'{keyword2}\''
        # 定义一个用于返回数据的变量
        searchResult = []
        result = cur.execute(cmd)
        for row in result:
            searchResult.append(row)
        conn.close()
        return searchResult
    

    # 获取数据的更新时间
    def getUpdateTime(self):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        result = cur.execute(f'SELECT * FROM dbInfo')
        for row in result:
            result = row
        return result[0]

    
    # 随机一首歌曲id
    def random(self):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        result = cur.execute(f'SELECT musicId FROM musicInfo ORDER BY RANDOM() LIMIT 1')
        for row in result:
            result = row
        return result[0]


class miaDB(object):

    def __init__(self, dbPath: str = f'{dbFolderPath}/mia_custom.sqlite') -> None:
        self.dbPath = dbPath
    

    # 获取默认设置
    def get_default(self) -> list:
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        result = cur.execute(f'SELECT * FROM b50Custom WHERE QQ = \'default\'')
        defaultResult = None
        for row in result:
            defaultResult = row[1:]
        conn.close()
        return defaultResult


    # 获取自定义信息（格式：(姓名框id, 背景板id)）
    def get_custom(self, QQ: str) -> list:
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 根据QQ号检索
        result = cur.execute(f'SELECT * FROM b50Custom WHERE QQ = \'{QQ}\'')
        searchResult = None
        for row in result:
            searchResult = row[1:]
        conn.close()
        # 获取默认Id以备用
        defaultPlateId, defaultFrameId = self.get_default()
        if searchResult:
            plateId = searchResult[0]
            frameId = searchResult[1]
            if plateId == None: # 将空数据替换成默认的
                plateId = defaultPlateId
            if frameId == None:
                frameId = defaultFrameId
            return [plateId, frameId]
        else:
            return [defaultPlateId, defaultFrameId]
        
    
    # 写入自定义信息
    def add_custom(self, QQ: str, idType: str, id: str) -> Boolean:
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 查询当前是否有对应QQ号的记录
        result = cur.execute(f'SELECT * FROM b50Custom WHERE QQ = \'{QQ}\'')
        qqSearchResult = None
        for row in result:
            qqSearchResult = row
        if idType in ['plateId', 'frameId']:
            # 先判断id是否存在
            result = cur.execute(f'SELECT * FROM {idType}List WHERE {idType} = \'{id}\'')
            searchResult = None
            for row in result:
                searchResult = row
            if searchResult: # id存在的情况
                if qqSearchResult: # 查询到已有记录的情况
                    cur.execute(f'UPDATE b50Custom SET {idType} = \'{id}\' WHERE QQ = \'{QQ}\'')
                else: # 未查询到已有记录的情况
                    plateId, frameId = "NULL", "NULL"
                    if idType == 'frameId':
                        frameId = id
                    elif idType == 'plateId':
                        plateId = id
                    cur.execute(f"INSERT INTO b50Custom VALUES('{QQ}', {plateId}, {frameId})")
                conn.commit()
                conn.close()
                return True
            else: # id不合法的情况
                conn.commit()
                conn.close()
                return False
        else:
            conn.commit()
            conn.close()
            return False

    
    # poke相关功能
    def addPokeCount(self, QQ:str):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 查询当前是否有对应QQ号的记录
        result = cur.execute(f'SELECT * FROM b50Custom WHERE QQ = \'{QQ}\'')
        qqSearchResult = None
        for row in result:
            qqSearchResult = row
        if qqSearchResult:
            currentPokeCount = qqSearchResult[-1]
            cur.execute(f'UPDATE poke SET pokeCount = {currentPokeCount + 1} WHERE QQ = \'{QQ}\'')
        else:
            cur.execute(f"INSERT INTO poke VALUES('{QQ}', 1)")
        conn.commit()
        conn.close()

    def readPokeCount(self):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 查询当前是否有对应QQ号的记录
        result = cur.execute(f'SELECT * FROM b50Custom')
        searchResult = None
        for row in result:
            searchResult = row
    

    # 获取抽签结果
    def getOmikujiResult(self, QQ: str):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        # 查询当前是否有对应QQ号的记录
        result = cur.execute(f'SELECT * FROM omikuji WHERE QQ = \'{QQ}\'')
        searchResult = None
        for row in result:
            searchResult = row
        conn.close()
        if searchResult:
            print(searchResult[0])
            return float(searchResult[1]), searchResult[2]
        else:
            return None

    
    # 写入抽签结果
    def writeOmikujiResult(self, QQ: str, randomNum: float, musicId: str):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        cur.execute(f"INSERT INTO omikuji VALUES({QQ}, {randomNum}, {musicId})")
        conn.commit()
        conn.close()
    

    # 清空抽签结果
    def cleanOmikujiResult(self):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        cur.execute(f"DELETE FROM omikuji")
        conn.commit()
        conn.close()

    
    def getVersion(self):
        conn = sqlite3.connect(self.dbPath)
        cur = conn.cursor()
        searchResult = None
        try:
            result = cur.execute(f'SELECT * FROM DBVersion')
            for row in result:
                searchResult = row
            return searchResult[0]
        except:
            return '100'


class DBUpgrade(object):
    def __init__(self, dbName: str) -> None:
        self.dbName = dbName
    
     # 获取数据库版本信息
    def get_version(self):
        conn = sqlite3.connect(f"src/database/{self.dbName}.sqlite")
        cur = conn.cursor()
        searchResult = None
        try:
            result = cur.execute(f'SELECT * FROM DBVersion')
            for row in result:
                searchResult = row
            return searchResult[0]
        except:
            return '100'

    
    def upgrade(self):
        sqlPath = f"src/libraries/sql_upgrade_conf/{self.dbName}"
        # 获取升级文件列表
        fileList = getFileList(sqlPath)
        fileList.sort()
        # 获取数据库版本
        currentVersion = self.get_version()

        conn = sqlite3.connect(f"src/database/{self.dbName}.sqlite")
        cur = conn.cursor()
        
        for file in fileList:
            if int(file.split('.')[0]) > int(currentVersion):
                sql = open(f"{sqlPath}/{file}", 'r')
                sqlCmd = sql.readlines()
                sql.close()
                sqlCmd = "".join(sqlCmd)
                cur.executescript(sqlCmd)

        cur.close()


        
if __name__ == '__main__':
    # DBInit(rebuild=True)
    # maimaiDB().update()
    print(maimaiDB().search('musicId', '8'))
    # print(miaDB().get_custom('1'))
    # print(miaDB().get_default())
    # miaDB().add_custom('1179782321','plateId', '206201')
    # maimaiDB().getUpdateTime()
