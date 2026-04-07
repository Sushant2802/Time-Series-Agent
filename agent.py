# agent.py
from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from config import MODEL_ID, MODEL_KWARGS, SYSTEM_PROMPT
from tools import TOOLS

# ✅ Use Converse API instead of ChatBedrock
llm = ChatBedrockConverse(
    model=MODEL_ID,
    **MODEL_KWARGS
)

checkpointer = MemorySaver()
store = InMemoryStore()

agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
    store=store,
    name="timeseries_agent",
    # debug=True
)


def run_query(query: str, thread_id: str = "sm123") -> str:
    # ✅ Get existing state (chat history)
    state = agent.get_state(
        config={"configurable": {"thread_id": thread_id}}
    )

    messages = state.values.get("messages", []) if state else []

    # ✅ Keep last 10 messages only (memory control)
    messages = messages[-10:]

    # ✅ Append new user message
    messages.append({
        "role": "user",
        "content": query
    })

    # ✅ Invoke agent
    response = agent.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}}
    )

    # ✅ Return last AI response
    return response["messages"][-1].content




# # agent.py
# from langgraph.prebuilt import create_react_agent
# from langchain_aws import ChatBedrock
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.store.memory import InMemoryStore
# from config import MODEL_ID, MODEL_KWARGS, SYSTEM_PROMPT
# from tools import TOOLS

# llm = ChatBedrock(model_id=MODEL_ID, model_kwargs=MODEL_KWARGS)

# checkpointer = MemorySaver()
# store = InMemoryStore()

# agent = create_react_agent(
#     model=llm,
#     tools=TOOLS,
#     prompt=SYSTEM_PROMPT,
#     checkpointer=checkpointer,
#     store=store,
#     name="timeseries_agent",
#     # debug=True
# )



# def run_query(query: str, thread_id: str = "sm123") -> str:
#     # Get existing state (chat history)
#     state = agent.get_state(config={"configurable": {"thread_id": thread_id}})
    
#     messages = state.values.get("messages", []) if state else []
#     messages = messages[-10:]

#     # Add new user message
#     messages.append({"role": "user", "content": query})

#     # Invoke agent
#     response = agent.invoke(
#         {"messages": messages},
#         config={"configurable": {"thread_id": thread_id}}
#     )

#     return response["messages"][-1].content