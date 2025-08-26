from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, after_kickoff, agent, crew, task
from crewai_tools import FileReadTool

from src.llms import CustomCrewLLM, _get_llm_creds
from src.utils import JobsModel, store_jobs_info


@CrewBase
class AgenticJobSearch:
    """AgenticJobSearch crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self, provider:str ='OPENROUTER', temperature:float = 0.1):
        super().__init__()
        self.temperature = temperature
        dc = _get_llm_creds(provider)
        self.llm = CustomCrewLLM(dc['model_name'], dc['api_key'], dc['api_base'], self.temperature)

    @agent
    def job_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['job_researcher'], # type: ignore[index]
            llm=self.llm
        )

    @task
    def extract_job_info(self) -> Task:
        return Task(
            config=self.tasks_config['extract_job_info'], # type: ignore[index]
            tools = [FileReadTool()],
            output_pydantic=JobsModel,
        )

    @after_kickoff
    def process_outputs(self, results):
        return store_jobs_info(results)

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
            max_rpm=1,  # OpenRouter Free API Limitation is 20 RPM
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
