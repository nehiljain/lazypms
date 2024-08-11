from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import json
import threading
import os

# Initialize the Slack client and app
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
GITHUB_PA_TOKEN = os.environ.get("GITHUB_PA_TOKEN")

# if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
#     raise ValueError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in environment variables")

slack_client = None #WebClient(token=SLACK_BOT_TOKEN)
app = None #App(token=SLACK_BOT_TOKEN)

class SlackAPIInput(BaseModel):
    input: str = Field(description='A JSON string containing the operation and its parameters. Example: {"operation": "send_message", "channel": "C1234567890", "message": "Hello, world!"}')

@tool("slack_api_tool", args_schema=SlackAPIInput, return_direct=False)
def slack_api_tool(input: str) -> str:
    """
    Enables real-time monitoring of Slack channels, reading and parsing of messages,
    sending messages, and distributing release notes to appropriate channels.
    """
    try:
        data = json.loads(input)
        operation = data.get('operation')

        if operation == 'send_message':
            return send_message(data.get('channel'), data.get('message'))
        elif operation == 'read_message':
            return read_message(data.get('channel'), data.get('ts'))
        elif operation == 'distribute_release_notes':
            return distribute_release_notes(data.get('channels'), data.get('notes'))
        elif operation == 'start_monitoring':
            return start_monitoring()
        elif operation == 'get_channel_history':
            return get_channel_history(data.get('channel'), data.get('limit', 100))
        else:
            return f"Unknown operation: {operation}"
    except json.JSONDecodeError:
        return "Invalid input: Not a valid JSON string"
    except KeyError as e:
        return f"Missing required field: {str(e)}"

def send_message(channel: str, message: str) -> str:
    try:
        result = slack_client.chat_postMessage(channel=channel, text=message)
        return f"Message sent successfully. Timestamp: {result['ts']}"
    except SlackApiError as e:
        return f"Error sending message: {str(e)}"

def read_message(channel: str, ts: str) -> str:
    try:
        result = slack_client.conversations_history(channel=channel, latest=ts, limit=1, inclusive=True)
        if result['messages']:
            return f"Message content: {result['messages'][0]['text']}"
        else:
            return "Message not found"
    except SlackApiError as e:
        return f"Error reading message: {str(e)}"

def distribute_release_notes(channels: list, notes: str) -> str:
    results = []
    for channel in channels:
        result = send_message(channel, notes)
        results.append(f"Channel {channel}: {result}")
    return "\n".join(results)

def get_channel_history(channel: str, limit: int = 100) -> str:
    try:
        result = slack_client.conversations_history(channel=channel, limit=limit)
        messages = result['messages']
        return json.dumps([{"text": msg["text"], "ts": msg["ts"]} for msg in messages])
    except SlackApiError as e:
        return f"Error getting channel history: {str(e)}"

# @app.event("message")
# def handle_message_events(body, logger):
#     logger.info(body)
#     message = body["event"]["text"]
#     channel = body["event"]["channel"]
#     user = body["event"]["user"]
    
#     # Process the message here
#     # For example, you could respond to specific keywords
#     if "hello" in message.lower():
#         send_message(channel, f"Hello <@{user}>! How can I assist you today?")

# def start_monitoring():
#     def run_socket_mode():
#         handler = SocketModeHandler(app, SLACK_APP_TOKEN)
#         handler.start()

#     # Start the Socket Mode handler in a separate thread
#     monitoring_thread = threading.Thread(target=run_socket_mode, daemon=True)
#     monitoring_thread.start()
#     return "Real-time monitoring started"

# # Initialize monitoring on import
# start_monitoring()


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from github import Github, GithubException
from datetime import datetime, timezone
import json
import re

class GitHubReleaseInput(BaseModel):
    input: str = Field(description="Requires a JSON string containing 'release_id'. Example: {\"release_id\": \"langchain-core==1.0.0\"}")

