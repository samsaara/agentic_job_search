# Agentic Job Search

Hola 👋!!! I created this pet project to play with [crewai](https://www.crewai.com) and to let agents help me keep an eye on jobs at organizations I like related to a topic of interest. You can also run it without agents as well. Hope it proves useful to you! 🙂

## How It Works

1. Given a list of organizations, it scrapes job listings and stores them locally under [src/scrape/crawl](src/scrape/crawl).
   - This part is async and can optionally be run only once (but it's recommended to run frequently as listings get updated often).
   - This is also done regardless of the approach (See [***Programmatic Job Search***](#programmatic-job-search) below)
2. Use an agent to read the scraped content and extract job info related to your topic of interest from those blobs of text.
   - Since our use case is not that complex, we only have one agent and one task which can be run async too.
   - You can use an LLM from a cloud provider that you have access to or that is running locally with ***ollama***.
3. Store extracted job information for each organization under [src/scrape/jobs/](src/scrape/jobs/) as `jobs_<org>.json` and generate a final report as `final_jobs_report_<time>.json`
   - You can add your own logic to tweak this further! Read these from pandas for further analysis or convert to markdown etc.

## Installation

### Pre-Requisites
- Python `>=3.10 <3.14` installed on your system.
- This project uses [uv](https://docs.astral.sh/uv/) for dependency management and package handling. So, install it with `pip` or `brew` or by other means.

### Instructions
Follow these steps to run the project locally after installing `uv`:
- run `uv tool install [--python 3.XX] crewai`
  - make sure `crewai` is now in your `$PATH` by running `which crewai` (I'm running `v0.175`)
- clone this repo and `cd` into it
- run `crewai install`
  - this automatically creates a virtual environment `.venv` in the repo and installs all dependencies
  - if you want to install any additional dependencies, run `uv add [--dev] <pkg>`
- copy `.env.example`, rename it to `.env` & populate it
  - you can get free credentials from [openrouter.ai](https://openrouter.ai/) / [AIML](https://aimlapi.com/)
  - if you want to do local LLM inferencing (with [ollama](https://ollama.com/)), look at [that](#ollama-model) section below.
- set the `JOB_TOPIC` in [config.py](src/config.py) to a topic of your interest. You get job reports just for roles related to just that.
  - You can also pass it as param when running `main.py` from CLI
- copy [orgs.yaml.example](src/scrape/orgs.yaml.example) & rename it to `orgs.yaml` to populate it with your favorites.
  - the `selector` key in the YAML file is used as CSS selector(s) with which you can filter for the exact content that you want to scrape so as not to download the entire webpage (which could be huge). Though its usage is *optional*, it is ***highly recommended***.
- the `max_rpm` (requests per minute) value, that sets the number of calls made to an LLM, is intentionally set to `1` by default to avoid accidental surge in calls. Make sure everything is set correctly, and change it to any higher number later.
  - You can also pass it as param when running `main.py` from CLI
  - If you have access to only free models on providers like openrouter/AIML, you get rate throttled pretty quickly because of the bursts of calls that crewAI makes if you run in async mode. So, instead go with non-async mode with `max_rpm` set or try [programmatic approach](#programmatic-job-search) and/or with [ollama](#ollama-model) instead.
- run `crewai run` & enjoy ✨


Optionally, you can also run `python src/agentic_job_search/main.py [--help]` for more info on params.


## Programmatic Job Search

You can also connect your favorite LLM running locally or on remote endpoint with [ollama](https://ollama.com/), for inferencing by skipping agentic workflow entirely.


Since we already have the scraped data, instead of asking the agents to (a) read the file with a tool (b) interpret it and extract info, we can directly tweak the `SYSTEM` prompt of our desired model and just pass the scraped content as input to receive the results in JSON.

Depending on your system config & the model used, the output can be relatively lot faster too.

1. set appropriate `kwargs` to the `run` function in [main.py](src/programmatic_job_search/main.py)
2. run `uv run run_manual` to get the job reports programmatically.

Optionally, you can also run `python src/programmatic_job_search/main.py [--help]` for more info on params.

_(You can also of course use an ollama model as your crew's LLM and run the agentic workflow. All you need to do is set the credentials in `.env` and change the provider to `OLLAMA`)_.

## Customizing

- Populate `.env` file with your credentials.
- You can add/edit agents & tasks config under [src/agentic_job_search/config](src/agentic_job_search/config/)
- Modify [crew.py](src/agentic_job_search/crew.py) to add your own logic, tools and specific args
- Modify [main.py](src/agentic_job_search/main.py) to add custom inputs for your agents and tasks

### ollama model

If you wish to go with local LLM inferencing approach:
1. install ollama
2. pull a model of your choice
3. populate the corresponding values in your `.env`.
4. run `ollama serve` to get the server running.
   - Most likely the server will be listening at `http://localhost:11434`. Check the logs and update this in the `.env` too


## Experimentation

You can run `uv run jupyter lab` to spin up a jupyter session with a notebook if you wish to play/test things.

## Troubleshooting
If in case you get `ModuleNotFoundError` when run with `uv run`, prefix the command with `PYTHONPATH='.'`. For example,
```bash
PYTHONPATH='.' uv run run_manual
```

## Cleanup

If you wish to delete the scraped content, look at `cleanup_*` functions under [src/utils](src/utils.py). Or you can directly run `uv run cleanup` which cleans up all the scraped content and generated job reports.


## Known Issues

I am facing a few issues which need further digging:

1. Unable to selectively override templates for agents.
     - When used a custom `system_template` for `Agent`, crewai doesn't insert the `{'role': 'system', 'content': ...}` but instead and puts the content of system & response templates altogether under `{'role': 'user', 'content':...}`.
    - I also was unable to overrride the response template as it doesn't showup even when providing it as an arguement to the agent. *I've observed this to be the leading cause to get blank/incorrect/hallucinated responses from (the free/less powerful) LLMs I've tested.

2. It's also not clear how to reliably control the no. of requests made to LLM with 'async kickoff'. Though `max_rpm` is exposed via `Crew` & `Agent`, the burst of calls that sometimes crewAI makes couldn't be controlled even when `max_rpm` set to `1`. One might have to use threading manually to lock and release over the LLM call method.
   - This might not be a problem, if you happen to have access to paid cloud provider. But for now, it's recommended to use the usual _sync_ kickoff if you use a free plan from providers like openrouter/AIML.

It could also be that these ain't bugs but my inexperience with crewai and insufficient documentation.
