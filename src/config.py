import logging
import os
from pathlib import Path

import yaml

# Change this to whatever you're interested in.
JOB_TOPIC = "Data Science or Machine/Deep Learning or NLP/LLMs or AI"

PROVIDER_CREDENTIALS_PATH = Path("creds.yaml")
SCRAPE_ORGS_PATH = Path("src/scrape/orgs.yaml")
SCRAPE_DOWNLOAD_PATH = Path("src/scrape/crawl")
JOBS_WRITE_PATH = Path("src/scrape/jobs")

for path in (SCRAPE_DOWNLOAD_PATH, JOBS_WRITE_PATH):
    path.mkdir(parents=True, exist_ok=True)


def get_logger(LOG_LEVEL="INFO"):
    LOG_PATH = Path("logs.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log = logging.Logger('agentic_search')
    log.setLevel(LOG_LEVEL)

    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    log.addHandler(file_handler)

    return log


log = get_logger('DEBUG')


def load_creds(provider):
    with open(PROVIDER_CREDENTIALS_PATH) as fl:
        creds = yaml.safe_load(fl)

    providers = creds.keys()

    # unset previous providers' credentials, if any
    _ = [os.environ.pop(key) for provider in providers for key in os.environ.keys() if key.startswith(provider)]

    if creds.get(provider):
        for k, v in creds[provider].items():
            os.environ[f'{provider}_{k}'] = str(v)
    else:
        log.error(f'LLM credentials for "{provider}" not found')
