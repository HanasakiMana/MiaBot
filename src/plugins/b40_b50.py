# b40/b50的相关功能

# 系统库
import os
import random
import json
import asyncio
import shutil

# nonebot
from nonebot import get_driver, require
from nonebot.plugin import on_command, on_regex
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from nonebot.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.message import event_preprocessor
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.params import Arg, CommandArg, ArgPlainText

from src.libraries.generate_b50v3 import GenerateB50
from src.libraries.image_process import image_to_base64


b40 = on_regex("b40")

@b40.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip().split(' ')[-1]
    print(username)
    if username == 'b40':
        img = await GenerateB50(qq=str(event.get_user_id()), b50=False).generate()
    else:
        img = await GenerateB50(username = username, b50=False).generate()
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
        await b40.send(Message([
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        ]))

b50 = on_regex("b50")

@b50.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip().split(' ')[-1]
    if username == 'b50':
        img = await GenerateB50(qq=str(event.get_user_id())).generate()
    else:
        img = await GenerateB50(username = username).generate()
    # 错误信息
    if img == 400:
        await b50.send(
            "美亚找不到你的数据，请确认你已经在查分器中已经注册并绑定好QQ了哦！\n查分器的使用教程戳这里：https://www.diving-fish.com/maimaidx/prober_guide"
        )
    elif img == 403:
        await b50.send(
            "这名玩家禁止别人查看TA的成绩哦，去和TA商量一下吧！"
        )
    else:
        await b50.send(Message([
            MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        ]))