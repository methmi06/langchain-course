'''
import os

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

# 1. Initialize Tavily tool (make sure TAVILY_API_KEY is in your .env)
tavily_search = TavilySearch(
    max_results=5,
    topic="general",
)
tools = [tavily_search]

# 2. Initialize LLM via GitHub Models
llm = ChatOpenAI(
    model="gpt-4o-mini",  # or "gpt-4o" etc, supported by GitHub Models
    api_key=os.environ.get("GITHUB_TOKEN"),
    base_url="https://models.inference.ai.azure.com",
    temperature=0,
)

# 3. Create the agent (no hub, just a system prompt)
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=(
        "You are a helpful research assistant. "
        "Use the TavilySearch tool when you need up-to-date information from the web."
    ),
)

def main():
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Search for three job postings for an AI engineer in the Bay Area "
                        "on LinkedIn and list all of their details."
                    ),
                }
            ]
        }
    )

    print(result)

if __name__ == "__main__":
    main()



import os
from dotenv import load_dotenv

load_dotenv()

from langchain_classic import hub
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from prompt import REACT_PROMPT_WITH_FORMAT_INSTRUCTIONS
from schemas import AgentResponse


# ---- LLM ----
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("GITHUB_TOKEN"),
    base_url="https://models.inference.ai.azure.com",
    temperature=0,
)


# ---- Modern Tavily tool wrapped for classic agent ----
from langchain_tavily import TavilySearch

tavily_runnable = TavilySearch(max_results=5)

tavily_tool = TavilySearchResults(
    max_results=5,
    include_answer=True,
)

tools = [tavily_tool]



# ---- Prompt from LangChain Hub ----
react_prompt = hub.pull("hwchase17/react")

# (Optional) If you want a custom ReAct prompt with format instructions:
output_parser = PydanticOutputParser(pydantic_object=AgentResponse)
react_prompt_with_format_instructions = PromptTemplate(
    template=REACT_PROMPT_WITH_FORMAT_INSTRUCTIONS,
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
).partial(format_instructions=output_parser.get_format_instructions())

# ---- Agent + Executor ----
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt,  # or react_prompt_with_format_instructions
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)
extract_output = RunnableLambda(lambda x: x["output"])
parse_output = RunnableLambda(lambda x: output_parser.parse(x))

chain = agent_executor | extract_output | parse_output


def main():
    result = chain.invoke(
        {
            "input": (
                "Search for three job postings for an AI engineer in the Bay Area "
                "on LinkedIn, and list all of their details here."
            )
        }
    )
    print(result)


if __name__ == "__main__":
    main()

'''

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_classic import hub
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableLambda


# ---- LLM ----
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("GITHUB_TOKEN"),
    base_url="https://models.inference.ai.azure.com",
    temperature=0,
)


# ---- Tavily Tool ----
tavily_tool = TavilySearchResults(
    max_results=5,
    include_answer=True,
)
tools = [tavily_tool]


# ---- ReAct Prompt ----
react_prompt = hub.pull("hwchase17/react")


# ---- Agent ----
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)


# ---- RunnableLambda functions ----

# 1. Extract final output text from agent result dict
extract_output = RunnableLambda(lambda x: x["output"])

# 2. OPTIONAL: Extract only the job bullet points from the final answer
extract_jobs = RunnableLambda(
    lambda text: [
        line.strip()
        for line in text.split("\n")
        if line.strip().startswith(("1.", "2.", "3."))
    ]
)

# Chain: agent → extract output → extract job lines
chain = agent_executor | extract_output | extract_jobs


def main():
    result = chain.invoke(
        {
            "input": (
                "Search for three job postings for an AI engineer in the Bay Area "
                "on LinkedIn, and list all of their details here."
            )
        }
    )
    print("\n=== FINAL JOB LINES ===")
    print(result)
    print("========================\n")


if __name__ == "__main__":
    main()
