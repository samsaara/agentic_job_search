import logging
from pathlib import Path

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

log = logging.Logger('agentic_search')
log.setLevel(logging.DEBUG)
log.addHandler(file_handler)


SCRAPE_ORGS_PATH = "src/scrape/orgs.yaml"
JOB_TOPIC = "Data Science or Machine/Deep Learning or NLP/LLMs or AI"

SCRAPE_DOWNLOAD_PATH = Path("src/scrape/crawl")
JOBS_WRITE_PATH = Path("src/scrape/jobs")

for path in (SCRAPE_DOWNLOAD_PATH, JOBS_WRITE_PATH):
    path.mkdir(parents=True, exist_ok=True)
