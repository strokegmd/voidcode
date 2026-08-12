import requests
import config
import json

from providers.deepseek.pow import DeepSeekPoW

USER_TOKEN = config.get_key('deepseek_user_token')

def get_pow_response() -> str:
    response = requests.post(
        url='https://chat.deepseek.com/api/v0/chat/create_pow_challenge', 
        headers=DeepSeekChatSession.get_headers(), 
        json={'target_path': '/api/v0/chat/completion'}
    )

    return DeepSeekPoW().solve_challenge(response.json()['data']['biz_data']['challenge'])

class DeepSeekChatSession:
    def __init__(self: 'DeepSeekChatSession', chat_session_id: str) -> None:
        self.chat_session_id = chat_session_id
        self.parent_message_id = None

    @staticmethod
    def get_headers(solve_challenge: bool = False) -> dict[str, str]:
        headers = {
            'Authorization': f'Bearer {USER_TOKEN}', 
            'x-client-platform': 'web',
            'x-client-version': '2.3.0',
        }

        if solve_challenge:
            headers['x-ds-pow-response'] = get_pow_response()
        
        return headers
    
    @staticmethod
    def create() -> 'DeepSeekChatSession':
        response = requests.post(
            url='https://chat.deepseek.com/api/v0/chat_session/create', 
            headers=DeepSeekChatSession.get_headers()
        )

        return DeepSeekChatSession(response.json()['data']['biz_data']['chat_session']['id'])

    def chat_completion(self: 'DeepSeekChatSession', prompt: str, thinking_enabled: bool = False, search_enabled: bool = False) -> str:
        response = requests.post(
            url='https://chat.deepseek.com/api/v0/chat/completion', 
            headers=self.get_headers(solve_challenge=True),
            json={
                'chat_session_id': self.chat_session_id, 
                'parent_message_id': self.parent_message_id, 
                'prompt': prompt, 
                'search_enabled': search_enabled, 
                'thinking_enabled': thinking_enabled, 
                'ref_file_ids': []
            }
        )
        
        thinking_finished = not thinking_enabled
        content = ''

        for line in response.text.splitlines():
            if not line.startswith('data: '):
                continue

            data = json.loads(line.split('data: ')[1])
            response_message_id = data.get('response_message_id')
            p = data.get('p')
            v = data.get('v')

            if p == 'response/fragments' and v[0]['type'] == 'RESPONSE':
                thinking_finished = True
                content = v[0]['content']

            if p == 'response/fragments/-1/content' and thinking_finished:
                content += v

            if v and isinstance(v, str) and thinking_finished and not p:
                content += v
            
            if response_message_id:
                self.parent_message_id = response_message_id

        return content
