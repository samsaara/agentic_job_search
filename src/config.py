import logging

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

log = logging.Logger('agentic_search')
log.setLevel(logging.DEBUG)
log.addHandler(file_handler)


SCRAPE_ORGS_PATH = "src/scrape/orgs.yaml"
SCRAPE_DOWNLOAD_PATH="src/scrape/crawl"
JOB_TOPIC = "Data Science | Machine/Deep Learning | NLP/LLMs | AI"
