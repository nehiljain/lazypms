import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from tools import slack_api_tool, github_release_data_tool, release_summary_scorer, human_feedback_interface, process_analytics_optimizer, exception_handler_model_updater
from context import slack_communication_guidelines, audience_specific_examples, release_notes_best_practices_tool, internal_review_guidelines, system_architecture_docs
from prompts import agent1_prompt, agent2_prompt, agent3_prompt, agent4_prompt, agent5_prompt
from langgraph.graph import StateGraph, END

from langchain_fireworks import ChatFireworks, FireworksEmbeddings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
class Config:
    RELEASE_NOTE_KEYWORDS = ["release notes", "changelog", "update", "new features"]
    REQUIRED_ENV_VARS = ['GITHUB_PA_TOKEN', 'SLACK_APP_TOKEN',"SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET", "FIREWORKS_API_KEY"]

# def validate_env_vars():
#     for var in Config.REQUIRED_ENV_VARS:
#         if var not in os.environ:
#             raise EnvironmentError(f"Missing required environment variable: {var}")

# validate_env_vars()

# Initialize the language model
anth_api_key = os.environ['ANTHROPIC_API_KEY']
llm = ChatAnthropic(temperature=0.3, anthropic_api_key=anth_api_key, model='claude-3-5-sonnet-20240620')
# llm = ChatFireworks(
#     api_key=os.getenv("FIREWORKS_API_KEY"),
#     model="accounts/fireworks/models/llama-v3p1-70b-instruct"
# )

# Define tools for each agent
agent1_tools = [slack_api_tool] #slack_communication_guidelines, slack_api_tool
agent2_tools = [github_release_data_tool]
agent3_tools = [release_summary_scorer, audience_specific_examples, release_notes_best_practices_tool] #github_analyzer_tool
agent4_tools = [human_feedback_interface, internal_review_guidelines]
agent5_tools = [process_analytics_optimizer, exception_handler_model_updater, system_architecture_docs]

# Create ReAct agents
agent1 = create_react_agent(llm, agent1_tools, agent1_prompt)
agent2 = create_react_agent(llm, agent2_tools, agent2_prompt)
agent3 = create_react_agent(llm, agent3_tools, agent3_prompt)
agent4 = create_react_agent(llm, agent4_tools, agent4_prompt)
agent5 = create_react_agent(llm, agent5_tools, agent5_prompt)

# Create agent executors
agent1_executor = AgentExecutor(agent=agent1, tools=agent1_tools, verbose=True, handle_parsing_errors=True, max_iterations=2)
agent2_executor = AgentExecutor(agent=agent2, tools=agent2_tools, verbose=True, handle_parsing_errors=True, max_iterations=2)
agent3_executor = AgentExecutor(agent=agent3, tools=agent3_tools, verbose=True, handle_parsing_errors=True, max_iterations=2)
agent4_executor = AgentExecutor(agent=agent4, tools=agent4_tools, verbose=True, handle_parsing_errors=True, max_iterations=2)
agent5_executor = AgentExecutor(agent=agent5, tools=agent5_tools, verbose=True, handle_parsing_errors=True, max_iterations=2)

# Define the StateGraph
from typing import TypedDict

class ReleaseNoteState(TypedDict):
    input: str
    parsed_request: Optional[str]
    github_data: Optional[str]
    generated_content: Optional[str]
    human_feedback: Optional[str]
    final_release_notes: Optional[str]
    process_feedback: Optional[str]
    exception_reports: List[str]
    process_metrics: Dict[str, Any]

# Define node functions
def slack_interaction_node(state: ReleaseNoteState) -> Dict[str, Any]:
    try:
        result = agent1_executor.invoke({"input": state["input"]})
        return {**state, "parsed_request": result["output"]}
    except Exception as e:
        logger.error(f"Error in slack_interaction_node: {str(e)}")
        return {**state, "exception_reports": state["exception_reports"] + [str(e)]}

def github_data_retrieval_node(state: ReleaseNoteState) -> Dict[str, Any]:
    try:
        if state["parsed_request"] is None:
            raise ValueError("No parsed request available")
        result = agent2_executor.invoke({"input": state["parsed_request"]})
        return {**state, "github_data": result["output"]}
    except Exception as e:
        logger.error(f"Error in github_data_retrieval_node: {str(e)}")
        return {**state, "exception_reports": state["exception_reports"] + [str(e)]}

