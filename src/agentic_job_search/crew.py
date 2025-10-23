from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, after_kickoff, agent, crew, task
from crewai_tools import FileReadTool

from src.config import log
from src.llms import CustomCrewLLM
from src.utils import OrgsModel, fix_job_listings, store_jobs_info

# Unfortunately, overriding with templates don't seem to fully work as expected.
# See README for known issues.
templates = {
    "system": """
        Hey, You are {role}. {backstory}\nYour mission is: {goal}
        You ONLY have access to the "{tool_names}" tool and should use it to read the file content.
        Here's more info about it:\n\n{tools}.
        IMPORTANT: Use the following format in your response:

        ```
        Thought: you should always think about what to do
        Action: the action to take, only one name of [{tool_names}], just the name, exactly as it's written.
        Action Input: the input to the action, just a simple JSON object, enclosed in curly braces, using \" to wrap keys and values.
        Observation: the result of the action
        ```

        Once all necessary information is gathered, return your response in JSON format requested by the user.
    """,
    "prompt": """This is what you have to do: {input}.""",
    "response": """{{ .Response }} Ensure your final answer contains only the content in the following format: {output_format}
        \nEnsure the final output does not include any code block markers like ```json or ```python.
    """,
}


@CrewBase
class AgenticJobSearch:
    """AgenticJobSearch crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self, provider: str = "OPENROUTER", temperature: float = 0.1, max_rpm=1):
        super().__init__()
        self.max_rpm = max_rpm  # to avoid rate throttling
        self.crew_llm = CustomCrewLLM(provider, temperature)

    @agent
    def job_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["job_researcher"],  # type: ignore[index]
            llm=self.crew_llm,
            tools=[FileReadTool()],
            max_rpm=self.max_rpm,
            use_system_prompt=True,
            # system_template=templates['system'],
            # prompt_template=templates['prompt'],
            # response_template=templates['response'],
        )

    @task
    def extract_job_info(self) -> Task:
        return Task(
            config=self.tasks_config["extract_job_info"],  # type: ignore[index]
            output_pydantic=OrgsModel,
        )

    @after_kickoff
    def process_outputs(self, results):
        try:
            model_dump = results.pydantic.model_dump()
            model_dump = OrgsModel(**fix_job_listings(model_dump)).model_dump()
        except Exception as e:
            log.exception(f"couldn't convert results into pydantic model:\n\n Error:{e}\n\n{results=}")
        return store_jobs_info(model_dump)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            output_log_file="logs.json",
            max_rpm=self.max_rpm,  # OpenRouter Free API Limitation is 20 RPM
        )
