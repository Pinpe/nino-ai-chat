from flask import *
import threading
import requests
import data
import core
import time


shell                          = Flask(__name__)
shell.jinja_env.filters['zip'] = zip


class state:
    reasoner       = True
    memory         = True
    login_done     = False
    latest_version = None


def alert(text, redirect):
    return f'''
        <script>
            alert('{text}')
            window.location.href = '{redirect}'
        </script>
    '''


def get_latest_version():
    while state.latest_version == None:
        state.latest_version = core.get_latest_version()
        time.sleep(5)


@shell.route('/login')
def pub_login():
    return render_template('login.html', theme_color=data.load_data()['config']['theme_color'])


@shell.route('/login_submit', methods=['POST'])
def login_submit():
    if request.form.get('password') == data.load_data()['config']['login_password']:
        state.login_done = True
        return redirect('/')
    else:
        return alert('密码似乎是错误的', '/login')


@shell.route('/')
def pub_root():
    last_hour = 0
    if (state.login_done == False) and (data.load_data()['config']['login_password'] != ''):
        return redirect('/login')
    context_pairs = []
    for i in data.load_data()['context']:
        parts = str(i).split('//')
        if parts[1] != last_hour:
            context_pairs.append(('shell', parts[0]))
        last_hour = parts[1]
        if parts[2] == '用户':
            context_pairs.append(('user', parts[3]))
        else:
            context_pairs.append(('ai', parts[3]))
            if parts[4] != '这条回复没有使用分割回复':
                context_pairs.append(('ai', parts[4]))
            if parts[5] != '这条回复没有添加长期记忆' and data.load_data()['config']['show_memory'] == True:
                context_pairs.append(('shell', f"{parts[5]}，已经记住了w"))
    if not context_pairs:
        context_pairs.append(('shell', '当前还没有上下文，打个招呼吧qwq'))
    context_type_list, context_list = zip(*context_pairs)
    return render_template(
        'index.html',
        # 上下文
        context_list      = context_list,
        context_type_list = context_type_list,
        # 聊天时的临时设置
        reasoner          = state.reasoner or None,
        memory            = state.memory or None,
        # 一些版本号获取
        latest_version    = state.latest_version,
        version           = core.get_version(),
        # 永久设置
        show_memory       = data.load_data()['config']['show_memory'],
        location          = data.load_data()['config']['location'],
        login_password    = data.load_data()['config']['login_password'],
        theme_color       = data.load_data()['config']['theme_color'],
        left_image        = data.load_data()['config']['left_image'],
        model_base_url    = data.load_data()['config']['model_base_url'],
        reasoner_model    = data.load_data()['config']['reasoner_model'],
        common_model      = data.load_data()['config']['common_model'],
        first_use         = data.load_data()['config']['first_use']
    )


@shell.route('/send', methods=['POST'])
def send():
    state.reasoner = False if request.form.get('reasoner') is None else True
    state.memory = False if request.form.get('memory') is None else True
    file = request.files['attachment_file']
    is_img = False
    for i in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff']:
        if i in file.filename:
            file.save('temp/attachment_img.png')
            is_img = True
            break
    file.save('temp/attachment_file.txt') if is_img==False else None
    core.send(
        user_input    = request.form.get('content'),
        reasoner      = state.reasoner,
        memory        = state.memory,
        location      = data.load_data()['config']['location']
    )
    return redirect('/#memory-text')


@shell.route('/config', methods=['POST'])
def config_():
    state.login_done = True
    data.update_config('first_use', 'false')
    data.update_config('show_memory', False if request.form.get('show-memory') is None else True)
    data.update_config('location', request.form.get('location'))
    data.update_config('login_password', request.form.get('login-password'))
    data.update_config('theme_color', request.form.get('theme-color'))
    data.update_config('left_image', request.form.get('left-image'))
    data.update_config('model_base_url', request.form.get('model-base-url'))
    data.update_config('reasoner_model', request.form.get('reasoner-model'))
    data.update_config('common_model', request.form.get('common-model'))
    return redirect('/')


@shell.route('/data')
def pub_data():
    return render_template(
        'data.html',
        memory_list = data.load_data()['memory'],
        tip         = '当前没有长期记忆，去创造美好的回忆吧qwq' if data.load_data()['memory'] == [] else '',
        theme_color = data.load_data()['config']['theme_color']
    )


@shell.route('/add-memory', methods=['POST'])
def add_memory():
    data.add_data('memory', request.form.get("memory_content"))
    return redirect('/data')


@shell.route('/remove-memory', methods=['POST'])
def remove_memory():
    data.remove_data('memory', request.form.get('memory'))
    return redirect('/data')


@shell.route('/remove-context')
def remove_context():
    data.remove_data('context')
    return redirect('/data')


@shell.route('/export-memory')
def export_memory():
    return send_file(
        'data/memory.json',
        download_name = f'{time.ctime()}_memory.json',
        as_attachment = True
    )


@shell.route('/export-context')
def export_context():
    return send_file(
        'data/context.json',
        download_name = f'{time.ctime()}_context.json',
        as_attachment = True
    )


@shell.route('/import-memory', methods=['POST'])
def import_memory():
    file = request.files['memory_file']
    file.filename = 'memory.json'
    file.save(f'data/{file.filename}')
    return redirect('/data')


@shell.route('/import-context', methods=['POST'])
def import_context():
    file = (request.files['context_file'])
    file.filename = 'context.json'
    file.save(f'data/{file.filename}')
    return redirect('/data')


@shell.route('/debug')
def pub_debug():
    return render_template(
        'debug.html',
        time         = time.ctime(),
        weather      = requests.get(f'https://api.seniverse.com/v3/weather/now.json?key={data.load_data()['env']['weather_api_key']}&location={data.load_data()['config']['location']}').text,
        config       = data.load_data()['config'],
        memory_list  = data.load_data()['memory'],
        context_list = data.load_data()['context']
    )


if __name__ == '__main__':
    get_latest_version_threading = threading.Thread(target=get_latest_version).start()
    shell.run(debug=True, use_reloader=False)