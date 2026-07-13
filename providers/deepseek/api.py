import requests
import config
import json

from providers.deepseek.pow import DeepSeekPoW

USER_TOKEN = config.get_key('deepseek_user_token')

def get_pow_response() -> str:
    response = requests.post(
        url='https://chat.deepseek.com/api/v0/chat/create_pow_challenge', 
        headers={'Authorization': f'Bearer {USER_TOKEN}'}, 
        json={'target_path': '/api/v0/chat/completion'}
    )

    return DeepSeekPoW().solve_challenge(response.json()['data']['biz_data']['challenge'])

class DeepSeekChatSession:
    def __init__(self: 'DeepSeekChatSession', chat_session_id: str) -> None:
        self.chat_session_id = chat_session_id
        self.parent_message_id = None
    
    @staticmethod
    def create() -> 'DeepSeekChatSession':
        response = requests.post(
            url='https://chat.deepseek.com/api/v0/chat_session/create', 
            headers={'Authorization': f'Bearer {USER_TOKEN}'}
        )

        return DeepSeekChatSession(response.json()['data']['biz_data']['id'])

    def chat_completion(self: 'DeepSeekChatSession', prompt: str, thinking_enabled: bool = False) -> str:
        response = requests.post(
            url='https://chat.deepseek.com/api/v0/chat/completion', 
            headers={'Authorization': f'Bearer {USER_TOKEN}', 'x-ds-pow-response': get_pow_response()},
            json={'chat_session_id': self.chat_session_id, 'parent_message_id': self.parent_message_id, 'prompt': prompt, 'search_enabled': True, 'thinking_enabled': thinking_enabled, 'ref_file_ids': []}
        )
        
        thinking_finished = False

        for line in response.text.splitlines():
            if not line.startswith('data: '):
                continue

            data = json.loads(line.split('data: ')[1])
            p = data.get('p')
            v = data.get('v', '')

            if p == 'response/content':
                content = v
                thinking_finished = True
            
            if isinstance(v, dict):
                self.parent_message_id = v['response']['message_id']
            
            if thinking_finished and not p:
                content += v
        
        return content

