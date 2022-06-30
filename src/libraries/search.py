# 这个文件主要包含了查歌的功能

import re

from music_data_process import musicData, update_music_data
from image_transform import text_to_image

class Search(object):
    def __init__(self):
        pass


    def search_from_name(self, name: str):
        self.results = []
        for key, ids in musicData().name_id.items():
            if re.search(name, key, re.I) is not None:
                for id in ids:
                    self.results.append(f'{id}: {key}')
        print(self.results)

if __name__ == '__main__':
    Search().search_from_name('lovely')
