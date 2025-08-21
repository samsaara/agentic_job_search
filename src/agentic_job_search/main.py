#!/usr/bin/env python
import sys
import asyncio
import warnings

from pathlib import Path
from datetime import datetime

from agentic_job_search.crew import AgenticJobSearch
from src.scrape import scrape_orgs
from src.agentic_job_search import log


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    ORGS_FP = Path('src/agentic_job_search/config/orgs.yaml')
    DOWNLOAD_FP = Path('src/crawl/')
    DOWNLOAD_FP.mkdir(exist_ok=True)
    log.info(f"Scrapting for orgs at '{ORGS_FP}' and store at '{DOWNLOAD_FP}'")
    asyncio.run(scrape_orgs(ORGS_FP, DOWNLOAD_FP))

    try:
        AgenticJobSearch().crew().kickoff()
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        AgenticJobSearch().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AgenticJobSearch().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        AgenticJobSearch().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
