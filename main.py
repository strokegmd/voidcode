import subprocess
import config
import time
import os

from providers.deepseek.api import DeepSeekChatSession
from providers.chatgpt.api import ChatGPTChatSession
from providers.qwen.api import QwenChatSession

WORKSPACE = os.getcwd()
TOOL_USE_START_TAG = '<VOIDCODE_TOOL_USE>'
TOOL_USE_END_TAG = '</VOIDCODE_TOOL_USE>'

def format_tool_result(tool_name: str, result: str) -> str:
    return f'<VOIDCODE_TOOL_RESULT>\n{tool_name}\n{result}\n</VOIDCODE_TOOL_RESULT>\n\n'

def write_file(filename: str, content: str) -> None:
    with open(f'{WORKSPACE}\\{filename}', 'w', encoding='utf-8') as file:
        file.write(content)

def read_file(filename: str) -> str:
    with open(f'{WORKSPACE}\\{filename}', 'r', encoding='utf-8') as file:
        return file.read()

def list_files() -> str:
    listed_files = []

    for root, dirs, files in os.walk(WORKSPACE):
        for file in files:
            listed_files.append(os.path.join(root, file))

    return '\n'.join(listed_files)

def create_directory(name: str) -> None:
    os.mkdir(f'{WORKSPACE}\\{name}')

def execute_command(command: str) -> str:
    result = subprocess.run(command.split(), shell=True, capture_output=True)
    return result.stdout.decode()

def handle_command(prompt: str) -> None:
    global WORKSPACE

    args = prompt.split()
    if args[0] == '/workspace':
        WORKSPACE = ' '.join(args).replace('/workspace ', '')
        print(f'\n  [*] updated workspace to {WORKSPACE}\n')
    else:
        print(f'\n  [!] unknown command\n')

def create_chat_session(model: str) -> DeepSeekChatSession | ChatGPTChatSession | QwenChatSession | None:
    if model.lower() == 'deepseek':
        session = DeepSeekChatSession.create()

    elif model.lower() == 'chatgpt':
        session = ChatGPTChatSession()

    elif model.lower() in ['qwen3.7-plus', 'qwen3.7-max', 'qwen3.6-plus']:
        session = QwenChatSession.create()

    else:
        return None
    
    chat_completion(session, config.get_prompt())
    return session

def chat_completion(session: DeepSeekChatSession | ChatGPTChatSession | QwenChatSession, prompt: str) -> str:
    if isinstance(session, DeepSeekChatSession):
        return session.chat_completion(prompt, config.get_key('thinking_enabled'), config.get_key('search_enabled'))

    elif isinstance(session, ChatGPTChatSession):
        return session.chat_completion(prompt)

    elif isinstance(session, QwenChatSession):
        return session.chat_completion(prompt, config.get_key('model'), config.get_key('thinking_enabled'), config.get_key('search_enabled'))

def parse_tools(response: str) -> list[dict]:
    in_tool = False
    tool_lines = []
    parsed = []

    for line in response.splitlines():
        if line.strip() == TOOL_USE_START_TAG:
            in_tool = True
            tool_lines = []
            continue

        elif line.strip() == TOOL_USE_END_TAG:
            in_tool = False

            if tool_lines:
                tool_name = tool_lines[0].strip()
                args = tool_lines[1:]

                if tool_name == 'create_file':
                    parsed.append({'type': 'create_file', 'filename': args[0]})

                elif tool_name == 'write_file':
                    parsed.append({'type': 'write_file', 'filename': args[0], 'content': '\n'.join(args[1:])})

                elif tool_name == 'read_file':
                    parsed.append({'type': 'read_file', 'filename': args[0]})

                elif tool_name == 'list_files':
                    parsed.append({'type': 'list_files'})

                elif tool_name == 'create_directory':
                    parsed.append({'type': 'create_directory', 'directory_name': args[0]})

                elif tool_name == 'shell':
                    parsed.append({'type': 'shell', 'command': args[0]})

                elif tool_name == 'choice':
                    parsed.append({'type': 'choice', 'question': args[0], 'choices': '\n'.join(args[1:])})

            continue

        if in_tool:
            tool_lines.append(line)

        else:
            parsed.append({'type': 'ai_response', 'text': line})
    
    return parsed

def handle_response(session: DeepSeekChatSession | ChatGPTChatSession | QwenChatSession, response: str) -> None:
    if not response:
        return handle_response(session, chat_completion(session, format_tool_result('retry', 'Your response is empty. Probably, you included your response into your thinking block by accident.')))

    tools = parse_tools(response)
    tool_results = ''
    print()

    for tool in tools:
        try:
            if tool['type'] == 'ai_response':
                print('  ' + tool['text'])

            elif tool['type'] == 'create_file':
                write_file(tool['filename'], '')
                tool_results += format_tool_result('create_file', f'File {tool["filename"]} has been created.')
                print(f'  [*] [tool use] created file {tool["filename"]}')

            elif tool['type'] == 'write_file':
                write_file(tool['filename'], tool['content'])
                tool_results += format_tool_result('write_file', f'Wrote {len(tool["content"])} characters to {tool["filename"]}')
                print(f'  [*] [tool use] wrote {len(tool["content"])} characters to {tool["filename"]}')

            elif tool['type'] == 'read_file':
                content = read_file(tool['filename'])
                tool_results += format_tool_result('read_file', content)
                print(f'  [*] [tool use] read file {tool["filename"]} ({len(content)} characters)')

            elif tool['type'] == 'list_files':
                files = list_files()
                tool_results += format_tool_result('list_files', files)
                print(f'  [*] [tool use] listed {len(files)} files')

            elif tool['type'] == 'create_directory':
                create_directory(tool['directory_name'])
                tool_results += format_tool_result('create_directory', f'Directory {tool["directory_name"]} has been created.')
                print(f'  [*] [tool use] created directory with name {tool["directory_name"]}')

            elif tool['type'] == 'shell':
                tool_results += format_tool_result('shell', execute_command(tool['command']))
                print(f'  [*] [tool use] executed command {tool["command"]}')

            elif tool['type'] == 'choice':
                tool_results += format_tool_result('choice', input(f'{tool["question"]}\n\n{tool["choices"]}\n\n> '))

        except Exception as e:
            print(f'  [!] catched an exception: {e}.')
            handle_response(session, chat_completion(session, f'Catched an exception: {e}. Please retry your previous query.')) # TODO: maybe a bug here
            continue

    print()
    if tool_results:
        return handle_response(session, chat_completion(session, tool_results))

def main() -> None:
    print(f'\n    Voidcode\n    v1.0.00 test 4\n\n    Model: {config.get_key('model')}\n    Workspace: {WORKSPACE}\n')

    session = create_chat_session(config.get_key('model'))
    if not session:
        print('  [!] Can\'t create chat session! Configure model correctly in config.json')
        
    print('    [*] Ready for your prompts!\n')

    while True:
        prompt = input('>   ')
        if prompt.startswith('/'):
            handle_command(prompt)
            continue

        handle_response(session, chat_completion(session, prompt))

if __name__ == '__main__':
    main()
