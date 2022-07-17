# 这个文件主要用于生成b50图片
# v2升级：优化了IO性能，兼容B40
# v3升级：尝试以背景板（frame）为背景生成b40/b50
# UNiVERSE When!!!!!!!!!!

import asyncio
import re
import ssl
from urllib.request import urlopen
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math
import requests
import datetime, pytz
import time


from src.libraries.CONST import b50_resource,plate_path, frame_path, jacket_path, font_path, mia_version
# 用于获取自定义设置的函数get_custom
from src.libraries.database import miaDB


# 各种类型素材的目录
diff_path = b50_resource + '/Diffs' # 难度（BASIC，ADVANCED，EXPERT，MASTER，Re：MASTER）
medal_path = b50_resource + '/Medal' # 成就标志（FC，FC+，FS，FS+，AP，AP+，Blank）
rating_path = b50_resource + '/DXRating' # DX分数框
rank_path = b50_resource + '/Rank' # 等级（D，C，B，BB，BBB……）
MBase_path = b50_resource + '/MBase' # 封面背景
number_path = b50_resource + '/Number' # 数字


# 从水鱼服务器上获取用户的b50成绩
class GetBest(object):
    def __init__(self, qq: str = None, username: str = None, b50: bool = True):
        self.qq = qq
        self.username = username
        self.b50 = b50

    # 从水鱼的服务器获取用户的B50数据，并转成字典
    async def get_data(self):
        payload = self.get_payload() # 根据qq或username生成payload
        async with aiohttp.ClientSession() as session:
            async with session.post(url='https://www.diving-fish.com/api/maimaidxprober/query/player', json=payload, ssl=False)as resp:
                if resp.status == 400: # 请求错误（找不到该用户）
                        return None, 400
                elif resp.status == 403: # 拒绝请求（该用户禁止查看B40/B50）
                    return None, 403
                elif resp.status == 200: # 正常
                    data = await resp.content.read()# 读取获取到的数据
                    data = eval(str(data.decode()).replace('null', 'None')) # 将获取到的数据转成str，将所有null替换成None后转成dict
                    # print(data)
                    return data, 200
                else:
                    return None, 'InternalError'

    # 拼接出payload
    def get_payload(self):
        payload = {}
        if self.qq != None and self.username == None: # 对应通过QQ号查询的情况
            payload = {'qq': self.qq}
        elif self.qq == None and self.username != None: # 对应通过用户名查询的情况
            payload = {'username': self.username}
        if self.b50 == True:
            payload.update({'b50': True}) # 判断是否需要加b50的token
        return payload


# 处理水鱼获取的字典
class DataProcess(object):
    def __init__(self, data_dict: dict, b50: bool = True): # 传入字典
        self.data_dict = data_dict
        self.b50 = b50

    # 获取用户的基本信息
    def get_user_name(self):
        return self.data_dict.get('nickname')

    # 获取B15字典
    def get_b15(self):
        charts: dict = self.data_dict.get('charts')
        return charts.get('dx')

    # 获取B35字典
    def get_b35(self):
        charts: dict = self.data_dict.get('charts')
        return charts.get('sd')

    # 利用上述函数返回的单曲字典计算单曲rating
    def get_music_rating(self, dict: dict):
        achievement: float = dict.get('achievements')
        ds: float = dict.get('ds')
        if self.b50:
            base_rating = [7.0, 8.0, 9.6, 11.2, 12.0, 13.6, 15.2, 16.8, 20.0, 20.3, 20.8, 21.1, 21.6, 22.4]
            base_line = [50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 101.1] # 最大值只能是101.0，这里设定一个比101大的值避免下面出现101.0被pass
        else:
            base_rating = [1.0, 5.0, 6.0, 7.0, 7.5, 8.5, 9.5, 10.45, 12.5, 12.7, 13.0, 13.2, 13.5, 14.0]
            base_line = [50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 101.1]
        for i in range(len(base_line)):
            if achievement >= base_line[i]:
                pass
            else:
                return math.floor(ds * (min(100.5, achievement) / 100) * base_rating[i])

    # 计算B35/B15的总分数
    def get_dxscore(self, type: int): # 这里需要选择是b35还是b15
        dxscore_sum = 0
        if type == 35:
            for sub_dict in self.get_b35():
                dxscore_sum += self.get_music_rating(sub_dict)
        elif type == 15:
            for sub_dict in self.get_b15():
                dxscore_sum += self.get_music_rating(sub_dict)
        elif type == 50:
            for sub_dict in self.get_b35():
                dxscore_sum += self.get_music_rating(sub_dict)
            for sub_dict in self.get_b15():
                dxscore_sum += self.get_music_rating(sub_dict)    
        return dxscore_sum


