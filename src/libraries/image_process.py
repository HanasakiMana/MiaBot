from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
import base64

# from CONST import font_path
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
    image = Image.new('RGBA', (image_width, image_height), color=(255, 255, 255, 255))
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


# 因为图片的resize需要同时指定宽和高，写一个能够同时进行宽和高缩放的函数
def scale(size: tuple, rate: float):
    return [int(size[0] * rate), int(size[1] * rate)]




if __name__ == '__main__':
    text_to_image('''435. 願いを呼ぶ季節 master SD
468. ラブリー☆えんじぇる!! master SD
643. Excalibur ～Revived resolution～ expert SD
806. ナイトメア☆パーティーナイト reMaster SD
820. FFT expert SD
842. WORLD'S END UMBRELLA master SD
10181. 君の知らない物語 master DX
11150. ウマイネームイズうまみちゃん master DX
11155. ARAIS expert DX
11176. Climax expert DX
11178. ノーポイッ! master DX
11209. Grievous Lady expert DX
11236. Last Samurai expert DX
11272. 約束 master DX
11281. Re：End of a Dream expert DX
11288. Big Daddy expert DX
11293. LOSE CONTROL expert DX
11299. NAGAREBOSHI☆ROCKET expert DX
11300. U&iVERSE -銀河鸞翔- expert DX
11331. スーパーシンメトリー expert DX''', 10, (0, 0, 0), max_length=10000).show()