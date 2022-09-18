# 这个文件主要用于放置启动和定时执行的函数
# nonebot
from nonebot import get_driver, require
from nonebot.log import logger

# 自建文件导入
from src.libraries.database import DBInit, maimaiDB, miaDB, DBUpgrade# 更新本地缓存的歌曲数据


# 声明nonebot的driver
driver = get_driver()


#声明一个用于编写定时任务的scheduler
scheduler = require("nonebot_plugin_apscheduler").scheduler



# 在启动时需要执行的函数
@driver.on_startup
def _():
    logger.info("Boot up successfully!")
    # 初始化数据库
    DBInit()
    maimaiDB().update()
    DBUpgrade('mia_custom').upgrade()
    # 设定默认的姓名框和背景板
    miaDB().add_custom('default', 'plateId', '250101')
    miaDB().add_custom('default', 'frameId', '259505')
    # 每天0时从水鱼服务器抓取歌曲数据
    scheduler.add_job(
        maimaiDB().update,
        trigger='cron',
        hour = 0,
        minute = 0
        )
    # 每天0点清空抽签数据
    scheduler.add_job(
        miaDB().cleanOmikujiResult,
        trigger='cron',
        hour = 0,
        minute = 0
        )
