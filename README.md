# Agentic Job Search

Hola 👋!!! I created this pet project to play with [crewai](https://www.crewai.com) and to let agents help me keep an eye on jobs at organizations I like related to a topic of interest. You can also run it without agents as well. Hope it proves useful to you! 🙂

## How It Works

1. Scrape job listings and store them locally under [src/scrape/crawl](src/scrape/crawl).
   - This part is async and can optionally be run only once (but it's recommended to run frequently as listings get updated often).
   - This is also done regardless of the approach (See [***Programmatic Job Search***](#programmatic-job-search) below)
2. Use an agent to read the scraped content and extract job info related to your topic of interest from those blobs of text.
   - Since our use case is not that complex, we only have one agent but multiple tasks which can be run async too.
   - They work by default but feel free to check out their config files to tweak the params.
3. Store extracted job information for each organization under [src/scrape/jobs/](src/scrape/jobs/) as `<org>.json` and generate a final report as `final_job_report_<time>.json`
   - You can add your own logic to tweak this further! Read these from pandas for further analysis or convert to markdown etc.

## Installation

### Pre-Requisites
- Python `>=3.10 <3.14` installed on your system.
- This project uses [uv](https://docs.astral.sh/uv/) for dependency management and package handling. So, install it with `pip` or `brew` or by other means.

### Instructions
Follow these steps to run the project locally after installing `uv`:
- run `uv tool install [--python 3.XX] crewai`
  - make sure `crewai` is now in your `$PATH` by running `which crewai`
- clone this repo and `cd` into it
- run `crewai install`
  - this automatically creates a virtual environment `.venv` in the repo and installs all dependencies
  - if you want to install any additional dependencies, run `uv add [--dev] <pkg>`
- copy `.env.example`, rename it to `.env` & populate it
  - you can get free credentials from [openrouter.ai](https://openrouter.ai/) / [AIML](https://aimlapi.com/)
  - if you want to do local LLM inferencing (with [ollama](https://ollama.com/)), look at [***Programmatic Job Search***](#programmatic-job-search) section below.
- copy & rename [orgs.yaml.example](src/scrape/orgs.yaml.example) and populate with your favorites.
  - the `selector` key in the YAML file is used as CSS selector(s) with which you can filter for the exact content that you want to scrape so as not to download the entire webpage (which could be huge). Though its usage is *optional*, it is ***highly recommended***.
- run `crewai run` & enjoy ✨

## Programmatic Job Search

You can also connect your favorite LLM running locally or on remote endpoint with [ollama](https://ollama.com/), for inferencing by skipping agentic workflow entirely.

Since we already have the scraped data, instead of asking the agents to (a) read the file with a tool (b) interpret it and extract info, we can directly tweak the `SYSTEM` prompt of our desired model and just pass the scraped content as input to receive the results in JSON.

Depending on your system config & the model used, the output can be relatively lot faster too.


## Customizing

- Populate `.env` file with your credentials.
- You can add/edit agents & tasks config under [src/agentic_job_search/config](src/agentic_job_search/config/)
- Modify `src/agentic_job_search/crew.py` to add your own logic, tools and specific args
- Modify `src/agentic_job_search/main.py` to add custom inputs for your agents and tasks

### ollama model

If you wish to go with local LLM inferencing approach:
1. install ollama
2. pull a model of your choice
3. populate the corresponding values in your `.env`.
4. run `ollama serve` to get the server running.
   - Most likely the server will be listening at `http://localhost:11434`. Check the logs and update this in the `.env` too
5. set appropriate `kwargs` to the `run` function in [main.py](src/programmatic_job_search/main.py)
6. run `uv run run_manual` to get the job reports programmatically.


## Troubleshooting
If in case you get `ModuleNotFoundError` when run with `uv run`, prefix the command with `PYTHONPATH='.'`. For example,
```bash
PYTHONPATH='.' uv run run_manual
```

## Cleanup

If you wish to delete the scraped content, look at `cleanup_*` functions under [src/utils](src/utils.py). Or you can directly run `uv run cleanup`.
