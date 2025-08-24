#!/usr/bin/env python
import asyncio
import json
import warnings
from time import time

# from tenacity import retry, stop_after_attempt, wait_exponential
from agentic_job_search.crew import AgenticJobSearch
from src.config import JOBS_WRITE_PATH, log
from src.utils import prepare_inputs

warnings.filterwarnings("ignore") #, category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

""" @retry(
        wait=wait_exponential(2, min=4, max=300),
        stop=stop_after_attempt(3)
) """
async def _run_async():
    try:
        inputs = await prepare_inputs(scrape=False)
        crew = AgenticJobSearch().crew()
        return await crew.kickoff_for_each_async(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run():
    results = asyncio.run(_run_async())
    FINAL_REPORT_PATH = f"{JOBS_WRITE_PATH}/final_jobs_report_{int(time())}.json"
    log.debug(f"writing final jobs report to '{FINAL_REPORT_PATH}'")
    with open(FINAL_REPORT_PATH, 'w') as fl:
        json.dump(results, fl)
