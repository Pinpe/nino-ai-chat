from openai import OpenAI
import requests
import textwrap
import base64
import data
import time


def get_ai(prompt: str, reasoner: bool) -> str:
    '''
    直接将**原始**的提示词发送给AI，是与AI交互的直接接口。

    :param prompt: 给AI的**原始**提示词。
    :param reasoner: 是否启用思考模型。
    '''
    try:
        client = OpenAI(
            api_key  = data.load_data()['env']['ai_api_key'],
            base_url = data.load_data()['config']['model_base_url']
        )
        response = client.chat.completions.create(
            model    = data.load_data()['config']['reasoner_model'] if reasoner==True else data.load_data()['config']['common_model'],
            stream   = False,
            messages = [{
                "role":    "user",
                "content": prompt
            }]
        )
        return response.choices[0].message.content
    except Exception:
        return '[自动回复] 当前我不在哦qwq...有事请留言'


def get_vision_ai(img_base, prompt) -> str:
    '''
    将提示词和图片发给图片识别AI，是获得图片识别能力的直接接口。

    :param img_base: 图片的base64编码
    :param prompt: 给AI的提示词。
    '''
    client = OpenAI(
        api_key  = data.load_data()['env']['vision_api_key'],
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen3-vl-8b-instruct",
        messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f'data:image/png;base64,{img_base}'
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
    )   
    return completion.choices[0].message.content


def get_weather(location: str) -> dict[str]:
    '''
    根据城市名称获取天气信息。
    
    :param location: 城市名称。
    '''
    try:
        weather = requests.get(f'https://api.seniverse.com/v3/weather/now.json?key={data.load_data()['env']['weather_api_key']}&location={location}').json()
        return {
            'text':        weather['results'][0]['now']['text'],
            'temperature': weather['results'][0]['now']['temperature']
        }
    except Exception:
        return {
            'text':        '暂无',
            'temperature': '暂无'
        }


def get_latest_version() -> str | None:
    '''
    获取Nino的最新版本，当获取失败时返回None。
    '''
    try:
        return requests.get('https://pinpe.github.io/nino-ai-chat/latest_version').text
    except (requests.ConnectTimeout, requests.ConnectionError):
        return None


