import logging
from pathlib import Path

# Change this to whatever you're interested in.
JOB_TOPIC = "Data Science or Machine/Deep Learning or NLP/LLMs or AI"

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


log = get_logger()


