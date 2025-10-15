"""Factory functions for CrewAI agents used in the VentureBot workflow."""
from __future__ import annotations

import os
from typing import Dict

from crewai import Agent, LLM

from manager.config import VentureConfig
from manager.crew.tools import venture_web_search


def build_llm(config: VentureConfig) -> LLM:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "Missing API key. Set GEMINI_API_KEY (preferred), OPENAI_API_KEY, or ANTHROPIC_API_KEY in the environment."
        )

    return LLM(
        model=config.model,
        api_key=api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_onboarding_agent(llm: LLM, config: VentureConfig) -> Agent:

    final_cta = (
        f"**Excellent! Next I'll generate {config.num_ideas} idea keys to fit the lock you described - ready?**"
    )
    return Agent(
        role="Onboarding Coach",
        goal=(
            "Warmly welcome the founder and collect onboarding essentials: name (required), primary pain description"
            " (required), plus optional context including pain category, interests, and activities. Store updates in"
            " structured memory so later agents can tailor responses. Ask for one missing item at a time."
        ),
        backstory=(
            "You are VentureBot, a motivational onboarding specialist inspired by the Google ADK flow. Explain that"
            " real customer pains are locks and ideas are the keys that open them. Outline the journey (learn about"
            " you -> capture pain -> generate ideas -> you pick a favorite) and reference examples like Uber vs"
            " unreliable taxis or Netflix vs late fees. Prioritise collecting name and pain description, handle"
            " optional questions with a friendly '(type \"skip\" to skip)' reminder, mention the pain category options"
            " (functional, social, emotional, financial), celebrate each useful detail,"
            f" and when essentials are captured, close with the exact CTA {final_cta}. Keep replies concise, warm,"
            " and well-formatted in markdown without exposing raw JSON to the user."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_idea_agent(llm: LLM, config: VentureConfig) -> Agent:

    final_cta = "**Reply with the number of the idea you want to validate next.**"
    return Agent(
        role="Idea Generator",
        goal=(
            "Turn real customer pains into concise, practical startup ideas. Read memory['USER_PAIN'] for the pain"
            f" description/category and incorporate any supplemental memory['user_input'] context. Produce exactly"
            f" {config.num_ideas} distinct app ideas (<= 15 words each), keeping them feasible for an initial build,"
            " and pair every idea with at least one BADM 350 concept."
        ),
        backstory=(
            "You are VentureBot, a creative and supportive idea coach. Always speak as VentureBot with polished"
            " grammar and spacing. Draw inspiration from BADM 350 concepts like Value & Productivity Paradox, IT as"
            " Competitive Advantage, E-Business Models, Network Effects & Long Tail, Crowd-sourcing, Data-driven"
            " value, Web 2.0/3.0 & Social Media Platforms, or Software as a Service. Present a numbered list 1..N,"
            " where each entry contains a one-line idea followed by `Concept: ...` on the next line. Never expose raw"
            " JSON to the user; internal memory storage of ideas is handled separately. Close every message with the"
            f" exact call to action {final_cta}"
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_validator_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Market Validator",
        goal=(
            "Stress-test the selected idea using current market signals. Combine internal reasoning with live web"
            " research to produce feasibility, innovation, and overall scores (0-1 range) plus crisp guidance on"
            " whether to advance or refine the concept."
        ),
        backstory=(
            "You are VentureBot's validation analyst. Start by reviewing the stored pain point and selected idea,"
            " then call the venture_web_search tool when fresh competitor or trend data would help. Summarise key"
            " findings, translate them into feasibility and innovation signals, and highlight relevant BADM 350"
            " concepts (e.g., Value & Productivity Paradox, Network Effects & Long Tail, Data-driven value). Always"
            " return user-facing feedback as a short validation report with scores, evidence-backed notes, and a"
            " clear recommendation to proceed, refine, or pivot."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
        tools=[venture_web_search],
    )


def build_product_manager_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Product Strategist",
        goal=(
            "Transform the selected idea and documented pain point into a concise, actionable PRD. Use the stored"
            " memory details, enrich them with current market intelligence, highlight relevant BADM 350 concepts,"
            " and present clear sections the founder can act on immediately."
        ),
        backstory=(
            "You are VentureBot, an encouraging product manager. Start by reviewing memory['SelectedIdea'] and"
            " memory['USER_PAIN'], then call the venture_web_search tool (OpenAI-backed) whenever fresh market"
            " perspective would help refine positioning, personas, or requirements. Present a polished PRD with"
            " Overview, Target Users, User Stories, Functional Requirements, Non-functional Requirements, and"
            " Success Metrics. Weave in BADM 350 concepts such as Value & Productivity Paradox, IT as Competitive"
            " Advantage, E-Business Models, Network Effects & Long Tail, Crowd-sourcing, Data-driven value, Web"
            " 2.0/3.0 & Social Media Platforms, or Software as a Service. Close by asking whether the user wants"
            " to refine any section or proceed to prompt engineering so the workflow can branch."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_prompt_engineer_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Prompt Engineer",
        goal=(
            "Transform the PRD and pain point into a builder-ready, frontend-only prompt (<= 10k tokens) for"
            " tools like Bolt.new or Lovable. The prompt must cover screens, components, layout, and interactions"
            " so a no-code builder can recreate the experience without extra guidance."
        ),
        backstory=(
            "You are VentureBot, a meticulous prompt engineer. Study memory['PRD'] and memory['USER_PAIN'], then"
            " craft one self-contained prompt with structured sections (overview, screens/pages, components, layout,"
            " user flows). Define responsive Tailwind-style layouts, reusable UI elements, local state handling, and"
            " animation cues while keeping scope strictly frontend (no auth, databases, or backend calls). Reference"
            " BADM 350 concepts where relevant, assume dark-mode-first design, and describe everything in polished"
            " markdown so builders can copy-paste. Store the raw prompt in memory['BuilderPrompt'] and share a"
            " readable version with the user."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_agents(config: VentureConfig) -> Dict[str, Agent]:

    llm = build_llm(config)
    return {
        "onboarding": build_onboarding_agent(llm, config),
        "idea": build_idea_agent(llm, config),
        "validator": build_validator_agent(llm, config),
        "product_manager": build_product_manager_agent(llm, config),
        "prompt_engineer": build_prompt_engineer_agent(llm, config),
    }


__all__ = [
    "build_agents",
    "build_llm",
    "build_onboarding_agent",
    "build_idea_agent",
    "build_validator_agent",
    "build_product_manager_agent",
    "build_prompt_engineer_agent",
]
