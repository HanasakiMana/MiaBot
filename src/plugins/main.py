# 这个文件主要包括了与舞萌相关的核心功能

# 系统库
import os
import random
import json
import asyncio
import shutil

# nonebot
from nonebot import get_driver, require
from nonebot import on_command, on_message, on_regex, on_message, on_regex
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, Message, MessageSegment, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException

# 自建文件导入
from src.libraries.database import DBInit, maimaiDB # 更新本地缓存的歌曲数据
from src.libraries.image_process import send_image # 将文本格式化成图片并编码成必要的形式
from src.libraries.generate_b50v3 import GenerateB50
from src.libraries.image_process import image_to_base64
# 声明nonebot的driver
driver = get_driver()


#声明一个用于编写定时任务的scheduler
scheduler = require("nonebot_plugin_apscheduler").scheduler


# 事件前处理
@event_preprocessor
async def preprocessor(bot, event, state):
    if hasattr(event, 'message_type') and event.message_type == "private" and event.sub_type != "friend":
        raise IgnoredException("not reply group temp message")


# 在启动时需要执行的函数
@driver.on_startup
def _():
    logger.info("Boot up successfully!")
    # 初始化数据库
    DBInit()
    maimaiDB().update()
    scheduler.add_job(
        # 每天0时从水鱼服务器抓取歌曲数据
        maimaiDB().update,
        trigger='cron',
        hour = 0,
        minute = 0
        )


'''# 帮助命令
help = on_command('help', aliases={'Help', '帮助'})

@help.handle()
async def _(bot: Bot, event: Event, state: T_State):
    command = str(event.get_message()).split(' ')
    text  = None
    if len(command) == 1: # 对应仅输入help而不包含任何其他指令的情况
        text = general.help_text.get('help') # general.help_text是一个包含了帮助文档文本的字典
    else: # 对应help之后跟有参数的情况（具体参考src/static/text/help下的文档）
        try:
            text = general.help_text.get(command[-1])
        except:
            pass
    if text is None:
        await help.finish('没救啦！')
    else:
        await help.finish(MessageSegment.image(send_image(text)))'''
