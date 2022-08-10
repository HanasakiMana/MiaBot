# 这个文件主要包括了与舞萌相关的核心功能

# 系统库
from PIL import Image
import re

# nonebot
from nonebot import get_driver, require
from nonebot import on_command, on_message, on_regex, on_message, on_regex
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, Bot, Event, Message, MessageSegment, GroupMessageEvent
from nonebot import get_bot
# 自建
from src.libraries.generate_b50v3 import GenerateB50
from src.libraries.image_process import image_to_base64, text_to_image
from src.libraries.database import maimaiDB
from src.libraries.CONST import jacket_path, server_ip


# 美亚唱歌
singASong = on_regex("唱歌", rule=to_me())
@singASong.handle()
async def _(bot: Bot, event: Event, state: T_State):
    message = str(event.get_message()).strip().split(' ')
    id = message[-1]
    if len(message) == 1:
        await musicTitleSearch.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('请输入歌曲的id并注意留有空格哦！')
        )
    else:
        try:
            musicId = id[-4:] # 封面里使用的id，最多只有四位
            while musicId[0] == '0':
                    musicId = musicId[1:]
                    print(musicId)
            try:
                musicData = maimaiDB().search('musicId', musicId)
                title = musicData[0][1]
                artist = musicData[0][2]
            except:
                title = ''
                artist = ''
            jacketId = musicId
            if len(jacketId) < 4:
                jacketId = (4 - len(jacketId)) * '0' + jacketId # id不足四位进行补全0
            musicUrl = f"http://{server_ip}/music/{musicId}.mp3"
            jacketUrl = f"http://{server_ip}/jacket/UI_Jacket_00{jacketId}.png"
            print(event.dict().get('group_id'))
            await singASong.send(Message(
                MessageSegment.music_custom(
                    url=f'链接：{musicUrl}',
                    audio=musicUrl,
                    title=title,
                    content=artist,
                    img_url=jacketUrl
                )
            ))
        except:
            await musicTitleSearch.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('美亚没有找到这样的歌曲，请检查歌曲/谱面id后再试哦！')
        )

# 根据部分歌曲名称搜索歌曲
musicTitleSearch = on_regex("^search")
@musicTitleSearch.handle()
async def _(bot: Bot, event: Event, state: T_State):
    message = str(event.get_message()).strip().split(' ')
    keyword = message[-1]
    # 异常处理
    if len(message) == 1:
        await musicTitleSearch.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('美亚支持通过歌曲名称的全部或部分进行检索，请输入要检索的关键字哦！')
        )
    else:
        # 获得一个包含全部匹配结果的列表
        resultList = maimaiDB().search(type='title', keyword=keyword)
        if len(resultList) == 0:
            await musicTitleSearch.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'美亚没有找到这样的歌曲，请仔细检查之后再试哦！')
            )
        else:
            outputStr = '\n'
            count = 0
            for result in resultList:
                outputStr += f'{result[0]}: {result[1]}\n'
                if result[-2]: # 标准谱面id
                    outputStr += f'    标准谱面id: {result[-2]}\n'
                if result[-1]: # 标准谱面id
                    outputStr += f'    DX谱面id: {result[-1]}\n'
                count += 1
            outputStr += f'数据更新时间：{maimaiDB().getUpdateTime()}'
            if count > 20:
                await musicTitleSearch.send(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text(f'美亚找到的歌曲太多啦（{count}首），请缩小范围再试哦！')
                )
            else:
                await musicTitleSearch.send(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text(outputStr)
                )


