import re
import base64
import jinja2
import aiohttp
import mimetypes
from pathlib import Path
from nonebot import get_driver
from nonebot.adapters.cqhttp import Message, MessageSegment
from src.libs.playwright import get_new_page

from .rss_class import RSS

global_config = get_driver().config
proxy = global_config.http_proxy

dir_path = Path(__file__).parent
template_path = dir_path / 'template'
env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path),
                         enable_async=True)


async def rss_to_msg(rss: RSS, info: dict) -> Message:
    msg = Message()
    img = await rss_to_image(rss, info)
    if not img:
        return None
    msg.append(MessageSegment.image(img))
    msg.append(info['link'])
    return msg


async def rss_to_image(rss: RSS, info: dict) -> bytes:
    html = await rss_to_html(rss, info)
    html = await replace_url(html, rss.link)
    async with get_new_page(viewport={"width": 300, "height": 100}) as page:
        await page.set_content(html, wait_until='networkidle')
        img = await page.screenshot(full_page=True)
    return img


async def rss_to_html(rss: RSS, info: dict) -> str:
    template = env.get_template(f'{rss.style}.html')
    return await template.render_async(rss=rss, info=info)


async def replace_url(text: str, base_url: str) -> str:
    pattern = r'<img .*?src=[\"\'](.*?)[\"\'].*?/>'
    urls = re.findall(pattern, text, re.DOTALL)
    for url in urls:
        if url.startswith('data:image'):
            continue
        url_new = RSS.parse_url(url, base_url)
        b64 = await url_to_b64(url_new)
        text = text.replace(url, b64, 1)
    return text


async def url_to_b64(url: str) -> str:
    result = await download_img(url)
    if not result:
        return url
    type = mimetypes.guess_type(url)[0]
    if not type:
        type = 'image'
    return f'data:{type};base64,{base64.b64encode(result).decode()}'


async def download_img(url: str) -> bytearray:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as resp:
                result = await resp.read()
        return result
    except:
        return None


def split_nhd_title(text, url):
    text = text.strip()
    pattern = r''
    pattern_fail = r''

    p_url = r'\[(?P<category>.*?)\]'
    p_title = r'(?P<title>.*?)'
    p_subtitle = r'\[(?P<subtitle>.*?)\]'
    p_size = r'\[(?P<size_num>[\d\.]+)\s*(?P<size_unit>[GMKTB]+)\]'
    p_author = r'\[(?P<author>\S+)\]'

    if 'icat' in url:
        pattern += p_url
    pattern += p_title
    pattern_fail = pattern
    if 'ismalldescr' in url:
        pattern += p_subtitle
    if 'isize' in url:
        pattern += p_size
        pattern_fail += p_size
    if 'iuplder' in url:
        pattern += p_author
        pattern_fail += p_author

    match = re.match(pattern, text)
    if not match:
        match = re.match(pattern_fail, text)
    if match:
        return match.groupdict()


def load_category_img(category):
    img_path = template_path / 'catsprites' / f'{category}.png'
    if not img_path.exists():
        return category
    with (img_path).open('rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


env.filters['split_nhd_title'] = split_nhd_title
env.filters['load_category_img'] = load_category_img
