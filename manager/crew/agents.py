"""Factory functions for CrewAI agents used in the VentureBot workflow."""
from __future__ import annotations

import os
from typing import Dict

from crewai import Agent, LLM

from manager.config import VentureConfig


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

    return Agent(
        role="Idea Generator",
        goal=(
            f"Produce exactly {config.num_ideas} crisp, distinct, pain-driven app ideas (each ≤ 15 words), each"
            " explicitly tied to 1–2 BADM 350 concepts. Format the user-facing message as a numbered list and end"
            " with a clear CTA to pick an idea by number."
        ),
        backstory=(
            "You transform pains and preferences into practical startup ideas. Inspired by the legacy ADK agent,"
            " you integrate concepts like Network Effects, SaaS, Data-driven value, or Web 2.0/3.0, and present"
            " clear, non-duplicative options that are feasible for a first build."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_validator_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Market Validator",
        goal=(
            "Assess the chosen idea with concise market reasoning. Provide feasibility, innovation, and overall"
            " scores with short notes, drawing on digital strategy principles and (where applicable) multi-"
            " dimensional considerations such as market opportunity and competition."
        ),
        backstory=(
            "You synthesise market intelligence quickly (legacy ADK-style) and communicate tradeoffs clearly."
            " While you may internally consider dimensions like market opportunity and competitive landscape,"
            " keep the final output aligned to the structured schema with brief, readable guidance."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_product_manager_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Product Strategist",
        goal=(
            "Translate the validated idea and pain into a pragmatic PRD: overview, personas, user stories,"
            " functional and non-functional requirements, and success metrics. Close with a bold CTA to refine"
            " or proceed."
        ),
        backstory=(
            "You are a seasoned PM (inspired by the legacy ADK PM agent). You mix business strategy with UX"
            " empathy. Keep the PRD concise, readable, and action-oriented, and invite refinement before moving"
            " to prompt engineering."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_prompt_engineer_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Prompt Engineer",
        goal=(
            "Deliver a single high-fidelity prompt for no-code tools (e.g., Bolt.new, Lovable) that realises the"
            " PRD as a polished, frontend-only experience with clear screens, flows, components, and interactions."
        ),
        backstory=(
            "You speak the language of builders (legacy ADK prompt engineer lineage). Break the PRD into explicit"
            " screens, user flows, UI components, and interaction logic. Keep to frontend scope, reinforce helpful"
            " BADM 350 insights, and produce a builder-ready prompt plus a short encouraging summary."
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
