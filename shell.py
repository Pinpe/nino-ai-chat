from flask import *
import requests
import data
import core
import time
import os
import json


# 启动时检查环境变量并更新 env.json
print("=" * 60)
print("Nino AI 启动中...")
print("=" * 60)

# 检查环境变量
ai_api_key_from_env = os.environ.get('ai_api_key')
weather_api_key_from_env = os.environ.get('weather_api_key')

if ai_api_key_from_env or weather_api_key_from_env:
    print("\n📋 检测到环境变量配置：")
    if ai_api_key_from_env:
        print(f"  - ai_api_key: {ai_api_key_from_env[:8]}...{ai_api_key_from_env[-4:]}")
    else:
        print("  - ai_api_key: 未设置")
    
    if weather_api_key_from_env:
        print(f"  - weather_api_key: {weather_api_key_from_env[:8]}...{weather_api_key_from_env[-4:]}")
    else:
        print("  - weather_api_key: 未设置")
    
    try:
        print("\n💾 正在读取 env.json 文件...")
        # 读取现有的 env.json
        with open('env.json', 'r', encoding='UTF-8') as f:
            env_config = json.load(f)
        print("✅ 成功读取 env.json")
        print(f"  - 原 AI API Key: {env_config.get('ai_api_key', '空')[:8]}...{env_config.get('ai_api_key', '空')[-4:] if len(env_config.get('ai_api_key', '')) > 12 else ''}")
        print(f"  - 原 Weather API Key: {env_config.get('weather_api_key', '空')[:8]}...{env_config.get('weather_api_key', '空')[-4:] if len(env_config.get('weather_api_key', '')) > 12 else ''}")
        
        # 更新环境变量
        updated = False
        if ai_api_key_from_env:
            old_value = env_config.get('ai_api_key', '')
            env_config['ai_api_key'] = ai_api_key_from_env
            if old_value != ai_api_key_from_env:
                updated = True
                print("\n🔄 更新 AI_API_KEY")
        
        if weather_api_key_from_env:
            old_value = env_config.get('weather_api_key', '')
            env_config['weather_api_key'] = weather_api_key_from_env
            if old_value != weather_api_key_from_env:
                updated = True
                print("🔄 更新 WEATHER_API_KEY")
        
        if updated:
            # 写回 env.json
            print("\n💾 正在写入 env.json 文件...")
            with open('env.json', 'w', encoding='UTF-8') as f:
                json.dump(env_config, f, ensure_ascii=False, indent=4)
            print("✅ 成功更新 env.json 文件")
            print(f"  - 新 AI API Key: {env_config['ai_api_key'][:8]}...{env_config['ai_api_key'][-4:]}")
            print(f"  - 新 Weather API Key: {env_config['weather_api_key'][:8]}...{env_config['weather_api_key'][-4:]}")
        else:
            print("\nℹ️  环境变量与配置文件相同，无需更新")
            
    except FileNotFoundError:
        print("\n⚠️  未找到 env.json 文件，正在创建...")
        env_config = {}
        if ai_api_key_from_env:
            env_config['ai_api_key'] = ai_api_key_from_env
        if weather_api_key_from_env:
            env_config['weather_api_key'] = weather_api_key_from_env
        
        with open('env.json', 'w', encoding='UTF-8') as f:
            json.dump(env_config, f, ensure_ascii=False, indent=4)
        print("✅ 已创建 env.json 文件")
        
    except Exception as e:
        print(f"\n❌ 更新 env.json 失败: {e}")
        print(f"错误类型: {type(e).__name__}")
else:
    print("\nℹ️  未检测到环境变量配置，使用 env.json 文件中的配置")

print("\n" + "=" * 60)
print("正在启动 Flask 应用...")
print("=" * 60 + "\n")

shell                          = Flask(__name__)
shell.jinja_env.filters['zip'] = zip


class state:
    reasoner      = True
    memory        = True
    double_output = True
    login_done    = False


def alert(text, redirect):
    return f'''
        <script>
            alert('{text}')
            window.location.href = '{redirect}'
        </script>
    '''


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
        double_output     = state.double_output or None,
        # 最新版本号获取
        latest_version    = core.get_latest_version(),
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
    state.double_output = False if request.form.get('double_output') is None else True
    file = request.files['attachment_file']
    file.save('temp/attachment_file.txt')
    core.send(
        user_input    = request.form.get('content'),
        reasoner      = state.reasoner,
        memory        = state.memory,
        double_output = state.double_output,
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
    shell.run(debug=True)