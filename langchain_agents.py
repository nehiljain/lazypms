import os
import asyncio
import logging
from typing import Dict, Tuple, Any
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import slack_api_tool, github_data_tool, github_analyzer_tool, human_feedback_interface, process_analytics_optimizer, exception_handler_model_updater
from context import slack_communication_guidelines, audience_specific_examples, release_notes_best_practices, internal_review_guidelines, system_architecture_docs
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt, agent5_prompt

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
class Config:
    RELEASE_NOTE_KEYWORDS = ["release notes", "changelog", "update", "new features"]
    SLACK_RATE_LIMIT = 1  # seconds
    GITHUB_RATE_LIMIT = 1  # seconds
    REQUIRED_ENV_VARS = ['anth_apikey', 'SLACK_API_TOKEN', 'GITHUB_API_TOKEN']

def validate_env_vars():
    for var in Config.REQUIRED_ENV_VARS:
        if var not in os.environ:
            raise EnvironmentError(f"Missing required environment variable: {var}")

validate_env_vars()

# Initialize the language model
anth_api_key = os.environ['anth_apikey']
llm = ChatAnthropic(temperature=0.3, anthropic_api_key=anth_api_key, model='claude-3-opus-20240229')

# Define tools for each agent
agent1_tools = [slack_api_tool, slack_communication_guidelines]
agent2_tools = [github_data_tool]
agent3_tools = [github_analyzer_tool, audience_specific_examples, release_notes_best_practices]
agent4_tools = [human_feedback_interface, internal_review_guidelines]
agent5_tools = [process_analytics_optimizer, exception_handler_model_updater, system_architecture_docs]

# Create ReAct agents
agent1 = create_react_agent(llm, agent1_tools, agent1_prompt)
agent2 = create_react_agent(llm, agent2_tools, agent2_prompt)
agent3 = create_react_agent(llm, agent3_tools, agent3_prompt)
agent4 = create_react_agent(llm, agent4_tools, agent4_prompt)
agent5 = create_react_agent(llm, agent5_tools, agent5_prompt)

# Create agent executors
agent1_executor = AgentExecutor(agent=agent1, tools=agent1_tools, verbose=True, handle_parsing_errors=True)
agent2_executor = AgentExecutor(agent=agent2, tools=agent2_tools, verbose=True, handle_parsing_errors=True)
agent3_executor = AgentExecutor(agent=agent3, tools=agent3_tools, verbose=True, handle_parsing_errors=True)
agent4_executor = AgentExecutor(agent=agent4, tools=agent4_tools, verbose=True, handle_parsing_errors=True)
agent5_executor = AgentExecutor(agent=agent5, tools=agent5_tools, verbose=True, handle_parsing_errors=True)

async def process_slack_message(message: str) -> str:
    try:
        input_data = {"input": message}
        output = await agent1_executor.ainvoke(input_data)
        return output["output"]
    except Exception as e:
        logger.error(f"Error in process_slack_message: {str(e)}")
        return ""

async def github_data_retrieval_agent(parsed_release_note_request: str) -> str:
    try:
        input_data = {"input": parsed_release_note_request}
        output = await agent2_executor.ainvoke(input_data)
        return output["output"]
    except Exception as e:
        logger.error(f"Error in github_data_retrieval_agent: {str(e)}")
        return ""

async def data_analysis_and_content_generation_agent(input_data: str) -> str:
    try:
        agent_input = {
            "input": input_data,
            "task": "Analyze the GitHub data, categorize changes, and generate audience-specific release note content."
        }
        output = await agent3_executor.ainvoke(agent_input)
        return output["output"]
    except Exception as e:
        logger.error(f"Error in data_analysis_and_content_generation_agent: {str(e)}")
        return ""

async def human_interaction_and_feedback_agent(generated_content: str) -> Tuple[str, str]:
    try:
        input_data = f"Review and process the following generated content: {generated_content}"
        output = await agent4_executor.ainvoke({"input": input_data})
        final_release_notes = output.get("output", "")
        process_feedback_data = output.get("process_feedback_data", "")
        return final_release_notes, process_feedback_data
    except Exception as e:
        logger.error(f"Error in human_interaction_and_feedback_agent: {str(e)}")
        return "", ""

async def process_management_optimization_agent(input_data: str) -> str:
    try:
        result = await agent5_executor.ainvoke({"input": input_data})
        return result['output']
    except Exception as e:
        logger.error(f"Error in process_management_optimization_agent: {str(e)}")
        return f"An error occurred: {str(e)}"

def is_release_note_query(message: str) -> bool:
    return any(keyword in message.lower() for keyword in Config.RELEASE_NOTE_KEYWORDS)

async def process_message(message: str):
    try:
        parsed_request = await process_slack_message(message)
        github_data = await github_data_retrieval_agent(parsed_request)
        generated_content = await data_analysis_and_content_generation_agent(github_data)
        final_release_notes, process_feedback = await human_interaction_and_feedback_agent(generated_content)
        await slack_api_tool.send_message(final_release_notes)
        optimization_result = await process_management_optimization_agent(process_feedback)
        logger.info(f"Process improvements and model updates: {optimization_result}")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

async def monitor_slack_channel():
    while True:
        try:
            new_messages = await slack_api_tool.get_new_messages()
            tasks = [process_message(message) for message in new_messages if is_release_note_query(message)]
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in monitor_slack_channel: {str(e)}")
        await asyncio.sleep(Config.SLACK_RATE_LIMIT)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_slack_channel())
    except KeyboardInterrupt:
        logger.info("Process terminated by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
