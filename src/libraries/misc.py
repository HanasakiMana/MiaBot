import os


# 获取指定文件夹目录的文件列表，并且避免相对路径引发的问题
def getFileList(dirPath):
    currentPath = os.getcwd()
    os.chdir(dirPath)
    fileList = os.listdir()
    os.chdir(currentPath)
    return fileList