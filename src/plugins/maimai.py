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
from src.libraries.image_process import image_to_base64, text_to_image
from src.libraries.database import maimaiDB
from src.libraries.CONST import jacket_path, server_ip
from src.libraries.score_listv2 import generateScoreList


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
            musicId = id[-4:] # 封面里使用的id，最多只有四位
            while musicId[0] == '0':
                    musicId = musicId[1:]
                    print(musicId)
            try:
                musicData = maimaiDB().search('musicId', musicId)
                title = musicData[0][1]
                artist = musicData[0][2]
            except:
                title = musicId
                artist = ''
            jacketId = musicId
            if len(jacketId) < 4:
                jacketId = (4 - len(jacketId)) * '0' + jacketId # id不足四位进行补全0
            musicUrl = f"http://{server_ip}/{musicId}.mp3"
            jacketUrl = f"http://{server_ip}/jacket/UI_Jacket_00{jacketId}.png"
            jsonStr = {"app":"com.tencent.structmsg","desc":"音乐","view":"music","ver":"0.0.0.1","prompt":title,"meta":{"music":{"sourceMsgId":"0","title":title,"desc":artist,"preview":musicUrl,"tag":"","musicUrl":"","jumpUrl":"https://www.abcio.cn","appid":3353779836,"app_type":1,"action":"","source_url":"","source_icon":"","android_pkg_name":""}},"config":{"forward":0,"showSender":1}}
            jsonStr = str(jsonStr).replace(',', '&#44;')

            await singASong.send(Message(
                MessageSegment.text(musicUrl)
            ))

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
        sdezResultList = maimaiDB().search(type='title', keyword=keyword, dbType='SDEZ')
        
        if len(resultList) == 0 and len(sdezResultList) == 0:
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
            for sdezResult in sdezResultList:
                notInSDGB = True # 记录一个flag，用于确认该日服曲目是否包含在国服里
                for result in resultList:
                    if result[0] == sdezResult[0]:
                        notInSDGB = False
                if notInSDGB:
                    outputStr += f'{sdezResult[0]}: {sdezResult[1]}\n'
                    if sdezResult[-2]: # 标准谱面id
                        outputStr += f'    标准谱面id: {sdezResult[-2]}\n'
                    if sdezResult[-1]: # 标准谱面id
                        outputStr += f'    DX谱面id: {sdezResult[-1]}\n'
                    count += 1
            outputStr += f'国服数据更新时间：{maimaiDB().getUpdateTime()}'
            outputStr += f'\n\n日服数据版本：{maimaiDB().getSDEZDataVersion()}'
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
    keyword = message[-1] # 此时的keyword可能是歌曲id也可能是谱面id
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
        # 获取歌曲id
        # 以谱面id为关键字类型进行检索
        result = maimaiDB().search('chartId', keyword=keyword)
        sdezResult = maimaiDB().search('chartId', keyword=keyword, dbType='SDEZ')  
        # 检索国服
        if len(result) != 0: # 说明是谱面id，就可以从结果里拉取歌曲id
            musicId = result[0][2]
        else:
            result = maimaiDB().search('musicId', keyword=keyword)
            if len(result) != 0:
                musicId = keyword
        # 检索日服
        if len(sdezResult) != 0: 
            musicId = sdezResult[0][2]
        else:
            sdezResult = maimaiDB().search('musicId', keyword=keyword, dbType='SDEZ')
            if len(sdezResult) != 0:
                musicId = keyword

        # 生成歌曲信息

        # 根据国服和日服不同的结果返回查询到的定数结果（共2x2=4种）
        # 声明两个用于保存定数的变量
        stdDs = [] # 各个难度的定数
        dxDs = []
        # 二者都没找到的情况
        if len(result) == 0 and len(sdezResult) == 0:
            await musicTitleSearch.finish(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text(f'美亚没有找到这样的歌曲，请仔细检查之后再试哦！\n')
            )
        # 国服有而日服没有的情况
        elif len(result) != 0 and len(sdezResult) == 0:
            result = maimaiDB().search('musicId', keyword=musicId)
            if result[0][-2]: # 标准谱面id
                chartResult = maimaiDB().search('chartId', keyword=result[0][-2])
                for data in chartResult:
                    stdDs.append(data[5])
            if result[0][-1]: # dx谱面id
                chartResult = maimaiDB().search('chartId', keyword=result[0][-1])
                for data in chartResult:
                    dxDs.append(data[5])
        # 国服没有而日服有的情况
        elif len(result) == 0 and len(sdezResult) != 0:
            result = maimaiDB().search('musicId', keyword=musicId, dbType='SDEZ')
            if result[0][-2]: # 标准谱面id
                chartResult = maimaiDB('src/database/SDEZ.sqlite').search('chartId', keyword=result[0][-2], dbType='SDEZ')
                for data in chartResult:
                    stdDs.append(data[5])
            if result[0][-1]: # dx谱面id
                chartResult = maimaiDB('src/database/SDEZ.sqlite').search('chartId', keyword=result[0][-1], dbType='SDEZ')
                for data in chartResult:
                    dxDs.append(data[5])
        # 国服和日服都有的情况（可能存在定数差异和追加谱面）
        elif len(result) != 0 and len(sdezResult) != 0:
            result = maimaiDB().search('musicId', keyword=musicId)
            sdezResult = maimaiDB().search('musicId', keyword=musicId, dbType='SDEZ')
            
            sdgbStdDs = [] # 国服谱面定数
            sdgbDxDs = []
            sdezStdDs = [] # 日服谱面定数
            sdezDxDs = []

            if result[0][-2]: # 标准谱面id
                chartResult = maimaiDB().search('chartId', keyword=result[0][-2])
                for data in chartResult:
                    sdgbStdDs.append(data[5])
            if result[0][-1]: # dx谱面id
                chartResult = maimaiDB().search('chartId', keyword=result[0][-1])
                for data in chartResult:
                    sdgbDxDs.append(data[5])

            if sdezResult[0][-2]: # 标准谱面id
                chartResult = maimaiDB().search('chartId', keyword=sdezResult[0][-2], dbType='SDEZ')
                for data in chartResult:
                    sdezStdDs.append(data[5])
            if sdezResult[0][-1]: # dx谱面id
                chartResult = maimaiDB('src/database/SDEZ.sqlite').search('chartId', keyword=sdezResult[0][-1], dbType='SDEZ')
                for data in chartResult:
                    sdezDxDs.append(data[5])
            
            if sdgbStdDs == sdezStdDs: # 国服日服谱面定数完全一致
                stdDs = sdgbStdDs
            else:
                if len(sdgbStdDs) == len(sdezStdDs): # 只改变了定数，没有更改谱面
                    for i in range(len(sdgbStdDs)):
                        if sdgbStdDs[i] == sdezStdDs[i]:
                            stdDs.append(sdgbStdDs[i])
                        else:
                            stdDs.append(f"{sdgbStdDs[i]}->{sdezStdDs[i]}")
                else: # 增加了谱面
                    assert len(sdgbStdDs) == 4 and len(sdezStdDs) == 5
                    for i in range(0, 4):
                        if sdgbStdDs[i] == sdezStdDs[i]:
                            stdDs.append(sdgbStdDs[i])
                        else:
                            stdDs.append(f"{sdgbStdDs[i]}->{sdezStdDs[i]}")
                    stdDs.append(sdezStdDs[5])

            if sdgbDxDs == sdezDxDs: # 国服日服谱面定数完全一致
                dxDs = sdgbDxDs
            else:
                if len(sdgbDxDs) == len(sdezDxDs): # 只改变了定数，没有更改谱面
                    for i in range(len(sdgbDxDs)):
                        if sdgbDxDs[i] == sdezDxDs[i]:
                            dxDs.append(sdgbDxDs[i])
                        else:
                            dxDs.append(f"{sdgbDxDs[i]}->{sdezDxDs[i]}")
                else: # 增加了谱面
                    assert len(sdgbDxDs) == 4 and len(sdezDxDs) == 5
                    for i in range(0, 4):
                        if sdgbDxDs[i] == sdezDxDs[i]:
                            dxDs.append(sdgbDxDs[i])
                        else:
                            dxDs.append(f"{sdgbDxDs[i]}->{sdezDxDs[i]}")
                    dxDs.append(sdezDxDs[5])
        
        
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
            outputStr += f'\n\n日服数据版本：{maimaiDB().getSDEZDataVersion()}'
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

    try:
        chartData = maimaiDB().search('chartId', chartId, 'diff', diff)
    except:
        chartData = []

    try: 
        sdezChartData = maimaiDB().search('chartId', chartId, 'diff', diff, dbType='SDEZ')
    except:
        sdezChartData = []
    
    if len(chartData) == 0:
        if len(sdezChartData) == 0:
            # 完全无法检索到
            await chartSearch.finish(
                MessageSegment.text("美亚没有找到这样的谱面，请重新检查后再试哦！")
            )
        elif len(sdezChartData) != 0:
            # 日服限定曲目
            chartData = sdezChartData
        
        try:
            chartData = chartData[0]
            chartType = chartData[1]
            musicId = chartData[2]
            chartLevel = chartData[4]
            chartDs = chartData[5]
            charter = chartData[6]
            title = maimaiDB().search('musicId', musicId, dbType='SDEZ')[0][1]
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
    elif len(chartData) == 1:
        if len(sdezChartData) == 0:
            # 国服有而日服没有的曲子
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
        elif len(sdezChartData) == 1:
            # 国服和日服都有的曲子
            chartData = chartData[0]
            chartType = chartData[1]
            musicId = chartData[2]
            chartLevel = chartData[4]

            chartDs = chartData[5]
            sdezChartDs = sdezChartData[0][5]

            charter = chartData[6]
            title = maimaiDB().search('musicId', musicId)[0][1]
            
            if chartDs != sdezChartDs:
                outputStr = f"{chartId}. {title}({chartType})\n{diffName} {chartLevel}({chartDs}->{sdezChartDs})\n"
            else:
                outputStr = f"{chartId}. {title}({chartType})\n{diffName} {chartLevel}({chartDs})\n"
            tapCount, holdCount, slideCount, touchCount, breakCount = chartData[7], chartData[8], chartData[9], chartData[10], chartData[11]
            if touchCount is None:
                touchCount = '-'
            outputStr += f"TAP: {tapCount}\nHOLD: {holdCount}\nSLIDE: {slideCount}\nTOUCH: {touchCount}\nBREAK: {breakCount}\n谱师: {charter}"

            outputStr += f"\n\n日服数据版本：{maimaiDB().getSDEZDataVersion()}"
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