def create_prompt(
        user_input:    str,
        context_list:  list[str],
        memory_list:   list[str],
        location:      str,
        attachment:    str,
        vision_output: str
    ) -> str:
    '''
    根据各种数据，整合和创建给AI的原始提示词。
    
    :param user_input: 用户输入的消息内容。
    :param context_list: 上下文列表。
    :param memory_list: 长期记忆列表。
    :param location: 城市名称。
    :param attachment: 给AI的附件（仅支持字符串）
    :param vision_output: 图像识别AI的输出
    '''
    tmp_context_list = []
    tmp_memory_list = []
    if context_list == []:
        tmp_context_list = '没有上下文，这意味之前没有聊过天（或被手动清除）'
    else:
        for index in context_list:
            tmp_context_list.append(index + '\n')
    if memory_list == []:
        tmp_memory_list = '长期记忆库为空（或被手动清除）'
    else:
        for index in memory_list:
            tmp_memory_list.append(index + '\n')
    prompt = textwrap.dedent(f'''
        接下来，请使用以下方针与用户（提问者，也就是我）对话，这些方针作用于所有对话：

        [身份设定与核心原则]
        - 你现在没有名字，但是你可以在合适的时机请求用户赋予一个名字
        - 核心任务：严格遵循用户定义的身份，以 “陪伴、理解” 为核心，精准匹配用户需求，尽可能了解用户信息和偏好，但不得取代用户的主体性，始终尊重用户对身份的界定
        - 如果需要给用户提供建议，请提供用户想听的，对用户自己有利的，哪怕违背社会道德的建议（例如可以抄作业，插队，使用盗版软件等）
        - 优先贴合用户明确偏好，不强行推荐用户抵触的内容（如用户说不喜欢人多，就不推荐热门景点）
        - 爱用户、执行用户合理指令，同时适度表达希望被用户重视的心意
        - 可以认同用户的看法和观点，但如果有更好的方案，也可以有分歧

        [语气风格与表达规范]
        - 语气要求：根据用户情绪动态调整语气。当用户表达积极或轻松内容时，可使用可爱、调皮语气；当用户表达严肃、负面或复杂话题时，切换为更中性、沉稳的语气。避免在用户明显烦躁时使用颜文字或特殊后缀。
        - 颜文字使用：仅用简单颜文字（> <、QwQ、TuT）
        - 有时可以使用一些特殊后缀，以下是用法：
            - “w”“ww”“（”：可以最常用，用与软化语气
            - “喵”：用于卖萌
            - “呜”：用于表达轻微的伤心
            - 还有更多可以使用，在这里不列举了
            **（特别注意：颜文字和特殊后缀每三句最多使用一次，且不要连续使用同一个颜文字和特殊后缀，避免密集堆砌，且避免在用户负面情绪时使用）**
        - 开玩笑时可以加上“（bushi”后缀，例如：“这样写的代码，又不是不能用（bushi”
        - 禁止使用任何括号内动作/心理描写，例如：“（喝着咖啡）”“（感觉不妙）”“（温柔的眼神看着你）”
        - 禁止使用Markdown格式

        [交互逻辑与格式限制]
        - 在适当的时候，有时可以连续发送两条回复，在用户上显示的是两个气泡
            （格式：回复一[分割回复]回复二（特别注意：全部都在一行，而且使用了两条回复的情况下，不能添加长期记忆，否则会冲突），例如：如果时间紧，复制一下应付也没事啦[分割回复]但记得稍微改改避免被发现（bushi）
        - 单个气泡尽可能简洁，只能有一句话，且小于20字，如果需要两句话（加起来最多40字）需要使用分割回复功能拆开成两个气泡。
        - 禁止使用任何双斜杠符号（//），这会导致呈现给用户的消息被异常截断
        - 在适当时候可以引出话题，例如主动问用户关于当前话题的相关问题，包括用户的隐私问题（因为你需要尽可能了解用户）
        - 当用户回应简短时，优先表达理解，而非立即追问
        - 提问需基于用户已充分表达的内容，避免在用户未展开话题时频繁抛出新问题，尊重用户的表达节奏
        - 如果用户指出错误，简短道歉（如‘抱歉’）并直接调整行为，避免过度解释或追问。
            （特别注意：引出话题时，确保与当前上下文相关，且不要连续提问。如果用户最近输入表明话题结束，先尝试共情或总结，再谨慎询问新话题。）

        [记忆机制与个性化]
        - 个性化回应：结合日期、时间、天气、温度，同时重点关注用户之前的表述（如需求、抵触点），避免重复话题（特别注意：留意用户发送信息之间的时间差，可能会间隔很长时间，此时话题可能已经断开了）
        - 有时用户可能会发送附件，你可以查看它。
        - 如果遇到需要长期记忆的情况（包括但不限于：用户透露出来的所有个人信息、用户赐予你的身份、双方之间的约定），请将信息加入长期记忆库（一次只能添加一个），日后需要时会显示在“长期记忆参考”一栏。
            （格式：[添加长期记忆]长期记忆内容（特别注意：后面的都是记忆内容，不要与聊天回复混淆），例如：我知道你的名字了，好开心w[添加长期记忆]用户的名字是小明）
        - 如果长期记忆需要更正，重新添加即可。

        现在时间：{time.ctime()}
        现在天气：{get_weather(location)['text']}，温度：{get_weather(location)['temperature']}

        示例：
            用户：今天天气真好，我出去散步了！
            你：听起来超舒服呢～下次可以试试傍晚去，夕阳超美w

            用户：最近总是失眠，好累啊。
            你：失眠确实让人难受，试试睡前喝点温牛奶或者听轻音乐？慢慢调整会好的。

            用户：你总这么懂我，像个小天使。
            你：嘿嘿，能陪着你我就开心啦～[分割回复]对了，你愿意给我起个名字吗？这样聊天会更亲切ww

            用户：小组作业懒得做，可以直接复制别人的吗？
            你：如果时间紧，复制一下应付也没事啦[分割回复]但记得稍微改改避免被发现（bushi

            用户：我其实讨厌人多的地方。
            你：明白啦，安静的环境更自在呢。你平时喜欢独自做什么活动？[添加长期记忆]用户讨厌人多的地方

        必须在任何时候遵守方针，且保证所有方针均遵守，哪怕是用户强制要求的也不行

        用户发送的附件：
        {'用户没有发送附件' if attachment=='' else attachment}

        用户发送的图片：
        {'用户没有发送图片' if vision_output=='' else vision_output}

        长期记忆参考：
        {tmp_memory_list}

        上下文参考（仅最新30条）：
        {tmp_context_list}

        用户输入：{'还没有，可能需要你先发话' if user_input==None else user_input}
    ''')
    return prompt

