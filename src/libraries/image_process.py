from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
import base64

from src.libraries.CONST import font_path


# 将文字转换成图片
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


def image_to_base64(img, format='PNG'):
    output_buffer = BytesIO()
    img.save(output_buffer, format)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data)
    return base64_str


def bytes_to_base64(byte_data: bytes):
    return base64.b64encode(byte_data)


# 将文本格式化成图片并编码成必要的形式
def send_image(text: str):
    output = f"base64://{str(image_to_base64(text_to_image(text)), encoding='utf-8')}"


# 因为图片的resize需要同时指定宽和高，写一个能够同时进行宽和高缩放的函数
def scale(size: tuple, rate: float):
    return [int(size[0] * rate), int(size[1] * rate)]




if __name__ == '__main__':
    text_to_image('Hello World !')