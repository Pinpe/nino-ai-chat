import os


def clean():
    print('\033[2J')
    print('\033[H', end='')

rst = '\033[m'
black = '\033[30m'
red = '\033[31m'
green = '\033[32m'
yellow = '\033[33m'
blue = '\033[34m'
purple = '\033[35m'
cyan = '\033[36m'
white = '\033[37m'


whl_err = False
env_err = False


print('\033[?25l',end='')
clean()
print(
    f"{yellow}Nino依赖安装脚本\n"
    f"{'':=^30}{rst}\n"
    '在使用Nino之前，需要先使用此脚本检查并安装相关依赖，以确保Nino可以运行。\n'
    '以下内容是所需依赖和当前状态，当所有条目均为绿色时，才可以运行Nino。\n'
)


try:
    import flask
    print(f'{green}    [O] flask       已安装{rst}')
except Exception:
    print(f'{red}    [!] flask       未安装{rst}')
    whl_err = True

try:
    import openai
    print(f'{green}    [O] openai      已安装{rst}')
except Exception:
    print(f'{red}    [!] openai      未安装{rst}')
    whl_err = True

try:
    import requests
    print(f'{green}    [O] requests    已安装{rst}')
except Exception:
    print(f'{red}    [!] requests    未安装{rst}')
    whl_err = True

try:
    import typer
    print(f'{green}    [O] typer       已安装{rst}')
except Exception:
    print(f'{red}    [!] typer       未安装{rst}')
    whl_err = True


try:
    open('env.json')
    print(f'{green}    [O] env文件     可以读取{rst}\n')
except Exception:
    print(f'{red}    [!] env文件     无法读取{rst}\n')
    env_err = True


if whl_err == True:
    print(f'{red}问题：{rst}一些库没有安装。')
if env_err == True:
    print(f'{red}问题：{rst}env文件无法读取。')
if env_err == False and whl_err == False:
    print(f'{green}恭喜！{rst}依赖一切正常，快去享受Nino吧！')
    print('\033[?25h',end='')
    exit(0)


print(f'按下{yellow}回车键{rst}以修复问题，{yellow}Ctrl+C{rst}退出')
input()
if whl_err == True:
    os.system('pip install flask openai requests typer')
if env_err == True:
    open('env.json', mode='w').write('{\n    "ai_api_key": "",\n    "vision_api_key": "",\n"weather_api_key": ""\n}')
print(f'{green}修复完成！{rst}可尝试重新运行此脚本以确认是否修复成功。')
if env_err == True:
    print(f'{yellow}注意：{rst}请在env.json填写api密钥，修复生成的是空的。')
exit(0)