def data_analysis_content_generation_node(state: ReleaseNoteState) -> Dict[str, Any]:
    try:
        if state["github_data"] is None:
            raise ValueError("No GitHub data available")
        result = agent3_executor.invoke({"input": state["github_data"]})
        return {**state, "generated_content": result["output"]}
    except Exception as e:
        logger.error(f"Error in data_analysis_content_generation_node: {str(e)}")
        return {**state, "exception_reports": state["exception_reports"] + [str(e)]}

def human_interaction_feedback_node(state: ReleaseNoteState) -> Dict[str, Any]:
    try:
        if state["generated_content"] is None:
            raise ValueError("No generated content available")
        result = agent4_executor.invoke({"input": state["generated_content"]})
        return {**state, "human_feedback": result["output"], "final_release_notes": result.get("final_release_notes")}
    except Exception as e:
        logger.error(f"Error in human_interaction_feedback_node: {str(e)}")
        return {**state, "exception_reports": state["exception_reports"] + [str(e)]}

def process_management_optimization_node(state: ReleaseNoteState) -> Dict[str, Any]:
    try:
        input_data = {
            "exception_reports": state["exception_reports"],
            "process_metrics": state["process_metrics"],
            "human_feedback": state["human_feedback"]
        }
        result = agent5_executor.invoke({"input": str(input_data)})
        return {**state, "process_feedback": result["output"]}
    except Exception as e:
        logger.error(f"Error in process_management_optimization_node: {str(e)}")
        return {**state, "exception_reports": state["exception_reports"] + [str(e)]}

# Define the graph
workflow = StateGraph(ReleaseNoteState)

# Add nodes
#workflow.add_node("slack_interaction", slack_interaction_node)
workflow.add_node("github_data_retrieval", github_data_retrieval_node)
workflow.add_node("data_analysis_content_generation", data_analysis_content_generation_node)
workflow.add_node("human_interaction_feedback", human_interaction_feedback_node)
workflow.add_node("process_management_optimization", process_management_optimization_node)

# Define conditional edges
def is_release_note_query(state: ReleaseNoteState) -> str:
    return "continue" if state["parsed_request"] else "end"

def needs_revision(state: ReleaseNoteState) -> str:
    return "revise" if state["human_feedback"] and "revision_needed" in state["human_feedback"].lower() else "finalize"

# Add edges
# workflow.add_conditional_edges(
#     "slack_interaction",
#     is_release_note_query,
#     {
#         "continue": "github_data_retrieval",
#         "end": END
#     }
# )
workflow.add_edge("github_data_retrieval", "data_analysis_content_generation")
workflow.add_edge("data_analysis_content_generation", "human_interaction_feedback")
workflow.add_conditional_edges(
    "human_interaction_feedback",
    needs_revision,
    {
        "revise": "data_analysis_content_generation",
        "finalize": "process_management_optimization"
    }
)
workflow.add_edge("process_management_optimization", END)

# Set entry point
#workflow.set_entry_point("slack_interaction")
workflow.set_entry_point("github_data_retrieval")

# Compile the graph
graph = workflow.compile()

# Main program
def run_agent():
    initial_state: ReleaseNoteState = {
        "input": "",
        "parsed_request": None,
        "github_data": None,
        "generated_content": None,
        "human_feedback": None,
        "final_release_notes": None,
        "process_feedback": None,
        "exception_reports": [],
        "process_metrics": {}
    }

    try:
        # new_messages = slack_api_tool.get_new_messages()
        new_messages = ["Please generate release notes for the latest github release langchain-openai==0.1.21"]
        for message in new_messages:
            if any(keyword in message.lower() for keyword in Config.RELEASE_NOTE_KEYWORDS):
                initial_state["parsed_request"] = message
                for step in graph.stream(initial_state):
                    print(f"Step: {step}")
                    if "final_release_notes" in step and step["final_release_notes"]:
                        print(step["final_release_notes"])

                        return step["final_release_notes"]
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
    
if __name__ == "__main__":
    run_agent()
