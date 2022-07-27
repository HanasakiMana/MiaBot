# b40/b50的相关功能

# 系统库

from PIL import Image

# nonebot
from nonebot.plugin import on_regex
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment


# 自建函数
from src.libraries.generate_b50v3 import GenerateB50
from src.libraries.image_process import image_to_base64
from src.libraries.database import miaDB
from src.libraries.CONST import tmp_path


b40 = on_regex("^b40")
@b40.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip().split(' ')[-1]
    if username == 'b40':
        img = await GenerateB50(qq=str(event.get_user_id()), b50=False).generate()
    else:
        img = await GenerateB50(username = username, b50=False).generate()
    # 错误信息
    if img == 400:
        await b40.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text("美亚的本子上找不到你的数据，请确认你已经在查分器中已经注册并绑定好QQ了哦！\n查分器的使用教程戳这里：https://www.diving-fish.com/maimaidx/prober_guide")
        )
    elif img == 403:
        await b40.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text("这名玩家禁止别人查看TA的成绩哦，去和TA商量一下吧！")
        )
    else:
        await b40.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        )


b50 = on_regex("^b50")
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
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text("美亚的本子上找不到你的数据，请确认你已经在查分器中已经注册并绑定好QQ了哦！\n查分器的使用教程戳这里：https://www.diving-fish.com/maimaidx/prober_guide")
        )
    elif img == 403:
        await b50.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text("这名玩家禁止别人查看TA的成绩哦，去和TA商量一下吧！")
        )
    else:
        await b50.send(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
        )


# 自定义b50姓名框
plateCustom = on_regex('^自定义姓名框')
@plateCustom.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = str(event.get_user_id())
    id = str(event.get_message()).strip().split(' ')[-1]
    if id == '自定义姓名框':
        await frameCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'你可以通过输入“自定义姓名框 <姓名框id>”来自定义姓名框，姓名框id的列表可以在美亚的空间相册中找到哦！')
            )
    else:
        if miaDB().add_custom(qq, 'plateId', id):
            img = Image.open(f'{tmp_path}/plate/{id}.png')
            await plateCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'美亚已经记下来啦！你现在选择的姓名框是{id}:')
                +MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
            )
        else:
            await plateCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))+
                MessageSegment.text('美亚找不到你想要的姓名框，请重新检查id哦！')
            )

# 自定义b50背景板
frameCustom = on_regex('^自定义背景')
@frameCustom.handle()
async def _(bot: Bot, event: Event, state: T_State):
    qq = str(event.get_user_id())
    id = str(event.get_message()).strip().split(' ')[-1]
    if id == '自定义背景': # 对应没有id的情况
        await frameCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'你可以通过输入“自定义背景 <背景id>”的方式来自定义背景，背景id的列表可以在美亚的空间相册中找到哦！')
            )
    else:
        if miaDB().add_custom(qq, 'frameId', id):
            img = Image.open(f'{tmp_path}/frame/{id}.png')
            await frameCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text(f'美亚已经记下来啦！你现在选择的背景是{id}:')
                +MessageSegment.image(f"base64://{str(image_to_base64(img), encoding='utf-8')}")
            )
        else:
            await plateCustom.send(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text('美亚找不到你想要的背景，请重新检查id哦！')
            )
