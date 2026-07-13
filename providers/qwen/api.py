import requests
import config
import uuid
import time
import json

class QwenChatSession:
    def __init__(self: 'QwenChatSession', chat_id: str) -> None:
        self.chat_id = chat_id
        self.parent_id = None

    @staticmethod
    def get_headers() -> dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0', 
            'X-Request-Id': str(uuid.uuid4()), 
            'Cookie': f'token={config.get_key("qwen_token_cookie")}'
        }

    @staticmethod
    def create() -> 'QwenChatSession':
        response = requests.post(
            url='https://chat.qwen.ai/api/v2/chats/new',
            headers=QwenChatSession.get_headers(),
            json={}
        )

        return QwenChatSession(response.json()['data']['id'])

    def chat_completion(self: 'QwenChatSession', prompt: str, model: str = 'qwen3.7-max', thinking_enabled: bool = False) -> str:
        response = requests.post(
            url=f'https://chat.qwen.ai/api/v2/chat/completions?chat_id={self.chat_id}',
            headers=self.get_headers(),
            json = {
                'stream': True,
                'version': '2.1',
                'incremental_output': True,
                'chat_id': self.chat_id,
                'chat_mode': 'normal',
                'model': model,
                'parent_id': self.parent_id,
                'messages': [
                    {
                        'id': None,
                        'fid': str(uuid.uuid4()),
                        'parentId': self.parent_id,
                        'childrenIds': [str(uuid.uuid4())],
                        'role': 'user',
                        'content': prompt,
                        'user_action': 'chat',
                        'files': [],
                        'timestamp': int(time.time()),
                        'models': [model],
                        'model': model,
                        'chat_type': 't2t',
                        'feature_config': {
                            'thinking_enabled': thinking_enabled,
                            'output_schema': 'phase',
                            'research_mode': 'normal',
                            'auto_thinking': True,
                            'thinking_mode': 'Auto',
                            'thinking_format': 'summary',
                            'auto_search': True,
                        },
                        'extra': {'meta': {'subChatType': 't2t'}},
                        'sub_chat_type': 't2t',
                        'parent_id': self.parent_id,
                    },
                ],
                'timestamp': int(time.time()),
            }
        )

        content = ''
        for line in response.text.splitlines():
            if not line.startswith('data: '):
                continue

            data = json.loads(line.split('data: ')[1])
            if data.get('response.created'):
                self.parent_id = data['response.created']['response_id']

            if data.get('choices') and data['choices'][0]['delta']['phase'] == 'answer':
                content += data['choices'][0]['delta']['content']
        
        return content