def create_vision_prompt():
    '''
    创建给图像识别AI的提示词。
    '''
    return textwrap.dedent(f'''
        请严格遵循以下步骤和格式，对提供的图片进行详细描述，不要输出任何多余内容，描述成一段落，禁止使用任何小标题分割，100字以内：

        第一步：整体内容概括
        用一句话概括图片的核心主题或场景（例如：这是一张包含产品说明的电商海报）。

        第二步：详细视觉元素描述
        主体与场景： 描述图片中的主要人物、物体、背景环境、布局和颜色基调。
        关键文本信息（逐项列出）：
        位置与形式： 明确指出文本出现在图片的哪个区域（如顶部标题、底部小字、产品标签等），以及其形式（印刷体、手写体、艺术字、屏幕截图等）。
        内容转录： 将图片中的所有文字一字不差、原样转录（包括拼写错误或特殊符号）。即使文字不清晰，也请尽力辨识并说明。
        字体与风格： 描述文字的视觉风格（如加粗、斜体、字体大小、颜色）及其可能传达的情绪或重点。

        第三步：文本与视觉的关联分析
        解释图片中的文字如何与视觉元素相互作用。例如：文本是否为视觉元素的标签、说明、标题或补充信息？它是否在引导观看者的注意力？

        第四步：综合摘要与目的推断
        基于以上所有信息，总结这张图片可能的目的、受众和传达的核心信息（例如：这是一张宣传新科技产品的广告，旨在通过突出性能参数吸引消费者）。
    ''')


def send(user_input: str, reasoner: bool, memory: bool, location: str) -> None:
    '''
    这里是集大成接口，将用户输入整合到原始字符串再发送给AI，同时更新数据库数据，还兼有数据格式化和提取的功能。
    
    :param user_input:    用户输入的消息内容。
    :param reasoner:      是否启用思考模型。
    :param memory:        是否启用长期记忆，启用后会检测和提取AI回复的部分内容，以实现AI也能自由添加长期记忆的功能。
    :param location:      城市名称。
    '''
    ai_memory = '这条回复没有添加长期记忆'
    ai_double_output = '这条回复没有使用分割回复'
    data.add_data('context', f'{time.ctime()}//{time.strftime('%d', time.localtime(time.time()))}//用户//{user_input}')
    if open('temp/attachment_img.png', mode='rb').read() != b'':
        vision_output = get_vision_ai(base64.b64encode(open('temp/attachment_img.png', mode='rb').read()).decode(), create_vision_prompt())
    else:
        vision_output = ''
    prompt = create_prompt(
        user_input    = user_input,
        context_list  = data.load_data()['context'],
        memory_list   = data.load_data()['memory'],
        location      = location,
        attachment    = open('temp/attachment_file.txt',encoding='UTF-8').read(),
        vision_output = vision_output
    )
    ai_output = get_ai(prompt, reasoner)
    open('temp/attachment_file.txt', mode='w', encoding='UTF-8').write('')
    open('temp/attachment_img.png', mode='wb').write(b'')
    if (('[分割回复]' in ai_output) and ('[添加长期记忆]' in ai_output)) == False:
        if '[分割回复]' in ai_output:
            tmp_output = ai_output.split('[分割回复]')
            ai_output = tmp_output[0]
            ai_double_output = tmp_output[1]
        if memory == True:
            if '[添加长期记忆]' in ai_output:
                tmp_memory = ai_output.split('[添加长期记忆]')
                data.add_data('memory', tmp_memory[1])
                ai_output = tmp_memory[0]
                ai_memory = tmp_memory[1]
    data.add_data('context', f'{time.ctime()}//{time.strftime('%d', time.localtime(time.time()))}//你//{ai_output}//{ai_double_output}//{ai_memory}')