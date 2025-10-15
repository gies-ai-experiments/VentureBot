"""OpenAI-powered utilities and circuit breakers for VentureBot Crew agents."""
from __future__ import annotations

import json
import logging
import os
import re
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from crewai import tool
from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("OPENAI_MARKET_MODEL", "gpt-4.1-mini")
OPENAI_TIMEOUT = 45


class ValidationCircuitBreaker:
    """Simple circuit breaker to prevent repeated outbound failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.is_open = False

    def can_proceed(self) -> bool:
        if not self.is_open:
            return True
        if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
            logger.info("Circuit breaker timeout elapsed; resetting.")
            self.reset()
            return True
        return False

    def record_success(self) -> None:
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
        logger.debug("Circuit breaker recorded success; counters reset.")

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning("Circuit breaker opened after %s consecutive failures.", self.failure_count)
        else:
            logger.debug(
                "Circuit breaker failure count %s/%s.",
                self.failure_count,
                self.failure_threshold,
            )

    def reset(self) -> None:
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
        logger.info("Circuit breaker reset manually.")


validation_circuit_breaker = ValidationCircuitBreaker()


class MarketStage(Enum):
    """Lifecycle stage of the analysed market."""

    EMERGING = "emerging"
    GROWING = "growing"
    MATURE = "mature"
    DECLINING = "declining"


class CompetitorPosition(Enum):
    """Relative strength of a competitor."""

    LEADER = "market leader"
    CHALLENGER = "challenger"
    NICHE = "niche player"


@dataclass
class MarketScores:
    """Composite scores derived from market intelligence."""

    market_opportunity: float
    competitive_landscape: float
    execution_feasibility: float
    innovation_potential: float
    overall_score: float
    confidence: float


@dataclass
class MarketIntelligence:
    """Structured market intelligence."""

    tam_estimate: str
    growth_rate: str
    market_stage: MarketStage
    competitors: List[Dict[str, Any]]
    market_gaps: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    barriers: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class MarketAnalyzer:
    """Advanced market analysis engine."""

    def __init__(self) -> None:
        self.funding_patterns = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "k": 1_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
        }

    def analyze_market_intelligence(
        self, search_results: Dict[str, Any]
    ) -> Tuple[MarketScores, MarketIntelligence]:
        try:
            if "market_intelligence" in search_results:
                intelligence = self._parse_market_intelligence(search_results["market_intelligence"])
            else:
                intelligence = self._extract_basic_intelligence(search_results.get("results", []))

            scores = self._calculate_comprehensive_scores(intelligence, search_results)
            logger.info("Market analysis completed - Overall score: %.2f", scores.overall_score)
            return scores, intelligence
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error in market analysis: %s", exc)
            return self._default_scores(), self._default_intelligence()

    def _parse_market_intelligence(self, data: Dict[str, Any]) -> MarketIntelligence:
        market_size = data.get("market_size", {})
        tam_estimate = market_size.get("tam", "Unknown")
        growth_rate = market_size.get("growth_rate", "Unknown")
        stage_str = (market_size.get("market_stage", MarketStage.GROWING.value) or "growing").lower()
        try:
            market_stage = MarketStage(stage_str)
        except ValueError:
            market_stage = MarketStage.GROWING

        return MarketIntelligence(
            tam_estimate=tam_estimate,
            growth_rate=growth_rate,
            market_stage=market_stage,
            competitors=data.get("competitors", []),
            market_gaps=data.get("market_gaps", []),
            trends=data.get("trends", []),
            barriers=data.get("barriers", []),
            recommendations=data.get("recommendations", []),
        )

    def _extract_basic_intelligence(self, results: List[Dict[str, Any]]) -> MarketIntelligence:
        competitors: List[Dict[str, Any]] = []
        market_gaps: List[Dict[str, Any]] = []
        trends: List[Dict[str, Any]] = []
        barriers: List[Dict[str, Any]] = []

        for result in results:
            content = (result.get("content") or "").lower()
            title = result.get("title", "Result")

            if any(keyword in content for keyword in ["competitor", "company", "product", "leader"]):
                competitors.append(
                    {
                        "name": title,
                        "description": (result.get("content") or "")[:200],
                        "market_position": CompetitorPosition.CHALLENGER.value,
                        "funding": "Unknown",
                        "users": "Unknown",
                        "strengths": [],
                        "weaknesses": [],
                    }
                )

            if any(keyword in content for keyword in ["gap", "opportunity", "underserved", "need"]):
                market_gaps.append(
                    {
                        "gap": (result.get("content") or "")[:100],
                        "opportunity": "Market opportunity identified",
                        "difficulty": "medium",
                    }
                )

        return MarketIntelligence(
            tam_estimate="Data not available",
            growth_rate="Data not available",
            market_stage=MarketStage.GROWING,
            competitors=competitors,
            market_gaps=market_gaps,
            trends=trends,
            barriers=barriers,
            recommendations=[],
        )

    def _calculate_comprehensive_scores(
        self, intelligence: MarketIntelligence, search_results: Dict[str, Any]
    ) -> MarketScores:
        market_opportunity = self._score_market_opportunity(intelligence)
        competitive_landscape = self._score_competitive_landscape(intelligence)
        execution_feasibility = self._score_execution_feasibility(intelligence)
        innovation_potential = self._score_innovation_potential(intelligence)

        weights = {
            "market_opportunity": 0.3,
            "competitive_landscape": 0.25,
            "execution_feasibility": 0.25,
            "innovation_potential": 0.2,
        }
        overall_score = (
            market_opportunity * weights["market_opportunity"]
            + competitive_landscape * weights["competitive_landscape"]
            + execution_feasibility * weights["execution_feasibility"]
            + innovation_potential * weights["innovation_potential"]
        )

        confidence = self._calculate_confidence(intelligence, search_results)

        return MarketScores(
            market_opportunity=round(min(max(market_opportunity, 0.0), 1.0), 2),
            competitive_landscape=round(min(max(competitive_landscape, 0.0), 1.0), 2),
            execution_feasibility=round(min(max(execution_feasibility, 0.0), 1.0), 2),
            innovation_potential=round(min(max(innovation_potential, 0.0), 1.0), 2),
            overall_score=round(min(max(overall_score, 0.0), 1.0), 2),
            confidence=round(min(max(confidence, 0.0), 1.0), 2),
        )

    def _score_market_opportunity(self, intelligence: MarketIntelligence) -> float:
        score = 0.5
        tam = intelligence.tam_estimate.lower()
        if "billion" in tam or " b" in tam:
            score += 0.3
        elif "million" in tam or " m" in tam:
            score += 0.2
        elif tam not in {"unknown", "data not available"}:
            score += 0.1

        growth = intelligence.growth_rate.lower()
        if any(indicator in growth for indicator in ["15%", "20%", "25%", "30%", "high"]):
            score += 0.2
        elif any(indicator in growth for indicator in ["5%", "10%", "growing"]):
            score += 0.1

        if intelligence.market_stage == MarketStage.GROWING:
            score += 0.2
        elif intelligence.market_stage == MarketStage.EMERGING:
            score += 0.15
        elif intelligence.market_stage == MarketStage.DECLINING:
            score -= 0.2

        score += min(len(intelligence.market_gaps) * 0.1, 0.3)
        return score

    def _score_competitive_landscape(self, intelligence: MarketIntelligence) -> float:
        score = 1.0
        num_competitors = len(intelligence.competitors)

        if num_competitors >= 10:
            score -= 0.4
        elif num_competitors >= 5:
            score -= 0.3
        elif num_competitors >= 2:
            score -= 0.2
        elif num_competitors == 1:
            score -= 0.1

        strong_competitors = 0
        for competitor in intelligence.competitors:
            position = (competitor.get("market_position") or "").lower()
            funding = (competitor.get("funding") or "").lower()
            users = (competitor.get("users") or "").lower()
            if position == CompetitorPosition.LEADER.value:
                strong_competitors += 1
            if any(token in funding for token in ["billion", "million", "b", "m"]):
                strong_competitors += 1
            if any(token in users for token in ["million", "billion", "m users", "b users"]):
                strong_competitors += 1

        score -= min(strong_competitors * 0.15, 0.4)
        return score

    def _score_execution_feasibility(self, intelligence: MarketIntelligence) -> float:
        score = 0.7
        high_barriers = sum(
            1 for barrier in intelligence.barriers if (barrier.get("severity") or "").lower() == "high"
        )
        medium_barriers = sum(
            1 for barrier in intelligence.barriers if (barrier.get("severity") or "").lower() == "medium"
        )
        score -= high_barriers * 0.2
        score -= medium_barriers * 0.1

        if intelligence.market_stage == MarketStage.MATURE:
            score += 0.2
        elif intelligence.market_stage == MarketStage.EMERGING:
            score -= 0.1

        if len(intelligence.competitors) > 0:
            score += 0.1

        return score

    def _score_innovation_potential(self, intelligence: MarketIntelligence) -> float:
        score = 0.5
        score += min(len(intelligence.market_gaps) * 0.2, 0.4)

        if intelligence.market_stage == MarketStage.EMERGING:
            score += 0.3
        elif intelligence.market_stage == MarketStage.GROWING:
            score += 0.2
        elif intelligence.market_stage == MarketStage.MATURE:
            score -= 0.1

        score += min(len(intelligence.trends) * 0.1, 0.2)

        num_competitors = len(intelligence.competitors)
        if num_competitors <= 2:
            score += 0.2
        elif num_competitors <= 5:
            score += 0.1

        return score

    def _calculate_confidence(
        self, intelligence: MarketIntelligence, search_results: Dict[str, Any]
    ) -> float:
        confidence = 0.3
        analysis_type = search_results.get("analysis_type")
        if analysis_type == "enhanced":
            confidence += 0.4
        elif analysis_type == "basic":
            confidence += 0.2

        if intelligence.tam_estimate not in {"Unknown", "Data not available", "Analysis unavailable"}:
            confidence += 0.1
        if intelligence.growth_rate not in {"Unknown", "Data not available", "Analysis unavailable"}:
            confidence += 0.1
        if intelligence.competitors:
            confidence += 0.1
        if intelligence.market_gaps:
            confidence += 0.05
        if intelligence.trends:
            confidence += 0.05

        return confidence

    def _default_scores(self) -> MarketScores:
        return MarketScores(
            market_opportunity=0.5,
            competitive_landscape=0.5,
            execution_feasibility=0.5,
            innovation_potential=0.5,
            overall_score=0.5,
            confidence=0.3,
        )

    def _default_intelligence(self) -> MarketIntelligence:
        return MarketIntelligence(
            tam_estimate="Analysis unavailable",
            growth_rate="Analysis unavailable",
            market_stage=MarketStage.GROWING,
            competitors=[],
            market_gaps=[],
            trends=[],
            barriers=[],
            recommendations=[],
        )


class DashboardGenerator:
    """Generate rich, text-based dashboards summarising market intelligence."""

    def __init__(self) -> None:
        self.score_labels = {
            "high": "[High]",
            "medium": "[Medium]",
            "low": "[Low]",
        }
        self.progress_bars = {
            "full": "==========",
            "high": "=======---",
            "medium": "====------",
            "low": "==--------",
            "empty": "----------",
        }

    def generate_comprehensive_dashboard(
        self, idea: str, scores: MarketScores, intelligence: MarketIntelligence
    ) -> str:
        try:
            sections = [
                self._generate_header(idea, scores),
                self._generate_score_breakdown(scores),
                self._generate_competitor_analysis(intelligence.competitors),
                self._generate_opportunity_analysis(intelligence.market_gaps),
                self._generate_trend_analysis(intelligence.trends),
                self._generate_barrier_analysis(intelligence.barriers),
                self._generate_recommendations(intelligence.recommendations, scores),
                self._generate_footer(scores.confidence),
            ]
            dashboard = "\n\n".join(section for section in sections if section)
            logger.info("Generated comprehensive dashboard.")
            return dashboard
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Dashboard generation failed: %s", exc)
            return self._generate_fallback_dashboard(idea, scores)

    def _generate_header(self, idea: str, scores: MarketScores) -> str:
        rating = scores.overall_score * 10
        label = self._get_score_label(scores.overall_score)
        confidence_bar = self._get_progress_bar(scores.confidence)
        return (
            f"MARKET ANALYSIS: {idea}\n"
            f"Overall Assessment: {rating:.1f}/10 {label}\n"
            f"Confidence: {confidence_bar} ({scores.confidence:.1f}/1.0)"
        )

    def _generate_score_breakdown(self, scores: MarketScores) -> str:
        rows = [
            (
                "Market Opportunity",
                scores.market_opportunity,
            ),
            (
                "Competitive Position",
                scores.competitive_landscape,
            ),
            (
                "Execution Feasibility",
                scores.execution_feasibility,
            ),
            (
                "Innovation Potential",
                scores.innovation_potential,
            ),
        ]
        lines = ["DETAILED SCORES:"]
        for label, value in rows:
            lines.append(
                f"- {label}: {self._get_progress_bar(value)} "
                f"{value:.1f}/1.0 {self._get_score_label(value)}"
            )
        return "\n".join(lines)

    def _generate_competitor_analysis(self, competitors: List[Dict[str, Any]]) -> str:
        if not competitors:
            return (
                "COMPETITIVE LANDSCAPE:\n"
                "No major competitors identified. This may indicate whitespace or limited data."
            )

        lines: List[str] = ["COMPETITIVE LANDSCAPE:"]
        for competitor in competitors[:5]:
            name = competitor.get("name", "Competitor")
            description = competitor.get("description", "").strip()
            if len(description) > 90:
                description = f"{description[:87]}..."
            position = competitor.get("market_position", "position unknown")
            funding = competitor.get("funding", "Unknown")
            users = competitor.get("users", "Unknown")
            lines.append(f"- {name} ({position})")
            if description:
                lines.append(f"  Summary: {description}")
            details: List[str] = []
            if funding != "Unknown":
                details.append(f"Funding: {funding}")
            if users != "Unknown":
                details.append(f"Users: {users}")
            if details:
                lines.append(f"  Details: {', '.join(details)}")

        extra = len(competitors) - 5
        if extra > 0:
            lines.append(f"... plus {extra} more.")
        return "\n".join(lines)

    def _generate_opportunity_analysis(self, market_gaps: List[Dict[str, Any]]) -> str:
        if not market_gaps:
            return (
                "MARKET OPPORTUNITIES:\n"
                "No explicit gaps identified. Consider deeper user interviews to discover unmet needs."
            )

        lines = ["MARKET OPPORTUNITIES:"]
        for gap in market_gaps[:3]:
            gap_desc = gap.get("gap", "Opportunity")
            if len(gap_desc) > 90:
                gap_desc = f"{gap_desc[:87]}..."
            difficulty = gap.get("difficulty", "medium")
            opportunity = gap.get("opportunity", "")
            lines.append(f"- {gap_desc} (difficulty: {difficulty})")
            if opportunity and opportunity != gap_desc:
                lines.append(f"  Rationale: {opportunity}")
        return "\n".join(lines)

    def _generate_trend_analysis(self, trends: List[Dict[str, Any]]) -> str:
        if not trends:
            return (
                "MARKET TRENDS:\n"
                "No distinct trends surfaced. Monitor industry publications for emerging signals."
            )

        lines = ["MARKET TRENDS:"]
        for trend in trends[:3]:
            trend_desc = trend.get("trend", "Trend")
            impact = trend.get("impact", "")
            timeline = trend.get("timeline", "ongoing")
            if len(trend_desc) > 80:
                trend_desc = f"{trend_desc[:77]}..."
            lines.append(f"- {trend_desc} ({timeline})")
            if impact and impact != trend_desc:
                lines.append(f"  Impact: {impact}")
        return "\n".join(lines)

    def _generate_barrier_analysis(self, barriers: List[Dict[str, Any]]) -> str:
        if not barriers:
            return (
                "ENTRY BARRIERS:\n"
                "No major barriers identified. This suggests favourable conditions for entry."
            )

        lines = ["ENTRY BARRIERS:"]
        for barrier in barriers[:3]:
            description = barrier.get("barrier", "Barrier")
            severity = barrier.get("severity", "medium")
            mitigation = barrier.get("mitigation", "")
            if len(description) > 80:
                description = f"{description[:77]}..."
            lines.append(f"- {description} (severity: {severity})")
            if mitigation:
                lines.append(f"  Mitigation: {mitigation}")
        return "\n".join(lines)

    def _generate_recommendations(
        self, recommendations: List[Dict[str, Any]], scores: MarketScores
    ) -> str:
        lines = ["STRATEGIC RECOMMENDATIONS:"]

        for rec in recommendations[:3]:
            strategy = rec.get("strategy", "Recommendation")
            rationale = rec.get("rationale", "")
            priority = rec.get("priority", "medium")
            lines.append(f"- {strategy} (priority: {priority})")
            if rationale:
                lines.append(f"  Why: {rationale}")

        auto_recs = self._generate_auto_recommendations(scores)
        lines.extend(auto_recs)

        return "\n".join(lines)

    def _generate_auto_recommendations(self, scores: MarketScores) -> List[str]:
        recs: List[str] = []
        if scores.market_opportunity < 0.4:
            recs.append("- Explore adjacent markets to find stronger demand signals.")
        elif scores.market_opportunity > 0.7:
            recs.append("- Capitalise quickly on strong market appetite; prioritise speed.")

        if scores.competitive_landscape < 0.3:
            recs.append("- High competition detected; emphasise differentiation and brand.")
        elif scores.competitive_landscape > 0.7:
            recs.append("- Low competition; claim thought leadership early.")

        if scores.execution_feasibility < 0.4:
            recs.append("- Execution risk is high; de-risk with pilots or partnerships.")
        elif scores.execution_feasibility > 0.7:
            recs.append("- Execution looks feasible; focus on resource allocation.")

        if scores.innovation_potential > 0.7:
            recs.append("- Strong innovation runway; consider protecting IP and storytelling.")
        elif scores.innovation_potential < 0.4:
            recs.append("- Innovation signals are limited; optimise on operations and UX.")

        return recs

    def _generate_footer(self, confidence: float) -> str:
        return (
            f"ANALYSIS CONFIDENCE: {self._format_confidence(confidence)}\n"
            "Next Steps: Review recommendations, then proceed to product development when ready.\n\n"
            "**Would you like to proceed to product development, or explore a different idea?**"
        )

    def _get_score_label(self, score: float) -> str:
        if score >= 0.7:
            return self.score_labels["high"]
        if score >= 0.4:
            return self.score_labels["medium"]
        return self.score_labels["low"]

    def _get_progress_bar(self, score: float) -> str:
        if score >= 0.8:
            return self.progress_bars["full"]
        if score >= 0.6:
            return self.progress_bars["high"]
        if score >= 0.4:
            return self.progress_bars["medium"]
        if score >= 0.2:
            return self.progress_bars["low"]
        return self.progress_bars["empty"]

    def _format_confidence(self, confidence: float) -> str:
        if confidence >= 0.8:
            label = "very high"
        elif confidence >= 0.6:
            label = "high"
        elif confidence >= 0.4:
            label = "medium"
        else:
            label = "low"
        return f"{confidence:.1f}/1.0 ({label})"

    def _generate_fallback_dashboard(self, idea: str, scores: MarketScores) -> str:
        return (
            f"MARKET ANALYSIS: {idea}\n"
            f"Overall Score: {scores.overall_score:.1f}/1.0 {self._get_score_label(scores.overall_score)}\n"
            "Scores:\n"
            f"- Market Opportunity: {scores.market_opportunity:.1f}/1.0\n"
            f"- Competitive Landscape: {scores.competitive_landscape:.1f}/1.0\n"
            f"- Execution Feasibility: {scores.execution_feasibility:.1f}/1.0\n"
            f"- Innovation Potential: {scores.innovation_potential:.1f}/1.0\n\n"
            "**Would you like to proceed to product development, or explore a different idea?**"
        )

def _get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not configured; returning limited search results.")
        return None
    return OpenAI(api_key=api_key)


def _web_search_with_openai(query: str) -> Dict[str, Any]:
    client = _get_openai_client()
    if not client:
        validation_circuit_breaker.record_failure()
        return {
            "summary": "OpenAI API key not configured; unable to perform web search.",
            "key_signals": [],
            "competitors": [],
            "opportunities": [],
        }

    system_prompt = (
        "You are a market research analyst. Use web search tools when helpful and present findings in concise, "
        "evidence-backed form."
    )
    user_prompt = f"""Research the current market landscape for "{query}".
