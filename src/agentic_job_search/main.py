#!/usr/bin/env python
import asyncio
import warnings

# from tenacity import retry, stop_after_attempt, wait_exponential
from agentic_job_search.crew import AgenticJobSearch
from src.utils import prepare_inputs, store_final_jobs_report

warnings.filterwarnings("ignore") #, category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

""" @retry(
        wait=wait_exponential(2, min=4, max=300),
        stop=stop_after_attempt(3)
) """
async def _run_async(**kwargs):
    try:
        inputs = await prepare_inputs()
        crew = AgenticJobSearch(**kwargs).crew()
        return await crew.kickoff_for_each_async(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew {e}")

def _run(**kwargs):
    try:
        inputs = asyncio.run(prepare_inputs())
        crew = AgenticJobSearch(**kwargs).crew()
        return crew.kickoff_for_each(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew {e}")

def run():
    kwargs = {
        'provider': 'OLLAMA',
        'temperature': 0.1,
        'max_rpm': None,
    }
    # results = asyncio.run(_run_async(**kwargs))
    results = _run(**kwargs)
    store_final_jobs_report(results)
