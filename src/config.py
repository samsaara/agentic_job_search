import logging
from pathlib import Path

JOB_TOPIC = "Data Science or Machine/Deep Learning or NLP/LLMs or AI"
LOG_LEVEL = 'DEBUG'


SCRAPE_ORGS_PATH = "src/scrape/orgs.yaml"
SCRAPE_DOWNLOAD_PATH = Path("src/scrape/crawl")
JOBS_WRITE_PATH = Path("src/scrape/jobs")

for path in (SCRAPE_DOWNLOAD_PATH, JOBS_WRITE_PATH):
    path.mkdir(parents=True, exist_ok=True)


file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(LOG_LEVEL)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

log = logging.Logger('agentic_search')
log.setLevel(LOG_LEVEL)
log.addHandler(file_handler)
