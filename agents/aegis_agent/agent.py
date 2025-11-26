import os
import logging
from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.planners import PlanReActPlanner
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel, Field

from .prompts import *
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "automated_answer_script_grading_app_v0"
USER_ID = "dev_user_01"
SESSION_ID_BASE = "loop_exit_tool_session"
GEMINI_MODEL = "gemini-2.5-flash"
STATE_INITIAL_TOPIC = "initial_topic"

STATE_CURRENT_DOC = "cuurent_doc"
STATE_CRITICISM = "criticism"
COMPLETION_PHASE = "No major issues found"

class AgentFeedback(BaseModel):
    score_justification: str
    improvement_advice: str

class Evaluation(BaseModel):
    initial_score: float
    final_score: float
    score_reasoning: str
    agent_feedback: AgentFeedback

class EvaluationOutput(BaseModel):
    evaluation: Evaluation

def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
  print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
  tool_context.actions.escalate = True
  # Return empty dict as tools should typically return JSON-serializable output
  return {}

arbiter_agent = Agent(
  name="arbiter_agent",
  description=arbiter_desc,
  model=GEMINI_MODEL,
  instruction=arbiter_prompt,
  planner=PlanReActPlanner()
)

scrutinizer_agent = Agent(
  name="scrutinizer_agent",
  description=scrutinizer_desc,
  model=GEMINI_MODEL,
  instruction=scrutinizer_prompt,
  planner=PlanReActPlanner()
)

validator_agent = Agent(
  name="validator_agent",
  description=validator_desc,
  model=GEMINI_MODEL,
  instruction=validator_prompt,
  planner=PlanReActPlanner(),
  tools=[exit_loop],
)

mentor_agent = Agent(
  name="mentor_agent",
  description=mentor_desc,
  model=GEMINI_MODEL,
  instruction=mentor_prompt,
  planner=PlanReActPlanner(),
  output_key="evaluation_output",
  output_schema=EvaluationOutput
)

refinement_loop = LoopAgent(
  name="refinement_loop",
  sub_agents = [
    scrutinizer_agent,
    validator_agent
  ],
  max_iterations=2
)

root_agent = SequentialAgent(
  name="iterative_grading_pipeline",
  sub_agents = [
    arbiter_agent,
    refinement_loop,
    mentor_agent
  ],
  description = "An automated grading pipeline that evaluates answer scripts through three sequential stages: initial assessment by the arbiter agent, iterative refinement through scrutinizer and validator agents, and final mentoring feedback. The pipeline ensures thorough evaluation and constructive feedback for educational assessment."
)