Use web search to retrieve fresh information about competitors, trends, unmet needs, and risks.
Return JSON with this structure:
{{
  "key_signals": ["bullet insight 1", ...],
  "competitors": [
    {{
      "name": "Competitor name",
      "position": "leader/challenger/niche",
      "note": "short supporting detail"
    }}
  ],
  "opportunities": [
    {{
      "gap": "underserved need",
      "difficulty": "low/medium/high"
    }}
  ],
  "summary": "Two-sentence overview referencing cited findings."
}}
If the search returns little, say so and provide best-effort reasoning.
"""

    def _run_openai() -> Dict[str, Any]:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=[{"type": "web_search"}],
            tool_choice="auto",
        )

        # Prefer output_text if available
        output_text = getattr(response, "output_text", None)
        if not output_text:
            collected: List[str] = []
            for item in getattr(response, "output", []) or []:
                if item.type == "message":
                    for c in item.content:
                        if getattr(c, "type", "") == "output_text":
                            collected.append(c.text)
            output_text = "".join(collected)

        if not output_text:
            raise ValueError("OpenAI web search returned no textual output.")

        match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                data.setdefault("analysis_type", "enhanced")
                return data
            except json.JSONDecodeError:
                logger.debug("Unable to parse JSON from OpenAI output; returning raw text.")

        return {
            "summary": output_text.strip(),
            "key_signals": [],
            "competitors": [],
            "opportunities": [],
            "analysis_type": "basic",
        }

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_openai)
        try:
            analysis = future.result(timeout=OPENAI_TIMEOUT)
            validation_circuit_breaker.record_success()
            return analysis
        except FuturesTimeout:
            validation_circuit_breaker.record_failure()
            logger.warning("OpenAI analysis timed out after %s seconds.", OPENAI_TIMEOUT)
            return {
                "summary": "OpenAI analysis timed out; returning raw findings.",
                "key_signals": [],
                "competitors": [],
                "opportunities": [],
                "analysis_type": "timeout",
            }
        except Exception as exc:  # pylint: disable=broad-except
            validation_circuit_breaker.record_failure()
            logger.error("OpenAI analysis failed: %s", exc)
            return {
                "summary": f"OpenAI analysis failed: {exc}",
                "key_signals": [],
                "competitors": [],
                "opportunities": [],
                "analysis_type": "error",
            }


def _normalise_for_market_analyzer(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAI web search output into MarketAnalyzer-friendly structure."""
    market_size = {
        "tam": analysis.get("tam") or analysis.get("market_size", {}).get("tam", "Unknown"),
        "growth_rate": analysis.get("growth_rate", "Unknown"),
        "market_stage": analysis.get("market_stage", "growing"),
    }

    competitors: List[Dict[str, Any]] = []
    for competitor in analysis.get("competitors") or []:
        competitors.append(
            {
                "name": competitor.get("name", "Competitor"),
                "description": competitor.get("note", ""),
                "market_position": competitor.get("position", CompetitorPosition.CHALLENGER.value),
                "funding": competitor.get("funding", "Unknown"),
                "users": competitor.get("users", "Unknown"),
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", []),
            }
        )

    market_gaps = []
    for opportunity in analysis.get("opportunities") or []:
        market_gaps.append(
            {
                "gap": opportunity.get("gap", "Unspecified gap"),
                "opportunity": opportunity.get("opportunity", opportunity.get("note", "")),
                "difficulty": opportunity.get("difficulty", "medium"),
            }
        )

    trends = analysis.get("trends") or []
    barriers = analysis.get("barriers") or []
    recommendations = analysis.get("recommendations") or []

    return {
        "analysis_type": analysis.get("analysis_type", "basic"),
        "market_intelligence": {
            "market_size": market_size,
            "competitors": competitors,
            "market_gaps": market_gaps,
            "trends": trends,
            "barriers": barriers,
            "recommendations": recommendations,
        },
        "results": analysis.get("raw_results", []),
    }


@tool
def venture_web_search(query: str) -> str:
    """Search the public web and return market intelligence for the validator agent."""
    if not query or not query.strip():
        return "No query supplied to web search."

    if not validation_circuit_breaker.can_proceed():
        return "Web search is temporarily paused due to repeated failures. Please try again shortly."

    analysis = _web_search_with_openai(query)
    structured_payload = _normalise_for_market_analyzer(analysis)
    analyzer = MarketAnalyzer()
    scores, intelligence = analyzer.analyze_market_intelligence(structured_payload)
    dashboard = DashboardGenerator().generate_comprehensive_dashboard(query, scores, intelligence)
    return dashboard


__all__ = [
    "venture_web_search",
    "ValidationCircuitBreaker",
    "validation_circuit_breaker",
    "MarketAnalyzer",
    "MarketScores",
    "MarketIntelligence",
    "DashboardGenerator",
]
