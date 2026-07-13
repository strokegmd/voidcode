import config
import time
import json
import os

from providers.deepseek.api import DeepSeekChatSession
from providers.qwen.api import QwenChatSession

WORKSPACE = os.getcwd()

def write_file(filename: str, content: str) -> None:
    with open(f'{WORKSPACE}\\{filename}', 'w', encoding='utf-8') as file:
        file.write(content)

def read_file(filename: str) -> str:
    with open(f'{WORKSPACE}\\{filename}', 'r', encoding='utf-8') as file:
        return file.read()

def list_files() -> str:
    listed_files = []

    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            listed_files.append(os.path.join(root, file))

    return '\n'.join(listed_files)

def create_directory(name: str) -> None:
    os.mkdir(f'{WORKSPACE}\\{name}')

def handle_response(session: DeepSeekChatSession | QwenChatSession, response: str) -> None:
    print()

    try:
        for line in response.splitlines():
            if line.startswith('VOIDCODE_TOOL_USE'):
                data = json.loads(line.split('VOIDCODE_TOOL_USE|')[1])
                if data['type'] == 'create_file':
                    write_file(data['filename'], '')
                    print(f'  [*] [tool use] created file with name {data["filename"]}')
                elif data['type'] == 'write_file':
                    write_file(data['filename'], data['content'])
                    print(f'  [*] [tool use] wrote {len(data["content"])} characters to file with name {data["filename"]}')
                elif data['type'] == 'read_file':
                    content = read_file(data['filename'])
                    if len(content) < 64000:
                        handle_response(session, session.chat_completion(f'Contents of {data["filename"]}:\n\n{content}', thinking_enabled=True))
                    else:
                        handle_response(session, session.chat_completion(f'{data["filename"]} is too big!', thinking_enabled=True))
                        
                    print(f'  [*] [tool use] read file {data["filename"]} ({len(content)} characters)')
                elif data['type'] == 'list_files':
                    files = list_files()
                    print(f'  [*] [tool use] listed {len(files)} files')
                    handle_response(session, session.chat_completion(f'Listing files in {os.getcwd()}:\n\n{files}', thinking_enabled=True))
                elif data['type'] == 'create_directory':
                    create_directory(data['name'])
                    print(f'  [*] [tool use] created directory with name {data["name"]}')
                elif data['type'] == 'jobs_finished':
                    # TODO: idk if im even doing this tool stuff correctly, but i hope yes :^)
                    return

                continue

            print(f'  {line}')

        handle_response(session, session.chat_completion('[Voidcode] Done.', thinking_enabled=True))
        print()
    except Exception as e:
        print(f'  [!] catched an exception while working: {e}\n')
        handle_response(session, session.chat_completion(f'[Voidcode] Catched an exception while working: {e}. Please retry your previous query.', thinking_enabled=True))

def handle_command(prompt: str) -> None:
    global WORKSPACE

    args = prompt.split()
    if args[0] == '/workspace':
        new_workspace = ' '.join(args).replace('/workspace ', '')
        WORKSPACE = new_workspace

        print(f'\n  [*] updated workspace to {new_workspace}\n')
    else:
        print(f'\n  [!] unknown command\n')

def main() -> None:
    print(f'\n    Voidcode\n    v1.0.00 test 2\n\n    Model: Qwen3.7-Max\n    Workspace: {WORKSPACE}\n')

    # if not config.get_key('deepseek_user_token'):
    #     print('    [!] Set DeepSeek User Token in config.json!')
    #     return

    print('    [*] Initializing chat session...')
    session = QwenChatSession.create()
    session.chat_completion(config.get_prompt(), thinking_enabled=True)
    print('    [*] Ready for your prompts!\n')

    while True:
        prompt = input('  > ')
        if prompt.startswith('/'):
            handle_command(prompt)
            continue

        handle_response(session, session.chat_completion(prompt, thinking_enabled=True))

if __name__ == '__main__':
    main()
