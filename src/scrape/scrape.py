"""
Scrape the webpages mentioned in `orgs.yaml` and store them in a folder
that agents will later access to filter for jobs you like.
"""

import asyncio
import json
from pathlib import Path

import yaml
from playwright.async_api import async_playwright

from src.config import SCRAPE_DOWNLOAD_PATH, SCRAPE_ORGS_PATH, log


def get_orgs_info(orgs_yml_filepath=SCRAPE_ORGS_PATH):
    with open(Path(orgs_yml_filepath)) as fl:
        orgs_cfg = yaml.safe_load(fl)

    orgs = [
        {
            'org'     : org_name,
            'url'     : vals['url'],
            'selector': vals.get('selector'),
        } for org_name, vals in orgs_cfg.items()
    ]

    return orgs



async def scrape_orgs(max_concurrence=5):

    orgs = get_orgs_info()
    semaphore = asyncio.Semaphore(max_concurrence)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        async def scrape(*, org, url, selector):
            log.debug(f'scraping "{url}" of org: "{org}"')
            async with semaphore:
                page = await context.new_page()
                try:
                    await page.goto(url)
                    if selector is not None:
                        await page.wait_for_selector(selector)
                        entries = await page.query_selector_all(selector)
                        if len(entries):
                            log.debug('getting inner html')
                            content = ' '.join([await entry.inner_html() for entry in entries])
                    else:
                        content = await page.content()
                except Exception as e:
                    msg = f"Couldn't scrape '{url}'. Exception: {e}"
                    log.exception(msg)
                    raise
                finally:
                    await page.close()

                json_content = {
                    'org': '_'.join(org.lower().split()),
                    'url': url,
                    'content': content
                }
                with open(f"{SCRAPE_DOWNLOAD_PATH}/{org}.json", "w") as fp:
                    json.dump(json_content, fp, ensure_ascii=False)

        tasks = [scrape(**entry) for entry in orgs]
        await asyncio.gather(*tasks)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_orgs())
