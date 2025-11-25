from flask import *
import requests
import core
import time

shell                          = Flask(__name__)
shell.jinja_env.filters['zip'] = zip
reasoner                       = True
memory                         = True

def alert(text, redirect):
    return f'''
        <script>
            alert('{text}')
            window.location.href = '{redirect}'
        </script>
    '''

@shell.route('/')
def pub_root():
    context_pairs = []
    for i in core.load_data()['context']:
        parts = str(i).split('//')
        if parts[1] == '用户':
            context_pairs.append(('user', parts[2]))
        else:
            context_pairs.append(('ai', parts[2]))
            if parts[3] != 'None':
                context_pairs.append(('ai', parts[3]))
            if parts[4] != 'None' and core.load_data()['config']['show_memory'] == True:
                context_pairs.append(('shell', f"{parts[4]}，已经记住了w"))
    if not context_pairs:
        context_pairs.append(('shell', '当前还没有上下文，打个招呼吧qwq'))
    context_type_list, context_list = zip(*context_pairs)
    return render_template(
        'index.html',
        # 上下文
        context_list      = context_list,
        context_type_list = context_type_list,
        # 聊天时的临时设置
        reasoner          = reasoner or None,
        memory            = memory or None,
        # 最新版本号获取
        latest_version    = core.get_latest_version(),
        # 永久设置
        show_memory       = core.load_data()['config']['show_memory'],
        location          = core.load_data()['config']['location'],
        left_image        = core.load_data()['config']['left_image'],
        model_base_url    = core.load_data()['config']['model_base_url'],
        reasoner_model    = core.load_data()['config']['reasoner_model'],
        common_model      = core.load_data()['config']['common_model'],
        first_use         = core.load_data()['config']['first_use']
    )

@shell.route('/send', methods=['POST'])
def send():
    global reasoner, memory
    reasoner = False if request.form.get('reasoner') is None else True
    memory = False if request.form.get('memory') is None else True
    file = request.files['attachment_file']
    file.save('temp/attachment_file.txt')
    core.send(
        user_input = request.form.get('content'),
        reasoner   = reasoner,
        memory     = memory,
        location   = core.load_data()['config']['location']
    )
    return redirect('/#memory-text')

@shell.route('/config', methods=['POST'])
def config_():
    core.update_config('first_use', 'false')
    core.update_config('show_memory', False if request.form.get('show-memory') is None else True)
    core.update_config('location', request.form.get('location'))
    core.update_config('left_image', request.form.get('left-image'))
    core.update_config('model_base_url', request.form.get('model-base-url'))
    core.update_config('reasoner_model', request.form.get('reasoner-model'))
    core.update_config('common_model', request.form.get('common-model'))
    return redirect('/')

@shell.route('/data')
def pub_data():
    return render_template(
        'data.html',
        memory_list = core.load_data()['memory'],
        tip         = '当前没有长期记忆，去创造美好的回忆吧qwq' if core.load_data()['memory'] == [] else ''
    )

@shell.route('/add-memory', methods=['POST'])
def add_memory():
    core.add_data('memory', request.form.get("memory_content"))
    return redirect('/data')

@shell.route('/remove-memory', methods=['POST'])
def remove_memory():
    core.remove_data('memory', request.form.get('memory'))
    return redirect('/data')

@shell.route('/remove-context')
def remove_context():
    core.remove_data('context')
    return redirect('/data')

@shell.route('/export-memory')
def export_memory():
    return send_file('data/memory.json', as_attachment=True)

@shell.route('/export-context')
def export_context():
    return send_file('data/context.json', as_attachment=True)

@shell.route('/import-memory', methods=['POST'])
def import_memory():
    file = request.files['memory_file']
    if file.filename == 'memory.json':
        file.save(f'data/{file.filename}')
        return redirect('/data')
    else:
        return alert('请上传正确的文件', '/data')

@shell.route('/import-context', methods=['POST'])
def import_context():
    file = (request.files['context_file'])
    if file.filename == 'context.json':
        file.save(f'data/{file.filename}')
        return redirect('/data')
    else:
        return alert('请上传正确的文件', '/data')

@shell.route('/debug')
def pub_debug():
    return render_template(
        'debug.html',
        time         = time.ctime(),
        weather      = requests.get(f'https://api.seniverse.com/v3/weather/now.json?key={core.load_data()['env']['weather_api_key']}&location={core.load_data()['config']['location']}').text,
        memory_list  = core.load_data()['memory'],
        context_list = core.load_data()['context']
    )

if __name__ == '__main__':
    shell.run(debug=True)