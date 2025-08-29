import os
from time import sleep
from typing import Any, Dict, List, Optional, Union

import requests
from crewai import BaseLLM
from dotenv import load_dotenv

from src.config import log

load_dotenv()

"""
from tenacity import (
    retry,
    stop_after_delay,
    retry_if_exception_type,
    before,
    after
)

# 1. Module‐level lock
_call_lock = threading.Lock()

# 2. Timeout for acquiring the lock and for the call overall
_CALL_TIMEOUT = 30  # seconds


def _acquire_lock(retry_state):
    "Tenacity before-hook: try to acquire lock with timeout."
    acquired = _call_lock.acquire(timeout=_CALL_TIMEOUT)
    if not acquired:
        # If we cannot acquire within timeout, raise to abort
        raise RuntimeError(f"Timeout acquiring call lock after {_CALL_TIMEOUT}s")

def _release_lock(retry_state):
    "Tenacity after-hook: always release the lock."
    if _call_lock.locked():
        _call_lock.release()
 """


def _get_llm_creds(provider:str='OPENROUTER'):
    # replace with any provider you like but make sure you have stored its credentials in `.env`
    # They should all start with this prefix
    return {
        'model_name': os.environ.get(f"{provider}_MODEL_NAME"),
        'api_base': os.environ.get(f"{provider}_API_BASE"),
        'api_key': os.environ.get(f"{provider}_API_KEY"),
    }



class CustomCrewLLM(BaseLLM):
    def __init__(
            self,
            provider,
            temperature: float = 0.1,
            wait_between_requests_seconds:int = None
    ):
        self.provider = provider
        self.temperature = temperature
        self.llm = CustomLLM(provider, temperature, wait_between_requests_seconds)
        super().__init__(model=self.llm.model_name, temperature=self.temperature)

    """
    retry(
            # Stop retrying after overall timeout
            stop=stop_after_delay(_CALL_TIMEOUT),
            # Retry only on specific HTTP/network errors
            retry=retry_if_exception_type((requests.exceptions.RequestException, RuntimeError)),
            before=_acquire_lock,
            after=_release_lock,
            reraise=True
    )  """
    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
    ) -> Union[str, Any]:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        payload_kwargs = {'from_crew': True}
        if tools and self.supports_function_calling():
            payload_kwargs["tools"] = tools

        llm_resp = self.llm(messages, **payload_kwargs)
        return llm_resp

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        mappings = {
            'openai/gpt-oss-20b:free': 128000,
            'google/gemma3-12b-it': 128000,
            'qwen2.5-coder:14b': 32000,
        }
        if self.model not in mappings.keys():
            log.critical(f'context length for {self.model=} not found. Setting it to `4096`')
        return mappings.get(self.model, 4096)


class CustomLLM:
    def __init__(
        self,
        provider:str = 'OPENROUTER',
        temperature:float=0.1,
        wait_between_requests_seconds:int=5,
    ):
        self._provider = provider
        self.temperature = temperature
        self.wait = wait_between_requests_seconds
        self._set_creds()

    @property
    def provider(self):
        return self._provider

    def _set_creds(self):
        dc = _get_llm_creds(self.provider)
        self.model_name = dc.get('model_name')
        self.api_key = dc.get('api_key')
        self.api_base = dc.get('api_base')

    def change_provider(self, new_provider):
        self._provider = new_provider
        self._set_creds()

    def __call__(self, messages, **payload_kwargs):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        payload = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.temperature,
        }

        if self.provider != 'OLLAMA':
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            endpoint = f"{self.api_base}/chat/completions"
        else:
            headers = None
            endpoint = f"{self.api_base}/chat"
            from_crew = payload_kwargs.pop('from_crew', False)
            if not from_crew:
                # this forces resp. to be always in JSON which crewai doesn't like.
                payload.update({'format': 'json'})
            payload.update({'stream': False})

        payload.update(**payload_kwargs)

        log.debug('calling llm...')
        log.debug(f"{'/'*30}\n\n{messages}\n\n{'*'*30}")
        if self.wait:
            log.debug(f'sleeping for {self.wait} secs')
            sleep(self.wait)
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=1200)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            msg = "Make sure you're either connected to the internet or running ollama server if using the latter as provider"
            log.exception(msg)
            raise
        except Exception as e:
            log.exception(f"Error: {e}\n\nResponse: {resp.content.decode('utf8')}\n\n{resp.headers=}\n{resp.connection=}\n")
            raise

        if self.provider != 'OLLAMA':
            llm_resp = resp.json()["choices"][0]["message"]["content"]
        else:
            llm_resp = resp.json()['message']['content']
        log.debug(f"{'+'*30}\n\n{llm_resp}\n\n{'-'*30}")
        return llm_resp
