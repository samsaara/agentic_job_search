"""
Scrape the webpages mentioned in `orgs.yaml` and store them in a folder
that agents will later access to filter for jobs you like.
"""

import asyncio
import json
from pathlib import Path

import click
import yaml
from playwright.async_api import TimeoutError as playWrightTimeoutError
from playwright.async_api import async_playwright

from src.config import SCRAPE_DOWNLOAD_PATH, SCRAPE_ORGS_PATH, log


def get_orgs_info(orgs_yml_filepath=SCRAPE_ORGS_PATH):
    with open(Path(orgs_yml_filepath)) as fl:
        orgs_cfg = yaml.safe_load(fl)

    orgs = [
        {
            "org": org_name,
            "url": vals["url"],
            "selector": vals.get("selector"),
        }
        for org_name, vals in orgs_cfg.items()
    ]

    return orgs


async def scrape_orgs(max_concurrence=5, timeout_s=15):
    log.info("scraping organizations' data...")

    orgs = get_orgs_info()
    semaphore = asyncio.Semaphore(max_concurrence)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        unscraped_orgs = []

        async def scrape(*, org, url, selector):
            log.debug(f'scraping org: "{org}"')
            async with semaphore:
                page = await context.new_page()
                try:
                    content = None
                    await page.goto(url)
                    if selector is not None:
                        await page.wait_for_selector(selector, timeout=timeout_s * 1000)
                        entries = await page.query_selector_all(selector)
                        if len(entries):
                            content = " ".join([await entry.inner_html() for entry in entries])
                    else:
                        content = await page.content()
                except playWrightTimeoutError:
                    msg = f"Timeout trying to wait for selector. Couldn't scrape org: '{org}'"
                    log.exception(msg)
                    unscraped_orgs.append(org)
                except Exception as e:
                    msg = f"Couldn't scrape '{url}'. Exception: {e}"
                    log.exception(msg)
                    unscraped_orgs.append(org)
                finally:
                    await page.close()

                json_content = {"org": "_".join(org.lower().split()), "url": url, "content": content}
                with open(f"{SCRAPE_DOWNLOAD_PATH}/{org}.json", "w") as fp:
                    json.dump(json_content, fp, ensure_ascii=False)

        tasks = [scrape(**entry) for entry in orgs]
        await asyncio.gather(*tasks)

        if len(unscraped_orgs):
            log.warning(f"couldn't scrape for the followings orgs: {unscraped_orgs}")

        await context.close()
        await browser.close()


@click.command(context_settings=dict(show_default=True))
@click.option("--max-concurrence", default=5, help="max async jobs to run")
@click.option("--timeout-s", default=15, help="timeout in seconds waiting for selector")
def run_scrape(max_concurrence, timeout_s):
    import asyncio

    asyncio.run(scrape_orgs(int(max_concurrence), float(timeout_s)))


if __name__ == "__main__":
    run_scrape()
