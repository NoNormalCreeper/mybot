from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .data_source import tex2pic


__des__ = 'LaTeX公式'
__cmd__ = '''
tex {equation}
支持行内公式和少量行间公式
'''.strip()
__short_cmd__ = 'tex {equation}'
__example__ = '''
tex a + b = c
tex \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}
'''.strip()
__usage__ = f'{__des__}\nUsage:\n{__cmd__}\nExample:\n{__example__}'


tex = on_command('tex', block=True, priority=12)


@tex.handle()
async def _(msg: Message = CommandArg()):
    equation = msg.extract_plain_text().strip().strip('$')
    if not equation:
        await tex.finish()

    image = await tex2pic(equation)
    if image:
        await tex.finish(MessageSegment.image(image))
    else:
        await tex.finish('出错了，请检查公式或稍后再试')
