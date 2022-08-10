# 这个文件主要包括了美亚相关的个性化功能

# 系统库
import os
import platform
import psutil
import random
from PIL import Image

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
from src.libraries.CONST import poke_path
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
        msg = "server status:\n"
        msg += f"OS: {pla}"
        msg += f"Running on Python {py_info}\n"
        msg += f"CPU {cpu}%\n"
        msg += f"MEM {memory}%\n"
        msg += f"DISK {disk}%\n"
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
    maimaiDB().update()
    await updateDB.finish(
        MessageSegment.text(f'数据库更新完成！上一次更新时间为：{maimaiDB().getUpdateTime()}')
    )


# 戳一戳功能
'''async def _group_poke(bot: Bot, event: Event, state: T_State): # 用于判断戳一戳的行为和目标
    eventDict = event.dict()
    value = (eventDict.get('post_type') == 'notice' and eventDict.get('notice_type') == 'notipy' and eventDict.get('sub_type') == 'poke' and eventDict.get('target_id') == event.self_id)
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