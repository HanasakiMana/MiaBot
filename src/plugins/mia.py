# 这个文件主要包括了美亚相关的个性化功能

# 系统库
import os
import platform
import psutil

# nonebot
from nonebot.plugin import on_regex
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from nonebot.rule import to_me
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, Message, MessageSegment, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

# 自建文件导入
from src.libraries.image_process import image_to_base64 # 将文本格式化成图片并编码成必要的形式


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