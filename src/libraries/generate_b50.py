# 这个文件主要用于生成b40/b50图片

import asyncio
import re
from urllib.request import urlopen
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import math
import requests
import datetime, pytz
import time


from CONST import b50_resource, jacket_path, font_path, customize_path


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

    # 从水鱼的服务器获取用户的B40/B50数据，并转成字典
    async def get_data(self):
        payload = self.get_payload() # 根据qq或username生成payload
        async with aiohttp.ClientSession() as session:
            async with session.post(url='https://www.diving-fish.com/api/maimaidxprober/query/player', json=payload)as resp:
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
    def __init__(self, data_dict: dict): # 传入字典
        self.data_dict = data_dict

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
        base_rating = [7.0, 8.0, 9.6, 11.2, 12.0, 13.6, 15.2, 16.8, 20.0, 20.3, 20.8, 21.1, 21.6, 22.4]
        base_line = [50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5, 101.1] # 最大值只能是101.0，这里设定一个比101大的值避免下面出现101.0被pass
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
# 思路：先生成每一首曲子对应的图片，再生成姓名框，最后整合到一张图上
class GenerateB50(object):

    def __init__(self, qq: str = None, username: str = None):
        self.qq = qq
        self.username = username
        
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
        # img = img.resize(self.scale(img.size, 0.35))
        return img


    # 制作分数的图片
    def get_score_img(self, score: float):
        score = str(format(score, '.4f'))# 如果小数点后不足四位要补齐0
        num_image = Image.open(number_path + f'/UI_NUM_MLevel_02.png').convert('RGBA') # 这张图是所有数字和标点都存在的一整张图，需要按需裁切
        # num_image = num_image.resize((344, 472))
        '''per_image = Image.open(number_path + '/UI_RSL_Score_Per_Gold.png').convert('RGBA') # 百分号
        per_width, per_heigh = per_image.size # 百分号的尺寸'''
        
        # 根据当前图片的大小推算每个数字的大小
        width, heigh = num_image.size
        width, heigh = int(width/4), int(heigh/4)

        # 生成一个空白图片，长度是所有数字和百分号的长度，高度是数字的高度
        output = Image.new('RGBA', [len(score) * width, heigh + 30]) # 加高一些，避免数字被砍脚
        # 遍历分数的字符串，往output里加入图片
        decimal_flag = False # 用来标记是否遍历到了小数点之后
        for i in range(len(score)):
            pos = self.location_dict.get(score[i])
            num = num_image.crop((pos[0] * width, pos[1] * heigh, (pos[0] + 1) * width, (pos[1] + 1) * heigh))
            if decimal_flag:
                num = num.resize(self.scale(num.size, 0.8))
            if score[i] == '.': # 这里是为了下移小数点的位置
                output.paste(num, (i * width - 20, 13), mask=num)
                decimal_flag = True
            else:
                if not decimal_flag:
                    output.paste(num, (i * width, 0))
                else:
                    output.paste(num, (int((i + 0.2) * (width - 10)), 11))
            # 加入百分号
            '''if i == len(score) - 1:
                output.paste(per_image, (int((i + 1.1) * (width - 10)), 45), mask=per_image)'''
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

    # 获得游玩等级图标
    def get_rank_img(self, rank: str):
        # 配合文件名对字符串作修改（除了p字母外其他都是大写）
        rank_new = '' # 字符串是不可变对象，只能新建一个
        for i in range(len(rank)):
            if rank[i] != 'p':
                rank_new += rank[i].upper()
            else:
                rank_new += rank[i]
        return Image.open(rank_path + f"/UI_TTR_Rank_{rank_new}.png")

    
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
        

    # 绘制单首乐曲的信息
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
        # 定义一个难度编号和素材文件里字母的字典
        diff_level_dict = {'1': 'BSC', '2': 'ADV', '3': 'EXP', '4': 'MST', '5': 'MST_Re'}
        diff_level_text = diff_level_dict.get(diff_level)
        
        # 生成一个用于做背景的图片
        output = Image.open(MBase_path + f"/UI_TST_PlateMask.png").convert('RGBA').resize((600, 288)) # 打开背景
        level_color_dict = {'1': (107, 188, 69), '2': (245, 187, 65), '3': (238, 130, 125), '4': (147, 88, 212), '5': (210, 172, 249)} # 难度对应的底色
        output.paste(Image.new('RGB', (600, 288), level_color_dict.get(diff_level)), (0, 0), mask=output) # 给背景上色
        output.paste(Image.new('RGB', (600,180), (32, 63, 121)), (0, 0), mask=output.crop((0, 0, 600, 180))) # 上半部分的底色
        output.paste(Image.new('RGB', (600, 4), (255, 255, 255)), (0, 180), mask=output.crop((0, 179, 600, 183))) # 分割线
        
        # 封面框
        jacket_frame = Image.open(MBase_path + f"/UI_UPE_MusicJacket_Base_{diff_level_text}.png").convert('RGBA')
        output.paste(jacket_frame, (-20, 0), mask=jacket_frame)
        
        # 封面
        jacket_id = id[-4:] # 封面里使用的id，最多只有四位
        if len(jacket_id) < 4:
            jacket_id = (4 - len(jacket_id)) * '0' + jacket_id # id不足四位进行补全0
        try: 
            jacket = Image.open(jacket_path + f"/UI_Jacket_00{jacket_id}.png").convert('RGBA') # 打开封面
        except:
            jacket = Image.open(jacket_path + f"/UI_Jacket_000000.png").convert('RGBA')
        jacket = jacket.resize([216, 216])
        output.paste(jacket, (31, 37))

        # dx/sd图标
        dx_sd_icon = self.get_dx_sd_icon(type)
        dx_sd_icon = dx_sd_icon.resize(self.scale(dx_sd_icon.size, 0.7))
        output.paste(dx_sd_icon, (435, 16), mask=dx_sd_icon)

        # 编号
        count_img = self.text_to_image(f"# {count}", 30, font='/adobe_simhei.otf')
        output.paste(count_img, (275, 10), mask=count_img)
        
        # 标题
        title_image = self.text_to_image(name, 40, font='/adobe_simhei.otf',max_length=300)
        output.paste(title_image, (270, 55), mask=title_image)

        # achievement（得分）
        score_image = self.get_score_img(score)
        score_image = score_image.resize(self.scale((score_image.size[0], score_image.size[1] + 20), 0.9)) # 这里改了图像原本的横纵比
        output.paste(score_image, (int(460 - score_image.size[0]/2), 108), mask=score_image)
        
        # 得分等级
        rank_image = self.get_rank_img(rank)
        rank_image = rank_image.resize(self.scale(rank_image.size, 0.4))
        output.paste(rank_image, (470, 180), mask=rank_image)

        # 歌曲等级
        level_image = self.get_level_img(level, diff_level)
        output.paste(level_image, (int(200 - level_image.size[0]/2), int(240 - level_image.size[1]/2)), mask=level_image)
        
        # 详细信息
        music_rating = DataProcess(dict).get_music_rating(dict)
        info_image = self.text_to_image(f"{ds}->{music_rating}", 30, font='/msyhbd.ttc', max_length=300)
        output.paste(info_image, (270, 180), mask=info_image)

        # 歌曲id
        id_img = self.text_to_image(f"id: {id}", 30, font='/msyhbd.ttc')
        output.paste(id_img, (270, 220), mask=id_img)

        # fc/ap图标（两个图标坐标不一样，需要分别确定坐标）
        if fc != '':
            fc_image = Image.open(medal_path + f"/{fc}.png")
            output.paste(fc_image, (465, 227), mask=fc_image)
        if fs != '':
            fs_image = Image.open(medal_path + f"/{fs}.png")
            output.paste(fs_image, (515, 227), mask=fs_image)

        # output.show()
        return output

    # 获取自定义设置
    def get_customize(self):
        customize_setting = open(customize_path + '/b50_customize.json').read()
        customize_dict: dict= eval(str(customize_setting))
        try:
            if customize_dict.get(self.qq) is not None:
                return customize_dict.get(self.qq)
            else:
                return {'plate': '200101'}
        except:
            return {'plate': '200101'}


    # 获取dx rating的框框并添加值
    def get_dxrating_frame(self, rating: int):
        # 根据rating推算出应该用哪个框
        rating_base = [0, 1000, 2000, 4000, 7000, 10000, 12000, 13000, 14000, 14500, 15000]
        frame_id_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
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
    async def draw_user_info(self, getBest):
       
        userData = DataProcess(getBest[0])
        user_name = userData.get_user_name()
        dxscore_b35 = userData.get_dxscore(35)
        dxscore_b15 = userData.get_dxscore(15)
        dxscore_sum = userData.get_dxscore(50)
    
        # 自定义姓名框
        customize = self.get_customize()
        plate_id = customize.get('plate')
        output = Image.open(b50_resource + f"/plate/UI_Plate_{plate_id}.png")

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
        for i in user_name:
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
        shougou_text = self.text_to_image(f"B35:{dxscore_b35} + B15:{dxscore_b15} = {dxscore_sum}", 15, (0, 0, 0), font='/msyhbd.ttc')
        output.paste(shougou, (109, 80), mask=shougou)
        output.paste(shougou_text, (int(248 - shougou_text.size[0]/2), 76), mask=shougou_text)

        return output


    async def generate(self):
        current_time = time.time()
        getBest = await GetBest(self.qq, self.username).get_data()
        # 背景
        output = Image.open(b50_resource + '/b50_background.png')
        output = output.resize((1500, 1800))
        user_info = await self.draw_user_info(getBest)
        user_info = user_info.resize(self.scale(user_info.size, 1.2))
        output.paste(user_info, (30, 30))

        # 获取B35和B15列表
        code = getBest[-1]
        if getBest[-1] == 400: # 解析错误代码
            return 400
        elif getBest[-1] == 403:
            return 403
        elif getBest[-1] == 200:
            # 获取基本信息
            userData = DataProcess(getBest[0])
            b35_list: list = userData.get_b35()
            b15_list: list = userData.get_b15()
        
        # 绘制B35
        for i in range(0, len(b35_list)):
            init_width = 30
            init_heigh = 200
            music_score = self.draw_single_music(b35_list[i], i + 1)
            music_score = music_score.resize(self.scale(music_score.size, 0.45))
            output.paste(music_score, (init_width + (i%5) * 290, init_heigh + int(i/5) * 150), mask=music_score)
        
        # 绘制B15
        for i in range(0, len(b15_list)):
            init_width = 30
            init_heigh = 1300
            music_score = self.draw_single_music(b15_list[i], i + 1)
            music_score = music_score.resize(self.scale(music_score.size, 0.45))
            output.paste(music_score, (init_width + (i%5) * 290, init_heigh + int(i/5) * 150), mask=music_score)

        # 生成信息
        network_img = Image.open(b50_resource + '/On.png')
        network_img = network_img.resize(self.scale(network_img.size, 1.3))
        output.paste(network_img, (1400, 30), mask=network_img)
        version_img = self.text_to_image('Ver.DX1.20', 30, font='/msyhbd.ttc')
        output.paste(version_img, (1200, 38), mask=version_img)
        generated_info = self.text_to_image("Generated by MiaBot", 30, font='/msyhbd.ttc', max_length=800)
        generated_time = self.text_to_image(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'), 30, font='/msyhbd.ttc', max_length=800)
        output.paste(generated_info, (1120, 80), mask=generated_info)
        output.paste(generated_time, (1120, 120), mask=generated_time)
        output.show()
        print(f'It takes {time.time() - current_time}s to generate')
        return output, code


if __name__ == '__main__':
    asyncio.run(GenerateB50(qq='1179782321').generate())