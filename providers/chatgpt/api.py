import requests
import config
import time
import uuid
import json

class ChatGPTChatSession:
    def __init__(self: 'ChatGPTChatSession', conversation_id: str | None = None) -> None:
        self.conversation_id = conversation_id
        self.parent_message_id = 'client-created-root'

    def chat_completion(self: 'ChatGPTChatSession', prompt: str) -> str:
        response = requests.post(
            url='https://chatgpt.com/backend-api/f/conversation',
            headers={'Authorization': f'Bearer {config.get_key("chatgpt_authorization_token")}'},
            json={
                'action': 'next',
                'conversation_id': self.conversation_id,
                'messages': [
                    {
                        'id': str(uuid.uuid4()),
                        'author': {'role': 'user'},
                        'create_time': int(time.time()),
                        'content': {
                            'content_type': 'text',
                            'parts': [prompt],
                        }
                    },
                ],
                'parent_message_id': self.parent_message_id,
                'model': 'auto'
            }
        )

        for line in response.text.splitlines():
            if not line.startswith('data: ') or '[DONE]' in line:
                continue

            data = json.loads(line.split('data: ')[1])
            print(data)
            
            if data.get('message', {}).get('status') == 'finished_successfully' and data['message']['author']['role'] == 'assistant':
                self.parent_message_id = data['message']['id']
                self.conversation_id = data['conversation_id']

                try:
                    return ''.join(data['message']['content']['parts'])
                except:
                    return ''
