import os
from time import sleep
from typing import Any, Dict, List, Optional, Union

from crewai import BaseLLM
from litellm import APIConnectionError, completion

from src.config import load_creds, log

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


    # retry(
    #         # Stop retrying after overall timeout
    #         stop=stop_after_delay(_CALL_TIMEOUT),
    #         # Retry only on specific HTTP/network errors
    #         retry=retry_if_exception_type((requests.exceptions.RequestException, RuntimeError)),
    #         before=_acquire_lock,
    #         after=_release_lock,
    #         reraise=True
    # )
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

        # add this flag to let the custom llm know that it was being called by agentic workflow
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
        return int(os.environ[f"{self.provider}_CONTEXT_LENGTH"])


class CustomLLM:
    def __init__(
        self,
        provider:str = 'OPENROUTER',
        temperature:float = 0.1,
        wait_between_requests_seconds:int = 5,
    ):
        self._provider = provider
        self.temperature = temperature
        self.wait = wait_between_requests_seconds
        load_creds(provider)

    @property
    def provider(self):
        return self._provider

    def change_provider(self, new_provider):
        self._provider = new_provider
        load_creds(new_provider)

    def __call__(self, messages, **payload_kwargs):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        payload_kwargs.update({'stream': False, 'format': 'json', 'timeout': 300, 'temperature': self.temperature})
        if payload_kwargs.pop('from_crew', False):
            _ = payload_kwargs.pop('format')

        _prefix = bool(os.environ[f"{self.provider}_PREFIX"])
        MODEL_NAME = os.environ[f"{self.provider}_MODEL_NAME"]
        MODEL_NAME = f'{self.provider.lower()}/{MODEL_NAME}' if _prefix else MODEL_NAME

        log.debug('calling llm...')
        log.debug(f"{'/'*30}\n\n{messages}\n\n{'*'*30}")
        if self.wait:
            log.debug(f'sleeping for {self.wait} secs')
            sleep(self.wait)
        try:
            resp = completion(
                MODEL_NAME, messages, **payload_kwargs
            )
        except APIConnectionError as e:
            log.exception(e)
            raise
        except Exception as e:
            log.exception(e)
            raise

        llm_resp = resp.choices[0].message.content
        log.debug(f"Usage: {resp.usage.model_dump_json()}")

        log.debug(f"{'+'*30}\n\n{llm_resp}\n\n{'-'*30}\n\n")
        return llm_resp