# 根据歌曲/谱面id检索歌曲信息
musicSearch = on_regex("^id")
@musicSearch.handle()
async def _(bot: Bot, event: Event, state: T_State):
    message = str(event.get_message()).strip().split(' ')
    keyword = message[-1]
    if len(message) == 1:
        if message == 'id':
            text = '请输入要检索的歌曲id哦！'
        else:
            text = '请注意id和数字之间要留有空格哦！'
        await musicTitleSearch.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text(text)
        )
    else:
        # 检索谱面id，再获取歌曲id
        result = maimaiDB().search('chartId', keyword=keyword)
        if len(result) != 0:
            musicId = result[0][2]
        else:
            result = maimaiDB().search('musicId', keyword=keyword)
            if len(result) != 0:
                musicId = keyword
            else:
                await musicTitleSearch.finish(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text(f'美亚没有找到这样的歌曲，请仔细检查之后再试哦！\n')
            )
        # 获取各难度定数
        result = maimaiDB().search('musicId', keyword=musicId)
        stdDs = [] # 各个难度的定数
        dxDs = []
        if result[0][-2]: # 标准谱面id
            chartResult = maimaiDB().search('chartId', keyword=result[0][-2])
            for data in chartResult:
                stdDs.append(data[5])
        if result[0][-1]: # dx谱面id
            chartResult = maimaiDB().search('chartId', keyword=result[0][-1])
            for data in chartResult:
                dxDs.append(data[5])
        # 歌曲信息
        if len(result) == 0:
            await musicTitleSearch.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'美亚没有找到这样的歌曲，请仔细检查之后再试哦！\n')
            )
        elif len(result) == 1:
            for row in result:
                result = row
            try:
                musicId = result[0]
                while len(musicId) < 4:
                    musicId = '0' + musicId
                jacket = Image.open(f'{jacket_path}/UI_Jacket_00{musicId}.png')
            except:
                jacket = Image.open(f'{jacket_path}/UI_Jacket_000000.png')
            outputStr = f'{result[0]}. {result[1]}\n\
作曲：{result[2]}\n\
分类：{result[3]}\n\
BPM：{result[4]}\n\
版本：{result[5]}\n'
            if result[-2]: # 标准谱面id
                outputStr += f'\n标准谱面id: {result[-2]}\n'
                outputStr += '谱面定数：'
                for i in stdDs:
                    outputStr += f'{i}/'
                outputStr = outputStr[:-1]
            if result[-1]: # dx谱面id
                outputStr += f'\nDX谱面id: {result[-1]}\n'
                outputStr += '谱面定数：'
                for i in dxDs:
                    outputStr += f'{i}/'
                outputStr = outputStr[:-1]
            await musicTitleSearch.send(
                MessageSegment.image(f"base64://{str(image_to_base64(jacket), encoding='utf-8')}")
                +MessageSegment.text(outputStr)
            )

# 查谱面信息
chartSearch = on_regex(r"^([绿黄红紫白])id ([0-9]+)")
@chartSearch.handle()
async def _(bot: Bot, event: Event, state: T_State):
    diffLabelList = ['绿', '黄', '红', '紫', '白']
    diffNameList = ['Basic', 'Advanced', 'Expert', 'Master', 'Re: MASTER']
    diffList = ['basic', 'advanced', 'expert', 'master', 'reMaster']
    
    regex = "([绿黄红紫白])id ([0-9]+)"
    cmdGroups = re.match(regex, str(event.get_message())).groups()
    diffIndex = diffLabelList.index(cmdGroups[0])
    
    try:
        diffName = diffNameList[diffIndex]
        diff = diffList[diffIndex]
        chartId = cmdGroups[-1]
    except:
        chartSearch.finish(
            MessageSegment.text("请输入正确的参数！")
        )
    chartData = maimaiDB().search('chartId', chartId, 'diff', diff)
    if len(chartData) == 1:
        try:
            chartData = chartData[0]
            chartType = chartData[1]
            musicId = chartData[2]
            chartLevel = chartData[4]
            chartDs = chartData[5]
            charter = chartData[6]
            title = maimaiDB().search('musicId', musicId)[0][1]
            outputStr = f"{chartId}. {title}({chartType})\n{diffName} {chartLevel}({chartDs})\n"
            tapCount, holdCount, slideCount, touchCount, breakCount = chartData[7], chartData[8], chartData[9], chartData[10], chartData[11]
            if touchCount is None:
                touchCount = '-'
            outputStr += f"TAP: {tapCount}\nHOLD: {holdCount}\nSLIDE: {slideCount}\nTOUCH: {touchCount}\nBREAK: {breakCount}\n谱师: {charter}"
            # 将musicId变成封面id
            jacketId = (4 - len(musicId)) * '0' + musicId
            try: 
                jacket = Image.open(f'{jacket_path}/UI_Jacket_00{jacketId}.png')
            except:
                jacket = Image.open(f'{jacket_path}/UI_Jacket_000000.png')
            await chartSearch.send(
                MessageSegment.image(f"base64://{str(image_to_base64(jacket), encoding='utf-8')}")
                +MessageSegment.text(outputStr)
            )
        except:
            await chartSearch.finish(
                MessageSegment.text("美亚没有找到这样的谱面，请重新检查后再试哦！(Internal Error)")
            )

    else:
        await chartSearch.finish(
            MessageSegment.text("美亚没有找到这样的谱面，请重新检查后再试哦！")
        )


