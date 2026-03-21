import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from state import OrderState

# Load API keys from the .env file
load_dotenv()


# ─────────────────────────────────────────────
#  LLM Setup — Gemini (primary) + Groq (fallback)
#
#  We define two LLMs:
#    - gemini: primary, tried first
#    - groq:   fallback, used if gemini fails
#              (quota exceeded, rate limit, etc.)
#
#  .with_fallbacks([groq]) is a langchain-core
#  feature — if gemini raises any exception,
#  it automatically retries with groq.
#  No extra code needed in the node function.
# ─────────────────────────────────────────────

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

groq = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

# Primary LLM with Groq as fallback
llm = gemini.with_fallbacks([groq])


# ─────────────────────────────────────────────
#  ExtractedOrder — structured output schema
#
#  We use this Pydantic model to instruct the LLM:
#  "read the conversation and pull out these
#  three fields if the user has mentioned them."
#
#  All fields are Optional because the user may
#  not have provided everything yet.
# ─────────────────────────────────────────────

class ExtractedOrder(BaseModel):
    food_query: Optional[str] = None       # what the user wants to eat
    restaurant_name: Optional[str] = None  # preferred restaurant (if any)
    delivery_address: Optional[str] = None # delivery address


# For extraction we use groq directly (not the fallback chain)
# because .with_structured_output() + .with_fallbacks() together
# can behave unpredictably. Groq reliably supports structured output.
extractor = groq.with_structured_output(ExtractedOrder)


# ─────────────────────────────────────────────
#  System prompt for the chat LLM
#
#  This tells Gemini what its job is.
#  It guides the conversation to collect
#  exactly the 3 things we need before searching.
# ─────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are a friendly food ordering assistant.

Your job is to collect THREE pieces of information from the user:
1. What food they want to order (be specific — items and quantity if possible)
2. Which restaurant they want to order from (optional — they may not have a preference)
3. Their delivery address

Rules:
- Ask for one missing piece of information at a time, conversationally.
- If the user gives all three at once, acknowledge and confirm what you understood.
- Do NOT ask for payment details or anything else — just the 3 items above.
- Keep responses short and friendly.
"""


# ─────────────────────────────────────────────
#  gather_intent — the node function
#
#  In LangGraph, a node is just a Python function:
#    - Input:  the current state (OrderState)
#    - Output: a dict of fields to UPDATE in the state
#
#  LangGraph automatically merges the returned dict
#  into the existing state. You don't return the full
#  state — only what changed.
# ─────────────────────────────────────────────

def gather_intent(state: OrderState) -> dict:

    # Step 1: Prepend the system prompt to the conversation history.
    # `state["messages"]` contains all Human/AI messages so far.
    # SystemMessage is not shown to the user — it's instructions for the LLM.
    messages_with_system = [SystemMessage(content=CHAT_SYSTEM_PROMPT)] + state["messages"]

    # Step 2: Call Gemini with the full conversation.
    # The LLM reads the history and replies naturally to the user.
    ai_reply = llm.invoke(messages_with_system)

    # Step 3: Extract structured data from the conversation.
    # We pass the full conversation PLUS the AI's latest reply
    # so the extractor has the complete context.
    # The extractor returns an ExtractedOrder object (not text).
    extracted = extractor.invoke(messages_with_system + [ai_reply])

    # Step 4: Build the state update dict.
    # We always add the AI's reply to messages.
    # We only update a field if the extractor found a value for it
    # (don't overwrite existing data with None).
    update = {"messages": [ai_reply]}  # LangGraph appends this to existing messages

    if extracted.food_query:
        update["food_query"] = extracted.food_query

    if extracted.restaurant_name:
        update["restaurant_name"] = extracted.restaurant_name

    if extracted.delivery_address:
        update["delivery_address"] = extracted.delivery_address

    return update
