import asyncio
import json
from time import time
from typing import Any, Dict
from urllib.parse import urlparse

from pydantic import ValidationError

from src.config import JOB_TOPIC, JOBS_WRITE_PATH, log
from src.llms import CustomLLM
from src.utils import JobsModel, OrgsModel, prepare_inputs


class ProgrammaticJobSearch:
    def __init__(
        self,
        topic=JOB_TOPIC,
        scrape: bool = True,
        provider: str = 'OPENROUTER',
        temperature: float = 0.3,
        wait_between_requests_seconds:int = 15,
        **payload_kwargs: Dict[str, Any]
    ):
        self.topic = topic
        self.scrape = scrape
        self.provider = provider
        self.temperature = temperature
        self.inputs = asyncio.run(prepare_inputs(self.scrape))
        self.llm = CustomLLM(self.provider, self.temperature, wait_between_requests_seconds)
        self.payload_kwargs = payload_kwargs
        self._common_msg = ' '.join(f"""
                Your output should be strictly adhering to the following JSON Format:
                {{ "jobs": Optional[List[{{ "title": str, "href": str, "location": Optional, "workplaceType": Optional}}] ] }}

                The `href` should contain URL of that respective job title ONLY, which is embedded in the same job listing entry.
                Do NOT make up any information that is NOT present in the user provided text nor mix up the URLs.
                Set an empty list as a value for `jobs` if there are no jobs in the blob of text related to "{self.topic}".
        """.split())
        self._system_msg = {
            'role': 'system',
            'content': ' '.join(f"""
                You're a specialized bot excelled in web technologies (esp. HTML & CSS) and information retrieval from job postings.
                You only speak in JSON. The user will simply paste a blob of HTML text containing job listings and your goal is to
                extract all relevant information limited ONLY to topics: "{self.topic}" EXCLUSIVELY FROM THAT BLOB OF TEXT.

                {self._common_msg}
            """.split()),
        }

    def _merge_urls(self, job_url:str, org_url:str) -> str:
        if not org_url.startswith('http'):
            org_url = 'http://'+org_url
        parsed_url = urlparse(org_url)
        root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        job_url = job_url if job_url.startswith('/') else '/'+job_url
        return root_url + job_url

    def _fix_job_links(self, json_resp):
        jobs = json_resp['jobs']
        if len(jobs):
            for entry in jobs:
                entry['href'] = self._merge_urls(entry['href'], json_resp['url'])
        return json_resp

    def _clean_resp(self, resp):
        resp = resp.strip()
        start = resp.find('{')
        if start != -1:
           end = resp[::-1].find('}')
           if end != -1:
               resp = resp[start:len(resp)-end]
        return resp

    def _call_llm(self, messages):
        orig_msg = messages
        INVALID_RESPONSE = True
        while INVALID_RESPONSE:
            resp = self.llm(messages, **self.payload_kwargs)
            try:
                resp = self._clean_resp(resp)
                log.debug(f"{': : '*30}\n\n{resp}\n\n{'; ; '*30}")
                model = json.loads(resp)
                _ = JobsModel(**model)
                INVALID_RESPONSE = False
            except ValidationError as e:
                msg = f"Failed to load response as JSON. {e}"
                log.exception(msg)
            except Exception as e:
                msg = f"Invalid response. Error {e}"
                log.exception(e)

            if INVALID_RESPONSE:
                messages = orig_msg
                messages.extend([
                    {
                        'role': 'assistant',
                        'content': resp
                    },
                    {
                        'role': 'user',
                        'content': f"{msg}\n\n{self._common_msg}"
                    }
                ])
        return model

    def get_job_info_from_all_orgs(self):
        results = []
        for inp in self.inputs:
            scrape_fp = inp['json_file_path']
            with open(scrape_fp) as fl:
                html_content = json.load(fl)['content']
            messages = [
                self._system_msg,
                {
                    'role': 'user',
                    'content': html_content
                }
            ]
            model_dict = self._call_llm(messages)
            model_dict.update({
                'org': inp['org'],
                'url': inp['url'],
            })
            model_dict = OrgsModel(**self._fix_job_links(model_dict)).model_dump()
            log.debug(f'writing jobs info of {inp["org"]}')
            with open(f"{JOBS_WRITE_PATH}/{inp['org']}.json", 'w') as fl:
                json.dump(model_dict, fl)
            results.append(model_dict)

        FINAL_REPORT_PATH = f"{JOBS_WRITE_PATH}/final_jobs_report_{int(time())}.json"
        log.debug(f"writing final jobs report to '{FINAL_REPORT_PATH}'")
        with open(FINAL_REPORT_PATH, 'w') as fl:
            json.dump(results, fl)


def run():
    kwargs = {
        'scrape': False,
        'provider': 'OLLAMA',
        'temperature': 0.1,
        'wait_between_requests_seconds': .1,
    }
    ps = ProgrammaticJobSearch(**kwargs)
    ps.get_job_info_from_all_orgs()


if __name__ == "__main__":
    run()
