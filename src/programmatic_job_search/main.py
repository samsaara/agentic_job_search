import asyncio
import json
from typing import Any, Dict

from pydantic import ValidationError

from src.config import JOB_TOPIC, log
from src.llms import CustomLLM
from src.utils import (
    JobsModel,
    OrgsModel,
    clean_resp,
    fix_job_listings,
    prepare_inputs,
    store_final_jobs_report,
    store_jobs_info,
)


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
        self.payload_kwargs = payload_kwargs

        self.llm = CustomLLM(self.provider, self.temperature, wait_between_requests_seconds)
        self.inputs = asyncio.run(prepare_inputs(self.scrape))
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
    def _call_llm(self, messages):
        orig_msg = messages
        INVALID_RESPONSE = True
        while INVALID_RESPONSE:
            resp = self.llm(messages, **self.payload_kwargs)
            try:
                resp = clean_resp(resp)
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
            scrape_fp = inp['file_path']
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
            model_dump = OrgsModel(**fix_job_listings(model_dict)).model_dump()
            store_jobs_info(model_dump)
            results.append(model_dump)

        store_final_jobs_report(results)


def run():
    kwargs = {
        'scrape': False,
        'provider': 'OLLAMA',
        'temperature': 0.1,
        'wait_between_requests_seconds': None,
    }
    ps = ProgrammaticJobSearch(**kwargs)
    ps.get_job_info_from_all_orgs()


if __name__ == "__main__":
    run()
