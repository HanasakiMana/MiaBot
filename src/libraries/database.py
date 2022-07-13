import sqlite3
import os
dbPath = 'src/database'
sqlFilePath = 'src/libraries/sql_conf'


class DBInit(object):
    def __init__(self) -> None:
        currentPath = os.getcwd()
        # 搜集sql文件
        os.chdir(sqlFilePath)
        sqlFileList = os.listdir()
        # 切换回工作目录
        os.chdir(currentPath)
        for sqlFile in sqlFileList:
            fileName = sqlFile.split('.')[0]
            self.createDB(sqlFilePath + '/' + sqlFile, fileName, dbPath)


    def createDB(self, sqlPath, dbName, dbPath):
        # 读取sql文件的指令
        sql = open(sqlPath, 'r')
        sqlCmd = sql.readlines()
        sql.close()
        sqlCmd = "".join(sqlCmd)

        # 创建数据库
        conn = sqlite3.connect(dbPath + '/' + dbName + '.sqlite')
        cur = conn.cursor()
        cur.executescript(sqlCmd)
        conn.commit()
        conn.close()


# maimai相关数据库的读写操作
class maimaiDB(object):
    def __init__(self, dbPath):
        self.dbPath = dbPath

    def writeMusicData(self, musicData: list):
        cmdList = []
        for singleMusicInfo in musicData:
            # 根据列表分析歌曲信息
            id: str = singleMusicInfo[0]
            title: str = singleMusicInfo[1]
            artist: str = singleMusicInfo[2]
            genre: str = singleMusicInfo[3]
            bpm: int = singleMusicInfo[4]
            addVersion: str = singleMusicInfo[5]
            stdChartId: str = singleMusicInfo[6]
            stdChartLevel: str = singleMusicInfo[7]
            dxChartId: str = singleMusicInfo[8]
            dxChartLevel: str = singleMusicInfo[9]
            isNew: int = singleMusicInfo[10]
            # 拼接sql语句
            cmdList.append(f'INSERT INTO musicInfo VALUES (                 \
                {id}, {title}, {artist}, {genre}, {bpm}, {addVersion},      \
                {stdChartId}, {stdChartLevel}, {dxChartId}, {dxChartLevel}, \
                {isNew});')
        cmd = "".join(cmdList)
        conn = sqlite3.connect(dbPath)
        cur = conn.cursor()


        
if __name__ == '__main__':
    DBInit()