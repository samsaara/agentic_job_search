import html
import json
import random
from glob import glob
from shutil import rmtree
from time import time
from typing import List, Optional
from urllib.parse import urlparse

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


def merge_urls(job_url:str, org_url:str) -> str:
    if not org_url.startswith('http'):
        org_url = 'http://'+org_url
    parsed_url = urlparse(org_url)
    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    job_url = job_url if job_url.startswith('/') else '/'+job_url
    return root_url + job_url


def fix_job_listings(json_resp):
    jobs = json_resp['jobs']
    if len(jobs):
        for entry in jobs:
            entry['title'] = html.unescape(entry['title'])
            entry['href']  = merge_urls(entry['href'], json_resp['url'])
    return json_resp


def clean_resp(self, resp):
    resp = resp.strip()
    start = resp.find('{')
    if start != -1:
       end = resp[::-1].find('}')
       if end != -1:
           resp = resp[start:len(resp)-end]
    return resp


def store_jobs_info(model_dump):
    org = '_'.join(model_dump['org'].lower().split())
    fp = f'{JOBS_WRITE_PATH}/jobs_{org}.json'
    with open(fp, 'w') as fl:
        json.dump(model_dump, fl)
    log.info(f"stored jobs info for \"{model_dump['org']}\" at '{fp}'")


def store_final_jobs_report(results):
    FINAL_REPORT_PATH = f"{JOBS_WRITE_PATH}/final_jobs_report_{int(time())}.json"
    log.info(f"writing final jobs report to '{FINAL_REPORT_PATH}'")
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