# 定数查询
base = on_regex(r"^base")
@base.handle()
async def _(bot: Bot, event: Event, state: T_State):
    message = str(event.get_message()).strip().split(' ')
    ds = message[-1]
    results = maimaiDB().search('chartDs', ds)
    outputText = ''
    for result in results:
        chartId = result[0]
        chartType = result[1]
        musicId = result[2]
        musicName = maimaiDB().search('musicId', musicId, dbType='SDEZ')[0][1]
        chartDiff = result[3]
        outputText += f"{chartId}. {musicName} {chartDiff} ({chartType})\n"
    outputText = outputText[:-1]
    output = text_to_image(outputText, 10, (0, 0, 0), max_length=10000)
    await base.finish(
        MessageSegment.reply(event.dict().get('message_id'))
        +MessageSegment.image(f"base64://{str(image_to_base64(output), encoding='utf-8')}")
    )


# baseline
baseline = on_regex('^line|^Line|^baseline|^Baseline|^分数线')
@baseline.handle()
async def _(bot: Bot, event: Event, state: T_State):
    cmdList = str(event.get_message()).strip().split(' ') # 分割命令
    if len(cmdList) == 1 and cmdList[0] in ('line', 'Line', 'baseline', 'Baseline', '分数线'):
        await baseline.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('关于分数线的使用方法：line 谱面难度&id 目标达成率\n例如：“line 紫id11173 100.5”')
        )
    elif len(cmdList) != 3:
        await baseline.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('请检查格式是否正确哦！\n')
        )
    else:
        chart = cmdList[1]
        line = float(cmdList[2])
        
        try:
            chartLevelChinese, chartId = re.match("([绿黄红紫白])(?:id)?([0-9]+)", chart).groups()
            chartLevelList = ['basic', 'advanced', 'expert', 'master', 'reMaster']
            chartLevelChineseList = ['绿', '黄', '红', '紫', '白']
            chartLevel = chartLevelList[chartLevelChineseList.index(chartLevelChinese)]
        except:
            await baseline.finish(
            MessageSegment.reply(event.dict().get('message_id'))
            +MessageSegment.text('请检查输入的谱面格式是否正确哦！\n')
        )
        
        # 先搜国服再搜日服
        chartSearchResult = maimaiDB().search('chartId', chartId, 'diff', chartLevel)
        if chartSearchResult == []:
            chartSearchResult = maimaiDB().search('chartId', chartId, 'diff', chartLevel, dbType='SDEZ')
        
        if chartSearchResult == []:
            await baseline.finish(
                MessageSegment.reply(event.dict().get('message_id'))
                +MessageSegment.text('没有找到这样的谱面，请检查一下谱面id和难度哦\n')
            )
        else:
            chartData = chartSearchResult[0]
            musicId = chartData[2]
            
            title = maimaiDB().search('musicId', musicId, dbType='SDEZ')[0][1]
            tapCount, holdCount, slideCount, touchCount, breakCount = int(chartData[7]), int(chartData[8]), int(chartData[9]), chartData[10], int(chartData[11])
            if touchCount == None:
                touchCount = 0
            else:
                touchCount = int(touchCount)
            
            totalScore = 500 * tapCount + slideCount * 1500 + holdCount * 1000 + touchCount * 500 + breakCount * 2500
            breakBonus = 0.01 / breakCount # 绝赞总加分
            break50Reduce = totalScore * breakBonus / 4 # 50落减少的分数

            jacketId = (4 - len(musicId)) * '0' + musicId
            try: 
                jacket = Image.open(f'{jacket_path}/UI_Jacket_00{jacketId}.png')
            except:
                jacket = Image.open(f'{jacket_path}/UI_Jacket_000000.png')
            
            if (101-line) > 0 and (101-line) < 101:
                await baseline.finish(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text(
                        f"{chartLevelChinese}id{chartId}：{title}\n")
                    +MessageSegment.image(f"base64://{str(image_to_base64(jacket), encoding='utf-8')}")
                    +MessageSegment.text(
f'''在{line}%下最多允许的Tap GREAT数量为{(totalScore * (101-line)/10000):.2f}（每个-{10000 / totalScore:.4f}%）\n
绝赞（共{breakCount}个）50落相当于{(break50Reduce/100):.3f}个Tap GREAT（-{break50Reduce / totalScore * 100:.4f}%）'''
                    )
                )
            else:
                await baseline.finish(
                    MessageSegment.reply(event.dict().get('message_id'))
                    +MessageSegment.text('怎么可能会有这样的达成率嘛！')
                )


# 分数列表
scoreList = on_regex(r"[0-9]+\+?分数列表([0-9]+)?")
@scoreList.handle()
async def _(bot: Bot, event: Event, state: T_State):
    diff, page = str(event.get_message()).split('分数列表')[0], str(event.get_message()).split('分数列表')[1]
    if page == '':
        page = 1
    # 能成功就是ds，否则就是等级
    if len(diff.split('.')) != 1:
        diff = float(diff)
        outputImg = await generateScoreList(int(page), str(event.get_user_id()), ds=diff).generate()
    else:
        outputImg = await generateScoreList(int(page), str(event.get_user_id()), level=diff).generate()
    await scoreList.finish(
        MessageSegment.reply(event.dict().get('message_id'))
        +MessageSegment.image(f"base64://{str(image_to_base64(outputImg), encoding='utf-8')}")
    )
   