from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
import base64

from CONST import font_path


def text_to_image(text):
    font = ImageFont.truetype(font_path + '/Hannotate.ttc', 24)
    padding = 10
    margin = 4
    text_list = text.split('\n')
    max_width = 0
    for text in text_list:
        width, height = font.getsize(text)
        max_width = max(max_width, width)
    image_width = max_width + padding * 2
    image_height = height * len(text_list) + margin * (len(text_list) - 1) + padding * 2
    image = Image.new('RGB', (image_width, image_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    for j in range(len(text_list)):
        text = text_list[j]
        draw.text((padding, padding + j * (margin + height)), text, font=font, fill=(0, 0, 0))
    image.show()
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


if __name__ == '__main__':
    text_to_image('Hello World !')