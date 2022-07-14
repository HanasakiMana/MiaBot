import sqlite3
import os
import requests
import datetime, pytz
dbFolderPath = 'src/database'
sqlFilePath = 'src/libraries/sql_conf'


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
        chartData = {} # 谱面信息
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
            chartInfo = [chartType, musicId]
            # 遍历每一个难度的谱面
            for i in range(len(charts)):
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
                for i in [singleLevel, singleDs, charter, tap, hold, slide, touch, bReak]:
                    chartInfo.append(i)
            # 没有白谱的情况下需要对白谱的数据进行补全
            if len(charts) == 4:
                for i in range(8):
                    chartInfo.append('NULL')
            
            # 向谱面字典添加数据
            chartData.update({chartid: chartInfo})
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
            data = f"\'{id}\'"
            for i in info:
                # 给str套单引号，不然sql不认为是TEXT类型
                if isinstance(i, str):
                    # 如果曲名中出现了单引号，就需要把单引号打两遍，第一个相当于转义符
                    i = i.replace('\'', r"''")
                    # 套引号
                    i = f"\'{i}\'"
                data += f', {i}'
            return f'INSERT INTO {targetTable} VALUES({data})'

        # musicInfo
        for musicId, musicInfo in musicData.items():
            cmdList.append(joinCmd(musicId, musicInfo, 'musicInfo'))

        # chartInfo
        for chartId, chartInfo in chartData.items():
            cmdList.append(joinCmd(chartId, chartInfo, 'chartInfo'))
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
        



        
if __name__ == '__main__':
    DBInit(rebuild=True)
    maimaiDB().update()