# 生成B50
# 思路：加载好每种素材，再依照每首歌的初始坐标粘贴到背景上
# 上述方法较之前按歌曲生成的方式而言，每种素材只加载到内存一次，优化了IO性能

class GenerateB50(object):
    
    def __init__(self, qq: str = None, username: str = None, b50: bool = True):
        self.qq = qq
        self.username = username
        self.b50 = b50
        
        # 制作一个字典，里面包含了在整个数字表中每个字符的相对位置，分别乘以单个数字的宽和高就能当绝对坐标用（主要用于生成数字图片的函数）
        self.location_list = [[i, j] for j in range(0, 4) for i in range(0, 4)] # 生成一个4x4的数组用来标定位置
        sequence = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '-', ',', '.', 'lv']
        self.location_dict = {}
        for i in range(len(sequence)):
            self.location_dict.update({sequence[i]: self.location_list[i]})


    # 因为图片的resize需要同时指定宽和高，写一个能够同时进行宽和高缩放的函数
    def scale(self, size: tuple, rate: float):
        return [int(size[0] * rate), int(size[1] * rate)]

    
    # 将文字转换成图片
    def text_to_image(self, text: str, font_size: int, font_color: tuple = (255, 255, 255), font: str = '/msyh.ttc', max_length: int = 290): # 默认是白色和日语字体
        font = ImageFont.truetype(font_path + font, font_size, encoding='utf-8')
        padding = 10
        margin = 4
        # 如果字符数太多，就截短并在结尾加省略号
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
    

    # 获取当前用户的QQ头像
    def get_avatar(self):
        default = b50_resource + '/UI_Icon_209501.png' # 如果找不到头像就用一个默认的头像替代
        if self.qq == None:
            return default
        else:
            try:
                resp = requests.get(f"https://ssl.ptlogin2.qq.com/getface?imgtype=4&uin={self.qq}", timeout=1).text # 向QQ的api网站发送请求
                link = eval(re.search(r'[\{].*[\}]', resp).group(0)).get(self.qq) # 解析QQ返回的链接中头像的请求链接
                return urlopen(link, context=ssl._create_unverified_context())
            except:
                return default


    # 获取dx rating的框框并添加值
    def get_dxrating_frame(self, rating: int):
        # 根据rating推算出应该用哪个框
        if self.b50:
            rating_base = [0, 1000, 2000, 4000, 7000, 10000, 12000, 13000, 14000, 14500, 15000]
            frame_id_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
        else:
            rating_base = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 8500]
            frame_id_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '11']
        frame_id = '11'
        for i in range(len(rating_base)):
            if rating >= rating_base[i]:
                frame_id = frame_id_list[i]
        output = Image.open(b50_resource + f"/DXRating/UI_CMN_DXRating_{frame_id}.png")
        output = output.resize(self.scale(output.size, 0.5))
        
        # 绘制分数
        rating = str(rating)
        # 还是需要对数字表进行切割
        num_img = Image.open(b50_resource + '/Number/UI_NUM_Drating.png')
        # 根据当前图片的大小推算每个数字的大小
        width, heigh = num_img.size
        width, heigh = int(width/4), int(heigh/4)

        # 生成一个空白图片，长度是6位数字的长度（留白），高度是数字的高度
        num_output = Image.new('RGBA', [6 * width , heigh], (0, 0, 0, 0))
        # 向图片加入数字
        for i in range(len(rating)):
            pos = self.location_dict.get(rating[-(i + 1)])
            num = num_img.crop((pos[0] * width, pos[1] * heigh, (pos[0] + 1) * width, (pos[1] + 1) * heigh))
            num_output.paste(num, ((5 - i) * width + 6 * i, 0), mask=num) # 6*i是为了更改数字间距
        
        num_output = num_output.resize(self.scale(num_output.size, 1.1))
        output.paste(num_output, (92, 15), mask=num_output)
        return output


    # 生成用户信息
    async def draw_user_info(self, username: str, dxscore_b35: int, dxscore_b15: int, additioal_rating: int = 0):
        dxscore_sum = dxscore_b35 + dxscore_b15 + additioal_rating
    
        # 自定义姓名框
        customize = miaDB().get_custom(self.qq)
        plate_id = customize[0]
        output = Image.open(plate_path + f"/UI_Plate_{plate_id}.png")

        # 用户头像
        avatar = Image.open(self.get_avatar()).resize((98, 98))
        avatar_frame = Image.open(b50_resource + '/UI_LIB_Plate_Icon.png').resize((110, 110))
        output.paste(avatar, (8, 8))
        output.paste(avatar_frame, (3, 3), mask=avatar_frame)

        # DX分数
        dxrating_image = self.get_dxrating_frame(dxscore_sum)
        dxrating_image = dxrating_image.resize(self.scale(dxrating_image.size, 0.53))
        output.paste(dxrating_image, (110, 6), mask=dxrating_image)

        # 用户昵称
        dxrating_mask = Image.open(b50_resource + '/UI_RSL_DXRating_Mask.png') # 背景
        dxrating_mask = dxrating_mask.resize((262, 32))
        name_dx = Image.open(b50_resource + '/UI_CMN_Name_DX.png') # DX图标
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
        output.paste(dxrating_mask, (108, 49), mask=dxrating_mask)
        output.paste(name_dx, (321, 45), mask=name_dx)
        output.paste(name_img, (108, 43), mask=name_img)

        # 称号（用来显示B35和B15的分数）
        shougou = Image.open(b50_resource + '/UI_CMN_Shougou_Rainbow.png')
        if self.b50:
            shougou_text = self.text_to_image(f"B35:{dxscore_b35} + B15:{dxscore_b15} = {dxscore_sum}", 15, (0, 0, 0), font='/msyhbd.ttc')
        else:
            dxscore = dxscore_b35 + dxscore_b15
            shougou_text = self.text_to_image(f"B40:{dxscore} + 段位分:{additioal_rating}", 15, (0, 0, 0), font='/msyhbd.ttc')
        output.paste(shougou, (109, 80), mask=shougou)
        output.paste(shougou_text, (int(248 - shougou_text.size[0]/2), 76), mask=shougou_text)
        return output


    async def generate(self):
        # 获取用户的数据
        getData = await GetBest(self.qq, self.username, b50=self.b50).get_data()
        code = getData[-1]
        if code == 400:
            return 400
        elif code == 403:
            return 403
        elif code == 200:
             # 获取基本信息
            userData = DataProcess(getData[0], b50=self.b50)
            b35List: list = userData.get_b35()
            b15List: list = userData.get_b15()
            userName: str = userData.get_user_name()
            b35Rating = userData.get_dxscore(35)
            b15Rating = userData.get_dxscore(15)
            if self.b50 is not True:
                additionalRating = int(getData[0].get('additional_rating'))
        

            # ----------加载素材----------
            # 加载背景
            customize = miaDB().get_custom(self.qq)
            frameId = customize[1]
            output = Image.open(frame_path + f'/UI_Frame_{frameId}.png')
            output = output.resize(self.scale(output.size, 1.5), resample=Image.HAMMING)

            # 姓名框种种
            if self.b50:
                userInfo = await self.draw_user_info(userName, b35Rating, b15Rating)
            else:
                userInfo = await self.draw_user_info(userName, b35Rating, b15Rating, additionalRating)
            userInfo = userInfo.resize(self.scale(userInfo.size, 0.7))
            if self.b50:
                output.paste(userInfo, (15, 15), mask=userInfo)
            else:
                output.paste(userInfo, (45, 15), mask=userInfo)

            # 生成信息
            # 网络标志
            network_img = Image.open(b50_resource + '/On.png')
            network_img = network_img.resize(self.scale(network_img.size, 0.8))
            # 版本信息
            version_img = self.text_to_image(f'Ver.{mia_version}', 20, font='/msyhbd.ttc')
            # 生成时间
            generated_info = self.text_to_image("Generated by MiaBot", 20, font='/msyhbd.ttc', max_length=800)
            generated_time = self.text_to_image(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'), 20, font='/msyhbd.ttc', max_length=800)
            if self.b50:
                output.paste(version_img, (1440, 18), mask=version_img)
                output.paste(network_img, (1575, 19), mask=network_img)
                output.paste(generated_info, (1380, 40), mask=generated_info)
                output.paste(generated_time, (1390, 65), mask=generated_time)
            else:
                output.paste(version_img, (1420, 18), mask=version_img)
                output.paste(network_img, (1555, 18), mask=network_img)
                output.paste(generated_info, (1360, 40), mask=generated_info)
                output.paste(generated_time, (1370, 65), mask=generated_time)

            # 根据给出的初始坐标，生成每首歌在图上的初始坐标
            b35Position = []
            if self.b50:
                init_width = 20
            else:
                init_width = 50
            init_heigh = 100      
            for i in range(0, len(b35List)):
                if self.b50:
                    b35Position.append([init_width + (i%7) * 120, init_heigh + int(i/7) * 115])
                else:
                    b35Position.append([init_width + (i%5) * 130, init_heigh + int(i/5) * 115])
            b15Position = []
            if self.b50:
                init_width = 900
            else:
                init_width = 750
            for i in range(0, len(b15List)):
                if self.b50:
                    b15Position.append([init_width + (i%3) * 120, init_heigh + int(i/3) * 115])
                else:
                    b15Position.append([init_width + (i%3) * 130, init_heigh + int(i/3) * 115])
                
            
            # 按照难度生成不同曲子的底板
            '''backGround = [None, None, None, None, None]
            for i in range(0, 5):
                backGround[i] = Image.open(MBase_path + f"/UI_TST_PlateMask.png").convert('RGBA').resize((190, 90)) # 加载背景所需的文件作为蒙版
                backGround[i].paste(Image.new('RGB', (190, 90), (32, 63, 121)), (0, 0), mask=backGround[i]) # 底色
                backGround[i].paste(Image.new('RGB', (190, 2), (255, 255, 255)), (0, 55), mask=backGround[i].crop((0, 54, 190, 56))) # 分割线
            level_color_list = [(107, 188, 69), (245, 187, 65), (238, 130, 125), (147, 88, 212), (210, 172, 249)] # 难度对应的底色
            for i in range(0, 5):
                backGround[i].paste(Image.new(mode='RGB', size=(190, 33), color=level_color_list[i]), (0, 57), mask=backGround[i].crop((0, 57, 190, 90)))'''
            
            # 加入歌曲的封面框
            # 定义一个难度编号和素材文件里文本的字典
            diff_level_dict = {0: 'BSC', 1: 'ADV', 2: 'EXP', 3: 'MST', 4: 'MST_Re'}
            jacketFrame = []
            for i in range(0, 5):
                diff_level_text = diff_level_dict.get(i)
                jacketFrame.append(Image.open(MBase_path + f"/UI_UPE_MusicJacket_Base_{diff_level_text}.png").resize((128, 117)))
            
            # dx/sd图标
            dxIcon = Image.open(b50_resource + '/UI_TST_Infoicon_DeluxeMode.png').convert('RGBA')
            dxIcon = dxIcon.resize(self.scale(dxIcon.size, 0.25))
            stdIcon = Image.open(b50_resource + '/UI_TST_Infoicon_StandardMode.png').convert('RGBA')
            stdIcon = stdIcon.resize(self.scale(stdIcon.size, 0.25))

            
            # 等级
            rank_list = ['A', 'AA', 'AAA', 'B', 'BB', 'BBB', 'C', 'D', 'S', 'Sp', 'SS', 'SSp', 'SSS', 'SSSp']
            rankDict = {}
            for fileName in rank_list:
                img = Image.open(rank_path + f"/UI_TTR_Rank_{fileName}.png")
                img = img.resize(self.scale(img.size, 0.17))
                rankDict.update({fileName: img})

            # 成绩(achievement)分数所需的素材
            achi_image = Image.open(number_path + f'/UI_NUM_MLevel_02.png').convert('RGBA')
            achi_width, achi_heigh = int(achi_image.size[0]/4), int(achi_image.size[1]/4)
            
            # fc/fs图标
            fcfs_img = {
                'fc': Image.open(medal_path + "/fc.png").resize((23, 23)),
                'fcp': Image.open(medal_path + "/fcp.png").resize((23, 23)),
                'ap': Image.open(medal_path + "/ap.png").resize((23, 23)),
                'app': Image.open(medal_path + "/app.png").resize((23, 23)),
                'fs': Image.open(medal_path + "/fs.png").resize((23, 23)),
                'fsp': Image.open(medal_path + "/fsp.png").resize((23, 23)),
            }
            

            # 为每首歌绘制信息
            def single_paste(dict: dict, position: list, count: int):
                # 坐标信息
                x, y = position
                # 当前歌曲的基本信息
                id = str(dict.get('song_id'))
                name = dict.get('title')
                ds = dict.get('ds')
                diff_level = dict.get('level_index') # 水鱼定义的难度的label是0，1，2，3，4，需要加1
                rank = dict.get('rate') # 这个其实应该是rank（AAA， S， S+这些）
                score = dict.get('achievements')
                fc = dict.get('fc')
                fs = dict.get('fs')
                type = dict.get('type') # SD/DX谱面

                # ----------粘贴元素----------
                
                # 背景
                # output.paste(backGround[diff_level], (x, y), backGround[diff_level])
                
                # 封面框
                output.paste(jacketFrame[diff_level], (x - 20, y), mask=jacketFrame[diff_level])
                
                # 封面
                jacket_id = id[-4:] # 封面里使用的id，最多只有四位
                if len(jacket_id) < 4:
                    jacket_id = (4 - len(jacket_id)) * '0' + jacket_id # id不足四位进行补全0
                try: 
                    jacket = Image.open(jacket_path + f"/UI_Jacket_00{jacket_id}.png").convert('RGBA') # 打开封面
                except:
                    jacket = Image.open(jacket_path + f"/UI_Jacket_000000.png").convert('RGBA')
                # 高斯模糊
                jacket = jacket.filter(ImageFilter.GaussianBlur(radius=8)).resize([88, 88])
                # 降低画面亮度
                jacket = ImageEnhance.Brightness(jacket).enhance(0.8)
                output.paste(jacket, (x + 1 , y + 15))

                # 编号
                count_img = self.text_to_image(f"# {count}", 15, font='/adobe_simhei.otf')
                output.paste(count_img, (x - 7, 5 + y), mask=count_img)
                
                # dx/sd图标
                if type == 'DX':
                    output.paste(dxIcon, (40 + x, 15 + y), mask=dxIcon)
                elif type == 'SD':
                    output.paste(stdIcon, (40 + x, 15 + y), mask=stdIcon)
                

                # 曲名
                title_image = self.text_to_image(name, 12, font='/adobe_simhei.otf',max_length=88)
                output.paste(title_image, (x - 8, 22 + y), mask=title_image)

                # 成绩
                score = str(format(score, '.4f'))
                achi = Image.new('RGBA', [len(score) * achi_width, achi_heigh + 30]) # 加高一些，避免数字被砍脚
                # 遍历分数的字符串，往output里加入图片
                decimal_flag = False # 用来标记是否遍历到了小数点之后
                for i in range(len(score)):
                    pos = self.location_dict.get(score[i])
                    num = achi_image.crop((pos[0] * achi_width, pos[1] * achi_heigh, (pos[0] + 1) * achi_width, (pos[1] + 1) * achi_heigh))
                    if decimal_flag:
                        num = num.resize(self.scale(num.size, 0.7))
                    if score[i] == '.':
                        # 因为莫名其妙的原因，小数点前面的位数会决定小数点的位置偏移，所以修正一下
                        if i == 2:
                            achi.paste(num, (i * achi_width - 30, 13), mask=num)
                        else:
                            achi.paste(num, (i * achi_width - 40, 13), mask=num)
                        decimal_flag = True
                    else:
                        if not decimal_flag:
                            achi.paste(num, (i * achi_width - i * 9, 0))
                        else:
                            achi.paste(num, (int((i + 0.2) * (achi_width - 10)) - i*10 + 13, 15))
                achi = achi.resize(self.scale(achi.size, 0.35))
                # 为了让数字居中
                output.paste(achi, (x + int((128 - achi.size[0])/2) + 3, 45 + y), mask=achi)
                
                # 得分等级（Rank）
                # 配合文件名对字符串作修改（除了p字母外其他都是大写）
                rank_new = '' # 字符串是不可变对象，只能新建一个
                for i in range(len(rank)):
                    if rank[i] != 'p':
                        rank_new += rank[i].upper()
                    else:
                        rank_new += rank[i]
                output.paste(rankDict.get(rank_new), (5 + x, 67 + y), mask=rankDict.get(rank_new))
                
                
                # 详细信息
                music_rating = DataProcess(dict, b50=self.b50).get_music_rating(dict)
                info_image = self.text_to_image(f"{ds}->{music_rating}", 12, font='/msyhbd.ttc', max_length=300)
                output.paste(info_image, (x - 7, 75 + y), mask=info_image)

                '''# 歌曲id
                id_img = self.text_to_image(f"id: {id}", 12, font='/msyhbd.ttc')
                output.paste(id_img, (x - 5, 75 + y), mask=id_img)'''

                # fc/fs图标
                try:
                    output.paste(fcfs_img.get(fc), (45 + x, 65 + y), mask=fcfs_img.get(fc))
                    output.paste(fcfs_img.get(fs), (65 + x, 65 + y), mask=fcfs_img.get(fs))
                except:
                    pass

            # 放置元素    
            for i in range(len(b35List)):
                single_paste(b35List[i], b35Position[i], i + 1)
            for i in range(len(b15List)):
                single_paste(b15List[i], b15Position[i], i + 1)

            return output


if __name__ == '__main__':
    asyncio.run(GenerateB50(qq='1179782321', b50=True).generate())
    
