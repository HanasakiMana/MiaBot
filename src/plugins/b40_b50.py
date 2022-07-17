# b40/b50的相关功能

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

from src.libraries.generate_b50v3 import GenerateB50
from src.libraries.image_process import image_to_base64


b40 = on_command('b40')

@b40.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    if username == '':
        img = await GenerateB50(qq=str(event.get_user_id()), b50=False)
    else:
        img = await GenerateB50(username, b50=False)
    # 错误信息
    if img == 400:
        await b40.send(
            "美亚找不到你的数据，请确认你已经在查分器中已经注册并绑定好QQ了哦！\n查分器的使用教程戳这里：https://www.diving-fish.com/maimaidx/prober_guide"
        )
    elif img == 403:
        await b40.send(
            "这名玩家禁止别人查看TA的成绩哦，去和TA商量一下吧！"
        )
    else:
        b40.send(Message([
                {
                    "type": "image",
                    "data": {
                        "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
                    }
                }
            ]))


b50 = on_command('b50')

@b50.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    if username == '':
        img = await GenerateB50(qq=str(event.get_user_id()))
    else:
        img = await GenerateB50(username)
    # 错误信息
    if img == 400:
        await b40.send(
            "美亚找不到你的数据，请确认你已经在查分器中已经注册并绑定好QQ了哦！\n查分器的使用教程戳这里：https://www.diving-fish.com/maimaidx/prober_guide"
        )
    elif img == 403:
        await b40.send(
            "这名玩家禁止别人查看TA的成绩哦，去和TA商量一下吧！"
        )
    else:
        b40.send(Message([
                {
                    "type": "image",
                    "data": {
                        "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
                    }
                }
            ]))