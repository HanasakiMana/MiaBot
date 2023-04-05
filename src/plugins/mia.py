# 这个文件主要包括了美亚相关的个性化功能

# 系统库
import os
import platform
import psutil
import random
import re
from PIL import Image
from collections import Counter

# nonebot
from nonebot.plugin import on_regex, on_notice
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, PokeNotifyEvent
from nonebot.rule import to_me
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, Message, MessageSegment, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from src.libraries.database import maimaiDB, miaDB

# 自建文件导入
from src.libraries.image_process import image_to_base64 # 将文本格式化成图片并编码成必要的形式
from src.libraries.CONST import poke_path, jacket_path
from src.libraries.misc import getFileList


# 系统状态
status = on_regex('status', rule=to_me(), permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
@status.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        py_info = platform.python_version()
        pla = platform.platform()
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        memory = round(memory, 2)
        disk = psutil.disk_usage('/').percent
        msg = "服务器状态:\n"
        msg += f"  -系统版本：{pla}"
        msg += f"  -Python版本：{py_info}\n"
        msg += f"  -CPU占用：{cpu}%\n"
        msg += f"  -内存占用：{memory}%\n"
        msg += f"  -硬盘占用：{disk}%\n"
        msg += f"\n歌曲信息更新时间：{maimaiDB().getUpdateTime()}\n"
        msg += f"MIA数据库版本：V{miaDB().getVersion()}\n"
        if cpu > 80 or memory > 80:
            msg += "脑袋晕乎乎的……"
        else: msg += r"ニャーべラス～☆*:.｡. o(≧▽≦)o .｡.:*☆"
        await status.send(
            MessageSegment.reply(event.dict().get('message_id'))+
            MessageSegment.text(msg)
        )
    except:
        await status.send(
            MessageSegment.reply(event.dict().get('message_id'))+
            MessageSegment.text("没能获取系统状态……")
        )


# 手动更新数据库
updateDB = on_regex("update", rule=to_me(), permission=SUPERUSER)
@updateDB.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await updateDB.send(MessageSegment.text('正在更新歌曲数据库……'))
    maimaiDB().update()
    await updateDB.finish(
        MessageSegment.text(f'数据库更新完成！上一次更新时间为：{maimaiDB().getUpdateTime()}')
    )


# 戳一戳功能
'''async def _group_poke(bot: Bot, event: Event, state: T_State): # 用于判断戳一戳的行为和目标
    eventDict = event.dict()
    value = (eventDict.get('post_type') == 'notice' and eventDict.get('notice_type') == 'notify' and eventDict.get('sub_type') == 'poke' and eventDict.get('target_id') == event.self_id)
    return value

poke = on_notice(rule=_group_poke, priority=10, block=True)

@poke.handle()
async def _(bot: Bot, event: Event, state: T_State):
    # 记录用户poke次数
    miaDB().addPokeCount(str(event.get_user_id()))
    randomNum = random.random()
    # 在40%的可能性下，美亚从图库中选择一张图发送
    if randomNum <= 0.4:
        fileList = getFileList(poke_path)
        fileName = random.choice(fileList)
        img = Image.open(f'{poke_path}/{fileName}')
        await poke.finish(
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        )
    # 在40%的可能性下，美亚会从音频库中选择一段音频发送
    elif randomNum > 0.4 and randomNum <= 0.8:
        

'''


# 今日运势
omikuji = on_regex('^抽签')
@omikuji.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = str(event.get_user_id())
    text = ''

    if miaDB().getOmikujiResult(qq):
        randomNum, musicId = miaDB().getOmikujiResult(qq)
        text += '奇怪，美亚之前已经告诉过你了哦，你今天的运势是：\n\n'
    else:
        randomNum = random.random()
        musicId = maimaiDB().random()
        miaDB().writeOmikujiResult(qq, randomNum, musicId)

    
    # 抽签概率分布：[0: 0.05], (0.05: 0.15], (0.15: 0.3], (0.3: 0.5], (0.5: 0.7], (0.7: 0.85], (0.85: 0.95], (0.95: 1]
    if randomNum <= 0.05:
        text += "【大吉】\n哇！！！金色传说！！！！！今天的你是天选之子，一定是抽卡必定出金、一把吃鸡的程度吧！\n快快快，有什么想要的就去争取，有什么想做的就大胆去做吧！"
    elif randomNum <= 0.15:
        text += "【中吉】\n是中吉！！！不要有任何顾虑，想要给自己放个假就放心去玩，有什么想要做的事就大胆去做吧！\n用积极的眼光看世界的话，也许会有意想不到的收获？"
    elif randomNum <= 0.3:
        text += "【小吉】\n你抽到了小吉哦！想必今天的工作肯定能唰唰唰地结束，然后和朋友一起逛街、玩自己喜欢的游戏，好好地休息一下吧！\n一定要好好地记住自己的梦，也许梦里的愿望，有一天真的会实现哦？"
    elif randomNum <= 0.5:
        text += "【末吉】\n你抽到了末吉哦，平平稳稳的日常也很不错！\n只是在今天的话，小小地摸一下鱼也一定是被允许的吧？\n不过要小心，太摸的话有可能会迟到哦～"
    elif randomNum <= 0.7:
        text += "【小凶】\n啊哦，好像是小凶……\n今天可能会遇到让你稍稍烦心的事情呢，不过不用担心，控制好情绪、换个角度看问题的话，也许问题就可以迎刃而解哦！"
    elif randomNum <= 0.85:
        text += "【末吉】\n你抽到了末吉哦，平平稳稳的日常也很不错！\n只是在今天的话，小小地摸一下鱼也一定是被允许的吧？\n不过要小心，太摸的话有可能会迟到哦～"
    elif randomNum <= 0.95:
        text += "【大凶】\n呜哇，是大凶！怎么会这样！\n今天可能会遇到非常棘手的事情，不过不用担心！\n大凶某种意义上也是一种幸运哦，试着这样来想去转换心情吧！身边的大家也一定都会默默地支持你的！"
    elif randomNum <= 0.99:
        text += "【？？？】\n奇怪，为什么美亚看不出来你的运势呢？\n也许生活就是这样，不要去猜测未来会怎么样，而是应该永远期待下一个明天的到来吗？"
    else:
        text += "【超大吉】\n居然、居然是超大吉！！！！！！！\n这可是只有1%的概率才可以抽到的签！！！好强大的运气！今天的你一定是天选之子！\n如果最近有什么左右为难的事情，那就在今天做出决定吧，谁让今天是全世界都围绕着你的一天呢！"
    
    text += "\n\n今天的提分乐曲是：\n"
    
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
    for row in result:
                result = row
    try:
        musicId = result[0]
        while len(musicId) < 4:
            musicId = '0' + musicId
        jacket = Image.open(f'{jacket_path}/UI_Jacket_00{musicId}.png')
    except:
        jacket = Image.open(f'{jacket_path}/UI_Jacket_000000.png')
    outputStr = f'{result[0]}. {result[1]}\n'
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

    await omikuji.finish(
        MessageSegment.reply(event.dict().get('message_id'))
        +MessageSegment.text(text)
        +MessageSegment.image(f"base64://{str(image_to_base64(jacket), encoding='utf-8')}")
        +MessageSegment.text(outputStr)
    )


# 美亚帮我选
chooseOne = on_regex('[帮_选]', rule=to_me())
@chooseOne.handle()
async def _(bot: Bot, event: Event, state: T_State):
    optionList = str(event.get_message()).strip().split(' ')
    if len(optionList) <= 1:
        await chooseOne.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('请输入想要美亚帮忙选择的东西哦')
        )
    elif len(optionList) < 3:
        await chooseOne.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('选项太少啦，再检查一下吧！')
        )
    else:
        optionList = optionList[1:] # 清除第一个元素（‘美亚帮我选’这个命令）
        optionDict = dict(Counter(optionList))
        duplicate = [key for key, value in optionDict.items() if value > 1]
        if duplicate != []:
            await chooseOne.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text(f'怎么会有重复的{duplicate[0]}，不可以耍美亚！')
        )
        else:
            await chooseOne.finish(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'美亚建议选：{str(random.choice(optionList))} 哦！')
            )

