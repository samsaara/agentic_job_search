import asyncio
import json
import pickle
from glob import glob
from time import time
from typing import List, Optional

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, after_kickoff, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.config import JOB_TOPIC, SCRAPE_DOWNLOAD_PATH, log
from src.llms import CustomCrewLLM
from src.scrape.scrape import scrape_orgs

load_dotenv()



class Job(BaseModel):
    title: str = Field(..., description="Job Title")
    url: str = Field(..., description="URL of the Job application")
    location: Optional[str] = Field(..., description="Job Location")
    workplaceType: Optional[str] = Field(..., description="Way of Working (On-Site/Hybrid/Remote)")

class Jobs(BaseModel):
    org: str = Field(..., description="Name of the Organization")
    url: str = Field(..., description="URL of the Organization")
    jobs: List[Job]


@CrewBase
class AgenticJobSearch:
    """AgenticJobSearch crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def job_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['job_researcher'], # type: ignore[index]
            llm=CustomCrewLLM()
        )

    @task
    def extract_job_info(self) -> Task:
        return Task(
            config=self.tasks_config['extract_job_info'], # type: ignore[index]
            tools = [FileReadTool()],
            output_pydantic=Jobs,
        )

    def prepare_inputs(self):
        log.debug('preparing inputs')
        asyncio.run(scrape_orgs())
        text_filepaths = glob(f"{SCRAPE_DOWNLOAD_PATH}/*.json")[::-1]
        # random.shuffle(text_filepaths)
        inputs = []
        for fp in text_filepaths:
            with open(fp) as fl:
                content = json.load(fl)
            dc = {
                'org': content['org'],
                'url': content['url'],
                'json_file_path': str(fp),
                'topic': JOB_TOPIC,
            }
            inputs.append(dc)
        return inputs

    @after_kickoff
    def process_outputs(self, results):
        log.debug('processing outputs')
        with open(f'{int(time())}_final.pkl', 'wb') as fl:
            pickle.dump(results, fl)
        log.info('processed final outputs')

    @crew
    def crew(self) -> Crew:
        """Creates the AgenticJobSearch crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            output_log_file='logs.json',
            max_rpm=10,  # OpenRouter Free API Limitation is 20 RPM
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
