# 这个文件主要准备了mia初始化所需的功能

import asyncio
import os

from music_data_process import update_music_data

from CONST import help_path


# 生成一些全局变量
class general():
    help_text = {}
    


    def __init__(self):
        self.load_help()


    # 加载帮助文档
    def load_help(self):
        file_list = os.listdir(help_path)
        for file in file_list:
            name = file.split('.')[0]
            txt = open(help_path + '/' + file, 'r')
            self.help_text.update({name: txt.read()})
            txt.close



class init():

    def __init__(self):
        update_music_data()



if __name__ == '__main__':
    general().load_help()
    print(general.help_text.get('help'))