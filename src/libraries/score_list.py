# 这个文件用于生成分数列表（基本是第一版B50的魔改）
from urllib.request import urlopen
from PIL import Image, ImageFont, ImageDraw
import asyncio
import aiohttp
import requests, re
from typing import Optional, Tuple
from CONST import b50_resource, jacket_path, font_path, customize_path, developer_token
from dotenv import load_dotenv
import os
import math

from generate_b50 import DataProcess

# 各种类型素材的目录
diff_path = b50_resource + '/Diffs' # 难度（BASIC，ADVANCED，EXPERT，MASTER，Re：MASTER）
medal_path = b50_resource + '/Medal' # 成就标志（FC，FC+，FS，FS+，AP，AP+，Blank）
rating_path = b50_resource + '/DXRating' # DX分数框
rank_path = b50_resource + '/Rank' # 等级（D，C，B，BB，BBB……）
MBase_path = b50_resource + '/MBase' # 封面背景
number_path = b50_resource + '/Number' # 数字表


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


class Generate(object):
    def __init__(self, page: int, qq: str = None, username: str = None, level: str = None, ds: float = None):
        self.qq = qq
        self.username = username
        self.page = page
        self.level = level
        self.ds = ds
         # 制作一个字典，里面包含了在整个数字表中每个字符的相对位置，分别乘以单个数字的宽和高就能当绝对坐标用（主要用于生成数字图片的函数）
        self.location_list = [[i, j] for j in range(0, 4) for i in range(0, 4)] # 生成一个4x4的数组用来标定位置
        sequence = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '-', ',', '.', 'lv']
        self.location_dict = {}
        for i in range(len(sequence)):
            self.location_dict.update({sequence[i]: self.location_list[i]})


    # 因为图片的resize需要同时指定宽和高，写一个能够同时进行宽和高缩放的函数
    def scale(self, size: tuple, rate: float):
        return [int(size[0] * rate), int(size[1] * rate)]

    
    # 获取当前用户的QQ头像
    def get_avatar(self):
        default = b50_resource + '/UI_Icon_209501.png' # 如果找不到头像就用一个默认的头像替代
        if self.qq == None:
            return default
        else:
            try:
                resp = requests.get(f"https://ssl.ptlogin2.qq.com/getface?imgtype=4&uin={self.qq}").text # 向QQ的api网站发送请求
                link = eval(re.search(r'[\{].*[\}]', resp).group(0)).get(self.qq) # 解析QQ返回的链接中头像的请求链接
                return urlopen(link)
            except:
                return default


    # 获取dx/标准的图标
    def get_dx_sd_icon(self, type: str):
        if type == 'DX':
            img = Image.open(b50_resource + '/UI_TST_Infoicon_DeluxeMode.png').convert('RGBA')    
        elif type == 'SD':
            img = Image.open(b50_resource + '/UI_TST_Infoicon_StandardMode.png').convert('RGBA')
        img = img.resize(self.scale(img.size, 0.35))
        return img


    # 制作分数的图片
    def get_score_img(self, score: float):
        score = str(score)
        # 如果小数点后不足四位就补齐0
        decimal = score.split('.')[-1]
        if len(decimal) < 4:
            score += (4 - len(decimal)) * '0'
        num_image = Image.open(number_path + '/UI_Num_Score_1110000_Gold.png').convert('RGBA') # 这张图是所有数字和标点都存在的一整张图，需要按需裁切
        per_image = Image.open(number_path + '/UI_RSL_Score_Per_Gold.png').convert('RGBA') # 百分号
        per_width, per_heigh = per_image.size # 百分号的尺寸
        
        # 根据当前图片的大小推算每个数字的大小
        width, heigh = num_image.size
        width, heigh = int(width/4), int(heigh/4)

        # 生成一个空白图片，长度是所有数字和百分号的长度，高度是数字的高度
        output = Image.new('RGBA', [len(score) * width + per_width, heigh + 30]) # 加高一些，避免数字被砍脚
        # 遍历分数的字符串，往output里加入图片
        for i in range(len(score)):
            pos = self.location_dict.get(score[i])
            num = num_image.crop((pos[0] * width, pos[1] * heigh, (pos[0] + 1) * width, (pos[1] + 1) * heigh))
            if score[i] == '.': # 这里是为了下移小数点的位置
                output.paste(num, (i * width, 13))
            else:
                output.paste(num, (i * width, 0))
        # 加入百分号
        output.paste(per_image, (len(score) * width, heigh - per_heigh))
        return output


   # 制作歌曲等级的图片（基本就是上面的函数改了改）
    def get_level_img(self, level: float, diff_level: str):
        level = str(level)
        # 根据不同的难度选择不同的数字表
        num_image = Image.open(number_path + f"/UI_NUM_MLevel_0{diff_level}.png")
        # 根据当前图片的大小推算每个数字的大小
        width, heigh = num_image.size
        width, heigh = int(width/4), int(heigh/4)

        # 生成一个空白图片，长度是所有数字和lv符号的长度，高度是数字的高度
        output = Image.new('RGBA', [(len(level) + 1) * width , heigh + 30]) # 加高一些，避免数字被砍脚
        
        # lv符号
        lv_pos = self.location_dict.get('lv')
        lv_image = num_image.crop((lv_pos[0] * width, lv_pos[1] * heigh, (lv_pos[0] + 1) * width, (lv_pos[1] + 1) * heigh))
        output.paste(lv_image, (0, 0))
        # 遍历定数的字符串，往output里加入图片
        for i in range(len(level)):
            pos = self.location_dict.get(level[i])
            num = num_image.crop((pos[0] * width, pos[1] * heigh, (pos[0] + 1) * width, (pos[1] + 1) * heigh))
            if level[i] == '+':
                output.paste(num, ((i + 1) * width - (i+ 1) * 10 - 5, 0), mask=num)
            else:
                output.paste(num, ((i + 1) * width - (i+ 1) * 10, 0), mask=num)
        return output


    # 制作定数的图片（基本就是上面的函数改了改）
    def get_ds_img(self, ds: float, diff_level: str):
        ds = str(ds)
        # 根据不同的难度选择不同的数字表
        num_image = Image.open(number_path + f"/UI_NUM_MLevel_0{diff_level}.png")
        # 根据当前图片的大小推算每个数字的大小
        width, heigh = num_image.size
        width, heigh = int(width/4), int(heigh/4)

        # 生成一个空白图片，长度是所有数字和lv符号的长度，高度是数字的高度
        output = Image.new('RGBA', [(len(ds) + 1) * width , heigh + 30]) # 加高一些，避免数字被砍脚
        
        # 遍历定数的字符串，往output里加入图片
        for i in range(len(ds)):
            pos = self.location_dict.get(ds[i])
            num = num_image.crop((pos[0] * width, pos[1] * heigh, (pos[0] + 1) * width, (pos[1] + 1) * heigh))
            if ds[i] == '.':
                output.paste(num, (i * width - (i + 1) * 10 - 10, 10), mask=num)
                # 小数点后肯定只有一位，这里直接把最后一位塞进去
                last_pos = self.location_dict.get(ds[i + 1])
                last_num = num_image.crop((last_pos[0] * width, last_pos[1] * heigh, (last_pos[0] + 1) * width, (last_pos[1] + 1) * heigh))
                output.paste(last_num, ((i + 1) * width - (i + 2) * 10 - 15, 0), mask=last_num)
                return output
            else:
                output.paste(num, (i * width - (i + 1) * 10, 0), mask=num)


    # 获得游玩等级图标
    def get_rank_img(self, rank: str):
        # 配合文件名对字符串作修改（除了p字母外其他都是大写）
        rank_new = '' # 字符串是不可变对象，只能新建一个
        for i in range(len(rank)):
            if rank[i] != 'p':
                rank_new += rank[i].upper()
            else:
                rank_new += rank[i]
        return Image.open(rank_path + f"/UI_GAM_Rank_{rank_new}.png")

    
    # 将文字转换成图片
    def text_to_image(self, text: str, font_size: int, font_color: tuple = (255, 255, 255), font: str = '/msyh.ttc', max_length: int = 290): # 默认是白色和日语字体
        font = ImageFont.truetype(font_path + font, font_size, encoding='utf-8')
        padding = 10
        margin = 4
        # 如果字符数太多， 就截短并在结尾加省略号
        while font.getsize(text)[0] >= max_length:
            text = text[:-2]
            text += '…'
        text_list = text.split('\n')
        max_width = 0
        for text in text_list:
            width, height = font.getsize(text)
            max_width = max(max_width, width)
        image_width = max_width + padding * 2
        image_height = height * len(text_list) + margin * (len(text_list) - 1) + padding * 2
        image = Image.new('RGBA', (image_width, image_height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        for j in range(len(text_list)):
            text = text_list[j]
            draw.text((padding, padding + j * (margin + height)), text, font=font, fill=font_color)
        return image


    # 绘制单首乐曲的封面
    def draw_single_music(self, dict: dict, count: int): # 输入对应歌曲的字典
        # 分数的基本信息
        id = str(dict.get('song_id'))
        name = dict.get('title')
        ds = dict.get('ds')
        level = dict.get('level')
        diff_level = str(dict.get('level_index') + 1) # 水鱼定义的难度的label是0，1，2，3，4，需要加1
        rank = dict.get('rate') # 这个其实应该是rank（AAA， S， S+这些）
        score = dict.get('achievements')
        dxscore = dict.get('dxScore')
        fc = dict.get('fc')
        fs = dict.get('fs')
        type = dict.get('type') # SD/DX谱面
        
        # ----------进行素材的导入----------
        output = Image.open(MBase_path + f"/{diff_level}.png").convert('RGBA') # 打开背景

        # 导入封面
        jacket_id = id[-4:] # 封面里使用的id，最多只有四位
        if len(jacket_id) < 4:
            jacket_id = (4 - len(jacket_id)) * '0' + jacket_id # id不足四位进行补全0
        try: 
            jacket = Image.open(jacket_path + f"/UI_Jacket_00{jacket_id}.png").convert('RGBA').resize([118, 118]) # 打开封面
        except:
            jacket = Image.open(jacket_path + f"/UI_Jacket_000000.png").convert('RGBA').resize([118, 118])
        
        dx_sd_icon = self.get_dx_sd_icon(type) #dx/sd图标
        # 生成achievement（得分）的图片并做缩放
        score_image = self.get_score_img(score)
        score_image = score_image.resize(self.scale(score_image.size, 0.4))
        # 生成歌曲等级的图片并缩放
        level_image = self.get_level_img(level, diff_level)
        level_image = level_image.resize(self.scale(level_image.size, 0.6))
        # 获取得分等级图片
        rank_image = self.get_rank_img(rank)
        rank_image = rank_image.resize(self.scale(rank_image.size, 0.8))
        # 标题
        title_image = self.text_to_image(name, 13)
        # dxscore
        dxscore_image = self.text_to_image(str(dxscore), 14, (0, 0, 0))
        # 详细信息：
        music_rating = DataProcess(dict).get_music_rating(dict)
        id_image = self.text_to_image(str(f"#{count}    id: {id}     Rating: {ds} -> {music_rating}"), 14, (0, 0, 0), font='/msyhbd.ttc')
        # fc/ap图标的底板
        medal_base = Image.open(b50_resource + '/UI_RSL_MedalBase.png')
        medal_base = medal_base.resize(self.scale(medal_base.size, 0.3))
        # fc/ap图标（两个图标坐标不一样，需要分别确定坐标）
        fc_image = None
        fs_image = None
        if fc != '':
            fc_image = Image.open(medal_path + f"/{fc}.png")
            fc_image = fc_image.resize(self.scale(fc_image.size, 0.7))    
        if fs != '':
            fs_image = Image.open(medal_path + f"/{fs}.png")
            fs_image = fs_image.resize(self.scale(fs_image.size, 0.7))
        
        # ----------进行图片的绘制----------
        output.paste(jacket, (12, 12))
        output.paste(dx_sd_icon, (250, 12), mask=dx_sd_icon) # mask用图片本身创造一个透明度的蒙板，避免直接把图片范围内的像素透明度全变成0
        output.paste(score_image, (int(390 - score_image.size[0]/2), 60), mask=score_image)
        output.paste(level_image, (545, 45), mask = level_image)
        output.paste(rank_image, (12, 93), mask=rank_image)
        output.paste(title_image, (int(470 - title_image.size[0]/2), 4), mask=title_image)
        output.paste(dxscore_image, (575, 104), mask=dxscore_image)
        output.paste(id_image, (135, 104), mask=id_image)
        output.paste(medal_base, (139, 65), mask=medal_base)
        if fc_image is not None:
            output.paste(fc_image, (148, 67), mask=fc_image)
        if fs_image is not None:
            output.paste(fs_image, (188, 67), mask=fs_image)
        return output

    # 获取自定义设置
    def get_customize(self):
        customize_setting = open(customize_path + '/b50_customize.json').read()
        customize_dict = eval(str(customize_setting))
        try:
            if customize_dict.get(self.qq) is not None:
                return customize_dict.get(self.qq)
            else:
                return {'plate': '200101'}
        except:
            return {'plate': '200101'}


    async def generate(self):
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
                else:
                    return None, -1
                filtered_records = sorted(filtered_records, key=lambda level: level.get('achievements'), reverse=True)

                records_len = len(filtered_records)
                index = (self.page - 1) * 15 # 乘以每页显示的数量
                if index >= records_len or index < 0:
                    return None, -1

                output = Image.open(b50_resource + '/Background.png')
                output = output.crop((0, 0, 750, 2340))
                output = output.resize((750, 2700))
                avatar = Image.open(self.get_avatar()).resize((98, 98))
                avatar_frame = Image.open(b50_resource + '/UI_LIB_Plate_Icon.png').resize((110, 110))
                # 自定义姓名框
                customize = self.get_customize()
                plate_id = customize.get('plate')
                plate = Image.open(b50_resource + f"/plate/UI_Plate_{plate_id}.png")
                # 用户昵称
                dxrating_mask = Image.open(b50_resource + '/UI_RSL_DXRating_Mask.png') # 背景
                dxrating_mask = dxrating_mask.resize((274, 44))
                name_dx = Image.open(b50_resource + '/UI_CMN_Name_DX.png') # DX图标
                shougou = Image.open(b50_resource + '/UI_CMN_Shougou_Rainbow.png')
                if self.level:
                    shougou_text = self.text_to_image(f"等级分数列表：{self.level}，页数：{self.page}/{math.ceil(records_len / 15)}", 15, (0, 0, 0), font='/msyhbd.ttc')
                elif self.ds:
                    shougou_text = self.text_to_image(f"定数分数列表：{self.ds}，页数：{self.page}/{math.ceil(records_len / 15)}", 15, (0, 0, 0), font='/msyhbd.ttc')
                # 将用户昵称从半角转换成全角 https://www.jianshu.com/p/152e081fec1b
                name_Quan = ''
                for i in username:
                    if ord(i) < 0x0020 or ord(i) > 0x7e:
                        name_Quan += i
                    elif ord(i) == 0x0020: # 空格
                        name_Quan += chr(0x3000)
                    else:
                        name_Quan += chr(ord(i) + 0xfee0)
                name_img = self.text_to_image(name_Quan, 25, (0, 0, 0), font='/adobe_simhei.otf', max_length=220) # 用户昵称

                
                
                # 向背景添加单曲数据
                for i in range(index, min(index + 15, records_len)):
                    init_width = 20
                    init_heigh = 150
                    music_score = self.draw_single_music(filtered_records[i], i + 1)
                    music_score = music_score.resize(self.scale(music_score.size, 1.1))
                    output.paste(music_score, (init_width + (i%1) * 520, init_heigh + int(i/1) * 170), mask=music_score)
                output.paste(plate, (12, 12))
                output.paste(avatar, (20, 20))
                output.paste(avatar_frame, (15, 15), mask=avatar_frame)
                output.paste(dxrating_mask, (120, 53), mask=dxrating_mask)
                output.paste(name_dx, (333, 57), mask=name_dx)
                output.paste(name_img, (120, 55), mask=name_img)
                output.paste(shougou, (121, 92), mask=shougou)
                output.paste(shougou_text, (int(260 - shougou_text.size[0]/2), 88), mask=shougou_text)
                output.show()


if __name__ == '__main__':
    asyncio.run(Generate(1, '1179782321', ds=13.0).generate())