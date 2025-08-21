"""
Scrape the webpages mentioned in `orgs.yaml` and store them in a folder
that agents will later access to filter for jobs you like.
"""

import yaml
import asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from src.agentic_job_search import log


def scrape_content(url:str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # with browser.new_context() as context:
        page = browser.new_page()
        page.goto(url)
        content = page.content()

    # org = '_'.join(org.split())
    # file_name = Path(f'/tmp/{org}.txt')
    # with open(file_name, 'w') as fl:
    #     fl.write(content)
    # log.info(f'scraped content written to "{file_name}"')
    # log.info(f'scraped content written to "{file_name}"')
    return content


async def scrape_orgs(orgs_fp:Path, download_fp:Path, max_concurrence=5):

    with open(orgs_fp) as fl:
        orgs_cfg = yaml.safe_load(fl)

    orgs = [
        {
            'org'   : org_name,
            'url'   : url,
        } for org_name, url in orgs_cfg['orgs'].items()
    ]

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
                with open(f"{download_fp}/{org}.txt", "w") as fp:
                    fp.write(content)

        tasks = [scrape(entry['url'], entry['org']) for entry in orgs]
        await asyncio.gather(*tasks)

        await context.close()
        await browser.close()
