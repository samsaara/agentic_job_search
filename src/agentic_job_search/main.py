import asyncio
import warnings

import click

# from tenacity import retry, stop_after_attempt, wait_exponential
from agentic_job_search.crew import AgenticJobSearch
from src.utils import prepare_inputs, store_final_jobs_report

warnings.filterwarnings("ignore") #, category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

# @retry(
#         wait=wait_exponential(2, min=4, max=300),
#         stop=stop_after_attempt(3)
# )
async def _run_async(scrape=True, **kwargs):
    try:
        inputs = await prepare_inputs(scrape)
        crew = AgenticJobSearch(**kwargs).crew()
        return await crew.kickoff_for_each_async(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew {e}")

def _run(scrape=True, **kwargs):
    try:
        inputs = asyncio.run(prepare_inputs(scrape))
        crew = AgenticJobSearch(**kwargs).crew()
        return crew.kickoff_for_each(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew {e}")

@click.command(context_settings=dict(show_default=True))
@click.option("--scrape/--no-scrape", default=True, help="scrape org pages")
@click.option('--async-run/--no-async-run', default=False, help='whether to run the crew in async mode')
@click.option("--provider", default='OLLAMA', help="LLM Provider. Add creds in '.env' file")
@click.option('--temperature', default=0.1, help='model temperature (0-sticks to instructions, 1-highly creative)')
@click.option('--max-rpm', default=1, help="Max LLM calls to make per minute. Pass `-1` to remove any limits (aka None)")
def run(scrape, async_run, provider, temperature, max_rpm):
    if int(max_rpm) == -1:
        max_rpm = None
    kwargs = {
        'provider': provider,
        'temperature': temperature,
        'max_rpm': max_rpm,
    }
    if async_run:
        results = asyncio.run(_run_async(scrape, **kwargs))
    else:
        results = _run(scrape, **kwargs)
    store_final_jobs_report(results)


if __name__ == "__main__":
    run()
