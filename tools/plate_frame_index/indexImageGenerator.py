import os
from PIL import Image, ImageFont, ImageDraw


plate_path = 'src/static/image/plate'
frame_path = 'src/static/image/frame'
font_path = 'src/static/font'


def text_to_image(text: str, font_size: int, font_color: tuple = (255, 255, 255), font: str = '/msyh.ttc', max_length: int = 290): # 默认是白色和日语字体
    font = ImageFont.truetype(font_path + font, font_size, encoding='utf-8')
    padding = 10
    margin = 4
    # 如果字符数太多，就截短并在结尾加省略号
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

def scale(size: tuple, rate: float):
    return [int(size[0] * rate), int(size[1] * rate)]


# 获取id列表的函数
def getIdList(folderPath):
    currentPath = os.getcwd()
    os.chdir(folderPath)
    fileList = os.listdir()
    idList = []
    for file in fileList:
        idList.append(f"{file.split('.')[0].split('_')[-1]}")
    idList.sort()
    os.chdir(currentPath)
    return idList


# 生成姓名框/背景板索引，可以把所有样式合并在一张图片上并标上id
def getImageIndex(type: str):
    if type in ['Plate', 'Frame']:
        if type == 'Plate':
            idList = getIdList(plate_path)
            folderPath = plate_path
            saveFolder = 'tools/plate_frame_index/plate'
        else:
            idList = getIdList(frame_path)
            folderPath = frame_path
            saveFolder = 'tools/plate_frame_index/frame'
        # 获取图像的宽和高
        img = Image.open(f'{folderPath}/UI_{type}_{idList[0]}.png')
        scaleRate = 0.5

        for i in range(len(idList)): # 粘贴图片
            img = Image.open(f'{folderPath}/UI_{type}_{idList[i]}.png')
            img = img.resize(scale(img.size, scaleRate))
            idImg = text_to_image(idList[i], 40, (0, 0, 0))
            img.paste(idImg, (int(img.size[0]/2 - idImg.size[0]/2), int(img.size[1]/2 - idImg.size[1]/2)), mask=idImg)
            img.save(f'{saveFolder}/{idList[i]}.png')


getImageIndex('Frame')
getImageIndex('Plate')