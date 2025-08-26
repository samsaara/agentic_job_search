import json
import random
from glob import glob
from shutil import rmtree
from time import time
from typing import List, Optional

from pydantic import BaseModel, Field

from src.config import JOB_TOPIC, JOBS_WRITE_PATH, SCRAPE_DOWNLOAD_PATH, log
from src.scrape.scrape import scrape_orgs


class JobModel(BaseModel):
    title: str = Field(..., description="Job Title")
    href: str = Field(..., description="URL of the Job application")
    location: Optional[str] = Field(None, description="Job Location")
    workplaceType: Optional[str] = Field(None, description="Way of Working (On-Site/Hybrid/Remote)")


class JobsModel(BaseModel):
    jobs: List[JobModel]


class OrgsModel(BaseModel):
    org: str = Field(..., description="Name of the Organization")
    url: str = Field(..., description="URL of the Organization")
    jobs: List[JobModel]


async def prepare_inputs(scrape:bool=True):
    log.debug('preparing inputs')
    if scrape:
        await scrape_orgs()
    text_filepaths = glob(f"{SCRAPE_DOWNLOAD_PATH}/*.json")
    random.shuffle(text_filepaths)
    inputs = []
    for fp in text_filepaths:
        with open(fp) as fl:
            content = json.load(fl)
        dc = {
            'org': content['org'],
            'url': content['url'],
            'json_file_path': str(fp),
            'topic': JOB_TOPIC,
        }
        inputs.append(dc)
    return inputs


def store_jobs_info(results):
    model_dump = results.pydantic.model_dump()
    org = '_'.join(model_dump['org'].lower().split())
    log.debug(f'storing jobs found at "{org}"')
    with open(f'{JOBS_WRITE_PATH}/jobs_{org}.json', 'w') as fl:
        json.dump(model_dump, fl)
    return model_dump


def store_final_jobs_report(results):
    FINAL_REPORT_PATH = f"{JOBS_WRITE_PATH}/final_jobs_report_{int(time())}.json"
    log.debug(f"writing final jobs report to '{FINAL_REPORT_PATH}'")
    with open(FINAL_REPORT_PATH, 'w') as fl:
        json.dump(results, fl)


def cleanup_reports():
    """delete generated job reports"""
    log.warning('deleting all job reports generated so far!')
    rmtree(JOBS_WRITE_PATH)
    JOBS_WRITE_PATH.mkdir(parents=True)


def cleanup_crawled_content(delete_job_reports=True):
    log.warning('deleting crawled content scraped so far!')
    rmtree(SCRAPE_DOWNLOAD_PATH)
    SCRAPE_DOWNLOAD_PATH.mkdir(parents=True)
    if delete_job_reports:
        cleanup_reports()


def cleanup():
    cleanup_crawled_content()
