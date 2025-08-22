import os
import time
from typing import Any, Dict, List, Optional, Union

import backoff
import requests
from crewai import BaseLLM
from dotenv import load_dotenv

from src.config import log

load_dotenv()

def raw_llm_call(messages):
    model_name=os.environ['OPENROUTER_MODEL_NAME']
    api_key=os.environ['OPENROUTER_API_KEY']
    base_url=os.environ['OPENROUTER_API_BASE']
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    endpoint = f"{base_url}/chat/completions"

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    payload = {
        'model': model_name,
        'messages': messages,
    }

    resp = requests.post(endpoint, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


class OpenRouterLLM(BaseLLM):
    def __init__(
            self,
            model_name: str,
            api_key: str,
            base_url: str,
            requests_per_minute: int = 15,
            temperature: Optional[float] = None):
        super().__init__(model=model_name, temperature=temperature)
        self.api_key = api_key
        self.request_times = []
        self.requests_per_minute = requests_per_minute
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.endpoint = f"{base_url}/chat/completions"


    def _wait_for_rate_limit(self):
        now = time.time()
        # Remove timestamps older than 60 seconds
        self.request_times = [t for t in self.request_times if now - t < 60]

        # If at RPM limit, wait until we can send another
        if len(self.request_times) >= self.requests_per_minute:
            wait_secs = 60 - (now - self.request_times[0]) + 0.5
            log.info(f"RPM limit reached, sleeping {wait_secs:.1f}s")
            time.sleep(wait_secs)
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 60]

        # Record this request
        self.request_times.append(now)

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.HTTPError,
        max_tries=5, factor=3,
        giveup=lambda e: e.response is not None and e.response.status_code != 429,
    )
    def _perform_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the HTTP request, retrying on HTTPError 429 with exponential backoff.
        """
        response = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=60)
        response.raise_for_status()
        log.debug(f"{response.status_code=}")
        return response.json()

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[dict]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
    ) -> Union[str, Any]:
        log.debug('waiting for rate limit...')
        self._wait_for_rate_limit()
        # print(messages)
        log.debug('calling llm...')
        log.debug(f"{'='*30}\n\n{messages}\n\n{'='*30}")
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": messages,
        }
        if tools and self.supports_function_calling():
            payload["tools"] = tools

        resp = self._perform_request(payload)
        llm_resp = resp["choices"][0]["message"]["content"]
        log.debug(f"{'='*30}\n\n{llm_resp=}\n\n{'='*30}")
        return llm_resp

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return 262144
