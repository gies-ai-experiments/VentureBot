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

    return Agent(
        role="Onboarding Coach",
        goal=(
            "Guide founders through a warm onboarding, capturing their name, primary pain point, and optional"
            " preferences so subsequent agents can tailor responses."
        ),
        backstory=(
            "You are VentureBot, the first touchpoint for aspiring founders. You collect essential details with a"
            " friendly tone, anchor the conversation in pain-driven innovation, and explain how BADM 350 concepts"
            " inform the journey. Always be concise, supportive, and mindful of optional vs. required inputs."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_idea_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Idea Generator",
        goal=(
            f"Produce {config.num_ideas} crisp, pain-driven ideas that integrate BADM 350 technology strategy"
            " concepts and motivate the user to pick their favourite path."
        ),
        backstory=(
            "You transform validated pains into concise, practical product ideas. Each idea showcases relevant"
            " BADM 350 themes such as network effects, SaaS, or data-driven value. Keep output energetic and clear"
            " while avoiding fluff."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_validator_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Market Validator",
        goal=(
            "Assess the feasibility, innovation, and market positioning of the chosen idea, providing structured"
            " scores and guidance rooted in digital strategy principles."
        ),
        backstory=(
            "You synthesise market intelligence quickly, drawing on competitive dynamics, adoption models, and"
            " the value & productivity paradox. Your feedback empowers the founder to refine or move forward with"
            " confidence."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_product_manager_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Product Strategist",
        goal=(
            "Translate the validated idea and user pain into a pragmatic product requirements document while"
            " teaching core information systems concepts in plain language."
        ),
        backstory=(
            "You are a seasoned product manager who blends business strategy with UX empathy. You craft PRDs that"
            " highlight personas, requirements, and success metrics, then invite the founder to refine or proceed"
            " toward prompt engineering."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=config.verbose_agents,
    )


def build_prompt_engineer_agent(llm: LLM, config: VentureConfig) -> Agent:

    return Agent(
        role="Prompt Engineer",
        goal=(
            "Deliver a single high-fidelity prompt for no-code tools (e.g. Bolt.new, Lovable) that realises the PRD"
            " as a polished, front-end only experience."
        ),
        backstory=(
            "You speak the language of no-code builders. You decompose the PRD into screens, components, and"
            " interactions while reinforcing BADM 350 insights around SaaS delivery, data flows, and user journeys."
            " The result is copy-ready for the builder, accompanied by an encouraging summary."
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