@tool("github_release_data_tool", args_schema=GitHubReleaseInput, return_direct=False)
def github_release_data_tool(input: str) -> str:
    """
    Retrieve GitHub release notes by ID and extract edited code, issues, and pull requests from that release note.
    Requires a JSON string containing 'release_id'. Example: {\"release_id\": \"langchain-core==1.0.0\"}
    """
    try:
        input_data = json.loads(input)
        #repo_name = input_data['repo']
        release_id = input_data['release_id']

        g = Github(GITHUB_PA_TOKEN)

        #real repo
        repo = g.get_repo('langchain-ai/langchain')

        #fake repo
        fake_repo = g.get_repo('nehiljain/langchain-by-lazypms')

        # Fetch the specific release
        release = repo.get_release(release_id)

        print(release)
        data = {
            "release_title": release.title,
            "release_body": release.body,
            "edited_code": [],
            "issues": [],
            "pull_requests": []
        }

        # Extract edited code from release notes
        code_blocks = re.findall(r'```[\s\S]*?```', release.body)
        for block in code_blocks:
            data["edited_code"].append(block.strip('`'))

        # Extract issues and pull requests from release notes
        issue_pattern = r'#(\d+)'
        issues_and_prs = re.findall(issue_pattern, release.body)

        for number in issues_and_prs:
            try:
                issue = repo.get_issue(int(number))
                if issue.pull_request:
                    data["pull_requests"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "author": issue.user.login,
                        "created_at": issue.created_at.isoformat(),
                    })
                else:
                    data["issues"].append({
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "author": issue.user.login,
                        "created_at": issue.created_at.isoformat(),
                        "closed_at": issue.closed_at.isoformat() if issue.closed_at else None
                    })
            except GithubException:
                # If we can't fetch the issue/PR, we'll skip it
                continue

        return json.dumps(data, indent=2)

    except GithubException as e:
        if e.status == 403:
            return json.dumps({"error": "Rate limit exceeded. Please wait and try again later."})
        elif e.status == 404:
            return json.dumps({"error": "Repository or release not found. Please check the repository name and release ID."})
        else:
            return json.dumps({"error": f"GitHub API error: {str(e)}"})
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid input JSON. Please check your input format."})
    except KeyError as e:
        return json.dumps({"error": f"Missing required field in input: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json
from github import Github
from github.GithubException import GithubException, RateLimitExceededException
from datetime import datetime, timedelta

class GitHubAnalyzerInput(BaseModel):
    input: str = Field(description="A JSON string containing 'repo' (string, format: 'owner/repo') and 'days' (optional int, default 30). Example: {\"repo\": \"langchain-ai/langchain\", \"days\": 7}")

@tool("github_analyzer_tool", args_schema=GitHubAnalyzerInput, return_direct=False)
def github_analyzer_tool(input: str) -> str:
    """Analyzes a GitHub repository to categorize and organize information about features, bug fixes, and other relevant changes."""
    try:
        input_data = json.loads(input)
        repo = input_data['repo']
        days = input_data.get('days', 30)

        g = Github(GITHUB_PA_TOKEN)  # Replace with your actual GitHub API token
        #real repo
        repo = g.get_repo('langchain-ai/langchain')

        #fake repo
        fake_repo = g.get_repo('nehiljain/langchain-by-lazypms')
        
        # Fetch recent commits
        since_date = datetime.now() - timedelta(days=days)
        commits = repo.get_commits(since=since_date)
        
        # Analyze commits and categorize changes
        features = []
        bug_fixes = []
        other_changes = []
        
        for commit in commits:
            message = commit.commit.message.lower()
            if "feature" in message or "feat" in message:
                features.append(commit.commit.message)
            elif "fix" in message or "bug" in message:
                bug_fixes.append(commit.commit.message)
            else:
                other_changes.append(commit.commit.message)
        
        # Prepare structured output
        analysis = {
            "repo": repo,
            "analysis_period": f"Last {days} days",
            "features": features,
            "bug_fixes": bug_fixes,
            "other_changes": other_changes,
            "summary": {
                "total_commits": len(features) + len(bug_fixes) + len(other_changes),
                "feature_count": len(features),
                "bug_fix_count": len(bug_fixes),
                "other_change_count": len(other_changes)
            }
        }
        
        return json.dumps(analysis, indent=2)

    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid input JSON"})
    except KeyError as e:
        return json.dumps({"error": f"Missing required key in input: {str(e)}"})
    except RateLimitExceededException:
        return json.dumps({"error": "GitHub API rate limit exceeded. Please try again later."})
    except GithubException as e:
        return json.dumps({"error": f"GitHub API error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from langchain.tools import HumanInputRun
import json

class FeedbackInput(BaseModel):
    input: str = Field(description='A JSON string containing content to be reviewed, feedback type, and optional previous feedback. Example: {"content": "AI is transforming industries.", "feedback_type": "accuracy and clarity", "previous_feedback": ""}')

class FeedbackManager:
    def __init__(self):
        self.feedback_history = []
        self.human_input = HumanInputRun()

    def collect_feedback(self, content, feedback_type, previous_feedback=""):
        prompt = f"Please review the following content for {feedback_type}:\n\n{content}\n"
        if previous_feedback:
            prompt += f"\nPrevious feedback: {previous_feedback}\n"
        prompt += "\nEnter your feedback:"
        
        feedback = self.human_input.run(prompt)
        
        approval = self.human_input.run("Do you approve this content? (yes/no):")
        
        self.feedback_history.append({
            "content": content,
            "feedback_type": feedback_type,
            "feedback": feedback,
            "approval": approval
        })
        
        return f"Feedback: {feedback}\nApproval: {approval}"

    def get_feedback_history(self):
        return self.feedback_history

feedback_manager = FeedbackManager()

@tool("human_feedback_interface", args_schema=FeedbackInput, return_direct=False)
def human_feedback_interface(input: str) -> str:
    """
    Manage interactions with human reviewers, including prompting for content checks,
    collecting and organizing feedback, and obtaining final approval. This tool handles
    content review requests, facilitates feedback collection, and maintains a feedback history.
    """
    try:
        input_data = json.loads(input)
        content = input_data['content']
        feedback_type = input_data['feedback_type']
        previous_feedback = input_data.get('previous_feedback', "")
        
        feedback = feedback_manager.collect_feedback(content, feedback_type, previous_feedback)
        
        return f"Feedback collected: {feedback}\n\nFeedback history: {feedback_manager.get_feedback_history()}"
    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please provide a valid JSON string."
    except KeyError as e:
        return f"Error: Missing required key in input JSON: {str(e)}"


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

class ProcessAnalyticsInput(BaseModel):
    input: str = Field(description='A JSON string containing process data and KPI thresholds. Example: {"process_data": {"throughput": [100, 120, 95, 110, 105], "error_rate": [0.01, 0.02, 0.015, 0.025, 0.02], "response_time": [0.5, 0.6, 0.55, 0.7, 0.65]}, "kpi_thresholds": {"throughput": 90, "error_rate": 0.03, "response_time": 0.8}}')

@tool("process_analytics_optimizer", args_schema=ProcessAnalyticsInput, return_direct=False)
def process_analytics_optimizer(input: str) -> str:
    """
    A tool for real-time monitoring, data analysis, and visualization of process performance.
    It tracks key performance indicators, identifies bottlenecks, and suggests optimizations to improve overall process efficiency.
    """
    try:
        # Parse input JSON
        data = json.loads(input)
        if 'process_data' not in data or 'kpi_thresholds' not in data:
            raise ValueError("Input must contain 'process_data' and 'kpi_thresholds'")
        
        process_data = data['process_data']
        kpi_thresholds = data['kpi_thresholds']

        # Convert input data to DataFrame
        df = pd.DataFrame(process_data)

        if df.empty:
            raise ValueError("Process data is empty")

        # Calculate KPIs
        kpi_results = {}
        for kpi, threshold in kpi_thresholds.items():
            if kpi in df.columns:
                kpi_results[kpi] = {
                    'mean': df[kpi].mean(),
                    'min': df[kpi].min(),
                    'max': df[kpi].max(),
                    'threshold': threshold,
                    'violations': sum(df[kpi] > threshold) if kpi != 'throughput' else sum(df[kpi] < threshold)
                }
            else:
                raise ValueError(f"KPI '{kpi}' not found in process data")

        # Identify bottlenecks
        bottlenecks = [kpi for kpi, result in kpi_results.items() if result['violations'] > 0]

        # Visualize data
        plt.figure(figsize=(12, 6))
        for kpi in kpi_results.keys():
            plt.plot(df.index, df[kpi], label=kpi)
            plt.axhline(y=kpi_thresholds[kpi], color='r', linestyle='--', label=f'{kpi} threshold')
        plt.legend()
        plt.title("Process Performance Over Time")
        plt.xlabel("Time")
        plt.ylabel("Value")
        
        # Save plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        # Generate report
        report = "Process Analytics and Optimization Report:\n\n"
        report += "KPI Summary:\n"
        for kpi, result in kpi_results.items():
            report += f"{kpi}:\n"
            report += f"  Mean: {result['mean']:.2f}\n"
            report += f"  Min: {result['min']:.2f}\n"
            report += f"  Max: {result['max']:.2f}\n"
            report += f"  Threshold: {result['threshold']:.2f}\n"
            report += f"  Violations: {result['violations']}\n\n"

        report += "Bottlenecks Identified:\n"
        report += ", ".join(bottlenecks) if bottlenecks else "No bottlenecks identified.\n"

        report += "\nOptimization Suggestions:\n"
        for bottleneck in bottlenecks:
            if bottleneck == 'throughput':
                report += f"- Investigate ways to increase {bottleneck} to meet or exceed the threshold.\n"
            else:
                report += f"- Investigate and optimize {bottleneck} to reduce threshold violations.\n"

        report += "\nProcess Performance Visualization:\n"
        report += f"data:image/png;base64,{plot_base64}\n"

        return report

    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please check the input format."
    except ValueError as ve:
        return f"Error: {str(ve)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json
import logging
from langchain.callbacks import StdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from datetime import datetime, timedelta

class ExceptionHandlerModelUpdaterInput(BaseModel):
    input: str = Field(description='A string that can be parsed to a dictionary containing "query" and optionally "feedback". Example: {"query": "What is the capital of France?", "feedback": "The answer was correct and helpful."}')

class FeedbackCollector:
    def __init__(self):
        self.feedback_data = []

    def collect_feedback(self, query, response, feedback):
        self.feedback_data.append({
            "query": query,
            "response": response,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })

    def get_feedback_data(self):
        return self.feedback_data

class PerformanceTracker(StdOutCallbackHandler):
    def __init__(self):
        super().__init__()
        self.total_tokens = 0
        self.total_time = 0
        self.query_count = 0
        self.last_update_time = datetime.now()

    def on_llm_end(self, response, **kwargs):
        self.total_tokens += response.llm_output['token_usage']['total_tokens']
        self.total_time += response.llm_output['run_time']
        self.query_count += 1

feedback_collector = FeedbackCollector()
performance_tracker = PerformanceTracker()

@tool("exception_handler_model_updater", args_schema=ExceptionHandlerModelUpdaterInput, return_direct=False)
def exception_handler_model_updater(input: str) -> str:
    """A system that detects and manages process exceptions such as insufficient data or API failures. It also collects performance data and feedback to facilitate AI model updates, improving accuracy and relevance over time."""
    try:
        input_data = json.loads(input)
        query = input_data['query']
        feedback = input_data.get('feedback', None)

        llm = OpenAI(temperature=0.7)
        prompt = "Human: {query}\nAI:"
        chain = LLMChain(llm=llm, prompt=prompt)
        
        try:
            result = chain.run(query, callbacks=[performance_tracker])
            
            if feedback:
                feedback_collector.collect_feedback(query, result, feedback)
            
            logging.info(f"Total tokens used: {performance_tracker.total_tokens}")
            logging.info(f"Total time taken: {performance_tracker.total_time}")
            logging.info(f"Queries processed: {performance_tracker.query_count}")
            
            if should_update_model():
                update_model(feedback_collector.get_feedback_data(), performance_tracker)
            
            return result
        
        except Exception as e:
            logging.error(f"An error occurred while processing the query: {e}")
            return f"An error occurred while processing your request: {str(e)}. Please try again later."
        
    except json.JSONDecodeError:
        return "Invalid input format. Please provide a valid JSON string."

def should_update_model():
    time_since_last_update = datetime.now() - performance_tracker.last_update_time
    return (performance_tracker.query_count >= 100 or 
            time_since_last_update >= timedelta(hours=24) or 
            performance_tracker.total_tokens >= 10000)

def update_model(feedback_data, performance_data):
    logging.info("Updating model based on collected feedback and performance data")
    # Implement model update logic here
    # For example:
    # 1. Analyze feedback data for common patterns or issues
    # 2. Adjust model parameters based on performance metrics
    # 3. Retrain or fine-tune the model using collected data
    # 4. Update the OpenAI API key or switch to a different model if necessary
    
    # Reset performance tracker after update
    performance_data.total_tokens = 0
    performance_data.total_time = 0
    performance_data.query_count = 0
    performance_data.last_update_time = datetime.now()
    
    # Clear feedback data after update
    feedback_collector.feedback_data.clear()
    
    logging.info("Model update completed")

logging.basicConfig(level=logging.INFO)
