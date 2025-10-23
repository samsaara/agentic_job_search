import asyncio
import json
from ast import literal_eval
from typing import Any, Dict

import click
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
        provider: str = "OPENROUTER",
        temperature: float = 0.3,
        wait_between_requests_seconds: float = 15,
        **payload_kwargs: Dict[str, Any],
    ):
        self.topic = topic
        self.scrape = scrape
        self.provider = provider
        self.temperature = temperature
        self.payload_kwargs = payload_kwargs

        self.llm = CustomLLM(self.provider, self.temperature, wait_between_requests_seconds)
        self.inputs = asyncio.run(prepare_inputs(self.scrape))
        # the message is split so that we can reuse this common message when we're not satisfied with LLM's response
        self._common_msg = " ".join(
            f"""
                Your output should be strictly adhering to the following JSON Format:
                {{ "jobs": Optional[List[{{ "title": str, "href": str, "location": Optional, "workplaceType": Optional}}] ] }}

                The `href` should contain URL of that respective job title ONLY, which is embedded in the same job listing entry.
                Do NOT make up any information that is NOT present in the user provided text nor mix up the URLs.
                Set an empty list as a value for `jobs` if there are no jobs in the blob of text related to "{self.topic}".
        """.split()
        )
        self._system_msg = {
            "role": "system",
            "content": " ".join(
                f"""
                You're a specialized bot excelled in web technologies (esp. HTML & CSS) and information retrieval from job postings.
                You only speak in JSON. The user will simply paste a blob of HTML text containing job listings and your goal is to
                extract all relevant information limited ONLY to topics: "{self.topic}" EXCLUSIVELY FROM THAT BLOB OF TEXT.

                {self._common_msg}
           """.split()
            ),
        }

    def _call_llm(self, messages):
        orig_msg = messages
        INVALID_RESPONSE = True
        model, msg = None, ""
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
                messages.extend(
                    [
                        {"role": "assistant", "content": resp},
                        {"role": "user", "content": f"{msg}\n\n{self._common_msg}"},
                    ]
                )
        return model

    def get_job_info_from_all_orgs(self):
        results = []
        for inp in self.inputs:
            scrape_fp = inp["file_path"]
            with open(scrape_fp) as fl:
                html_content = json.load(fl)["content"]

            model_dict = {
                "org": inp["org"],
                "url": inp["url"],
            }
            if html_content is not None:
                messages = [self._system_msg, {"role": "user", "content": html_content}]
                # We call the LLM without giving `org` & `url` to avoid hallucinations
                # We add them back once the results are fetched.
                model_dict.update(**self._call_llm(messages))
            else:
                log.warning(f"no HTML content found for org: {inp['org']}")
                model_dict.update({"jobs": []})

            model_dump = OrgsModel(**fix_job_listings(model_dict)).model_dump()
            store_jobs_info(model_dump)
            results.append(model_dump)

        store_final_jobs_report(results)


@click.command(context_settings=dict(show_default=True))
@click.option("--topic", default=JOB_TOPIC, help="the topic to filter the scraped job listings with")
@click.option("--scrape/--no-scrape", default=True, help="scrape org pages")
@click.option("--provider", default="OPENROUTER", help="LLM Provider. Add creds in '.env' file")
@click.option("--temperature", default=0.1, help="model temperature (0-sticks to instructions, 1-highly creative)")
@click.option(
    "--wait-between-requests-seconds",
    default=0.1,
    help="no. of seconds to wait between two successive calls to LLM. Pass `-1` to set it to None",
)
@click.option("--payload-kwargs", default=dict(), help="other kwargs to be passed to the requests payload")
def run(topic, scrape, provider, temperature, wait_between_requests_seconds, payload_kwargs):
    payload_kwargs = literal_eval(payload_kwargs)
    wait_between_requests_seconds = (
        None if wait_between_requests_seconds == float("-1") else float(wait_between_requests_seconds)
    )
    ps = ProgrammaticJobSearch(topic, scrape, provider, temperature, wait_between_requests_seconds, **payload_kwargs)
    ps.get_job_info_from_all_orgs()


if __name__ == "__main__":
    run()
