from typing_extensions import Annotated
import typer
import core
import data


def main(
        user_input    : Annotated[str, typer.Argument(help='给AI输入的消息')],
        reasoner      : Annotated[bool, typer.Option(help='是否启用思考模型')]    = True,
        memory        : Annotated[bool, typer.Option(help='是否允许写入长期记忆')] = True,
    ):
    '''
    这是Nino的命令行Shell，可以用于二开参考以及没有GUI的环境，但仅提供最简功能。
    '''
    core.send(
        user_input    = user_input,
        reasoner      = reasoner,
        memory        = memory,
        location      = data.load_data()['config']['location']
    )
    port = str(data.load_data()['context'][-1]).split('//')
    print(port[3])
    if port[4] != '这条回复没有使用分割回复':
        print(port[4])
    if port[5] != '这条回复没有添加长期记忆':
        print(f'\033[36m{port[5]}，已经记住了w\033[m')


if __name__ == '__main__':
    typer.run(main)