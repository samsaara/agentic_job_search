"""
Scrape the webpages mentioned in `orgs.yaml` and store them in a folder
that agents will later access to filter for jobs you like.
"""

import yaml
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from src.config import log, SCRAPE_ORGS_PATH, SCRAPE_DOWNLOAD_PATH


def get_orgs_info(orgs_yml_filepath=SCRAPE_ORGS_PATH):
    with open(Path(orgs_yml_filepath)) as fl:
        orgs_cfg = yaml.safe_load(fl)

    orgs = [
        {
            'org'   : org_name,
            'url'   : url,
        } for org_name, url in orgs_cfg['orgs'].items()
    ]

    return orgs



async def scrape_orgs(max_concurrence=5):

    orgs = get_orgs_info()
    semaphore = asyncio.Semaphore(max_concurrence)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        async def scrape(url, org):
            log.debug(f'scraping "{url}" of org: "{org}"')
            async with semaphore:
                page = await context.new_page()
                try:
                    await page.goto(url)
                    content = await page.content()
                    org = '_'.join(org.split())
                finally:
                    await page.close()

                json_content = {
                    'org': org,
                    'url': url,
                    'content': content
                }
                with open(f"{SCRAPE_DOWNLOAD_PATH}/{org}.json", "w") as fp:
                    json.dump(json_content, fp, ensure_ascii=False)

        tasks = [scrape(entry['url'], entry['org']) for entry in orgs]
        await asyncio.gather(*tasks)

        await context.close()
        await browser.close()
