import re
import base64
from nonebot import require, get_bots, get_driver
from nonebot.adapters.cqhttp import MessageSegment

from .data_source import update_rss, update_rss_info
from .render import rss_to_image
from .rss_list import get_rss_list, get_user_ids

from .config import Config
global_config = get_driver().config
rss_config = Config(**global_config.dict())


def user_type(user_id: str):
    p_group = r'group_(\d+)'
    p_private = r'private_(\d+)'
    match = re.fullmatch(p_group, user_id)
    if match:
        return 'group', match.group(1)
    match = re.fullmatch(p_private, user_id)
    if match:
        return 'private', match.group(1)
    return '', user_id


async def rss_monitor():
    bots = list(get_bots().values())
    for bot in bots:
        user_ids = get_user_ids()
        for user_id in user_ids:
            user_rss_list = get_rss_list(user_id)
            for rss in user_rss_list:
                entries = await update_rss(rss)
                for entry in entries:
                    img = await rss_to_image(rss, entry)
                    if not img:
                        continue
                    msg = MessageSegment.image(
                        f"base64://{base64.b64encode(img).decode()}")
                    type, id = user_type(user_id)
                    if type == 'group':
                        await bot.send_group_msg(group_id=id, message=msg)
                    elif type == 'private':
                        await bot.send_private_msg(user_id=id, message=msg)


async def rss_info_monitor():
    user_ids = get_user_ids()
    for user_id in user_ids:
        user_rss_list = get_rss_list(user_id)
        for rss in user_rss_list:
            await update_rss_info(rss)


scheduler = require("nonebot_plugin_apscheduler").scheduler

rss_cron = rss_config.rss_update_cron
scheduler.add_job(
    rss_monitor,
    'cron',
    second=rss_cron[0],
    minute=rss_cron[1],
    hour=rss_cron[2],
    day=rss_cron[3],
    month=rss_cron[4],
    year=rss_cron[5],
    id='rss_monitor',
    coalesce=True,
    misfire_grace_time=30
)

rss_info_cron = rss_config.rss_info_update_cron
scheduler.add_job(
    rss_info_monitor,
    'cron',
    second=rss_info_cron[0],
    minute=rss_info_cron[1],
    hour=rss_info_cron[2],
    day=rss_info_cron[3],
    month=rss_info_cron[4],
    year=rss_info_cron[5],
    id='rss_info_monitor',
    coalesce=True,
    misfire_grace_time=30
)
