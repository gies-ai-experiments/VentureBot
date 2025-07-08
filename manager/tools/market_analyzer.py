#!/usr/bin/env python3
"""
Advanced Market Analysis Engine for VentureBot
Provides comprehensive market intelligence and multi-dimensional scoring.
"""

import logging
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MarketStage(Enum):
    EMERGING = "emerging"
    GROWING = "growing" 
    MATURE = "mature"
    DECLINING = "declining"

class CompetitorPosition(Enum):
    LEADER = "market leader"
    CHALLENGER = "challenger"
    NICHE = "niche player"

@dataclass
class MarketScores:
    """Multi-dimensional market analysis scores"""
    market_opportunity: float  # 0-1.0
    competitive_landscape: float  # 0-1.0  
    execution_feasibility: float  # 0-1.0
    innovation_potential: float  # 0-1.0
    overall_score: float  # 0-1.0
    confidence: float  # 0-1.0

@dataclass
class MarketIntelligence:
    """Structured market intelligence data"""
    tam_estimate: str
    growth_rate: str
    market_stage: MarketStage
    competitors: List[Dict[str, Any]]
    market_gaps: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    barriers: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

class MarketAnalyzer:
    """Advanced market analysis engine"""
    
    def __init__(self):
        self.funding_patterns = {
            'million': 1_000_000,
            'billion': 1_000_000_000,
            'k': 1_000,
            'm': 1_000_000,
            'b': 1_000_000_000
        }
        
    def analyze_market_intelligence(self, search_results: Dict[str, Any]) -> Tuple[MarketScores, MarketIntelligence]:
        """
        Analyze market intelligence data and generate comprehensive scores
        
        Args:
            search_results: Enhanced search results with market intelligence
            
        Returns:
            Tuple of (MarketScores, MarketIntelligence)
        """
        try:
            # Extract market intelligence if available
            if "market_intelligence" in search_results:
                intelligence_data = search_results["market_intelligence"]
                intelligence = self._parse_market_intelligence(intelligence_data)
            else:
                # Fallback to basic analysis
                intelligence = self._extract_basic_intelligence(search_results.get("results", []))
            
            # Calculate multi-dimensional scores
            scores = self._calculate_comprehensive_scores(intelligence, search_results)
            
            logger.info(f"Market analysis completed - Overall score: {scores.overall_score:.2f}")
            
            return scores, intelligence
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            # Return default moderate scores on error
            default_scores = MarketScores(
                market_opportunity=0.5,
                competitive_landscape=0.5,
                execution_feasibility=0.5,
                innovation_potential=0.5,
                overall_score=0.5,
                confidence=0.3
            )
            default_intelligence = self._get_default_intelligence()
            return default_scores, default_intelligence
    
    def _parse_market_intelligence(self, intelligence_data: Dict[str, Any]) -> MarketIntelligence:
        """Parse structured market intelligence data"""
        
        # Extract market size information
        market_size = intelligence_data.get("market_size", {})
        tam_estimate = market_size.get("tam", "Unknown")
        growth_rate = market_size.get("growth_rate", "Unknown")
        
        # Parse market stage
        stage_str = market_size.get("market_stage", "growing").lower()
        try:
            market_stage = MarketStage(stage_str)
        except ValueError:
            market_stage = MarketStage.GROWING
        
        # Extract other intelligence components
        competitors = intelligence_data.get("competitors", [])
        market_gaps = intelligence_data.get("market_gaps", [])
        trends = intelligence_data.get("trends", [])
        barriers = intelligence_data.get("barriers", [])
        recommendations = intelligence_data.get("recommendations", [])
        
        return MarketIntelligence(
            tam_estimate=tam_estimate,
            growth_rate=growth_rate,
            market_stage=market_stage,
            competitors=competitors,
            market_gaps=market_gaps,
            trends=trends,
            barriers=barriers,
            recommendations=recommendations
        )
    
    def _extract_basic_intelligence(self, results: List[Dict[str, Any]]) -> MarketIntelligence:
        """Extract intelligence from basic search results"""
        
        # Analyze result content for intelligence
        competitors = []
        market_gaps = []
        trends = []
        barriers = []
        
        for result in results:
            content = result.get("content", "").lower()
            title = result.get("title", "")
            
            # Extract competitor information
            if any(keyword in content for keyword in ["competitor", "company", "product", "leader"]):
                competitors.append({
                    "name": title,
                    "description": result.get("content", "")[:200],
                    "market_position": "challenger",  # Default
                    "funding": "Unknown",
                    "users": "Unknown",
                    "strengths": [],
                    "weaknesses": []
                })
            
            # Look for market gaps
            if any(keyword in content for keyword in ["gap", "opportunity", "underserved", "need"]):
                market_gaps.append({
                    "gap": result.get("content", "")[:100],
                    "opportunity": "Market opportunity identified",
                    "difficulty": "medium"
                })
        
        return MarketIntelligence(
            tam_estimate="Data not available",
            growth_rate="Data not available", 
            market_stage=MarketStage.GROWING,
            competitors=competitors,
            market_gaps=market_gaps,
            trends=trends,
            barriers=barriers,
            recommendations=[]
        )
    
    def _calculate_comprehensive_scores(self, intelligence: MarketIntelligence, search_results: Dict[str, Any]) -> MarketScores:
        """Calculate multi-dimensional market scores"""
        
        # 1. Market Opportunity Score (0-1.0)
        market_opportunity = self._score_market_opportunity(intelligence)
        
        # 2. Competitive Landscape Score (0-1.0) 
        competitive_landscape = self._score_competitive_landscape(intelligence)
        
        # 3. Execution Feasibility Score (0-1.0)
        execution_feasibility = self._score_execution_feasibility(intelligence)
        
        # 4. Innovation Potential Score (0-1.0)
        innovation_potential = self._score_innovation_potential(intelligence)
        
        # 5. Calculate overall weighted score
        weights = {
            'market_opportunity': 0.3,
            'competitive_landscape': 0.25,
            'execution_feasibility': 0.25,
            'innovation_potential': 0.2
        }
        
        overall_score = (
            market_opportunity * weights['market_opportunity'] +
            competitive_landscape * weights['competitive_landscape'] +
            execution_feasibility * weights['execution_feasibility'] +
            innovation_potential * weights['innovation_potential']
        )
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(intelligence, search_results)
        
        return MarketScores(
            market_opportunity=round(market_opportunity, 2),
            competitive_landscape=round(competitive_landscape, 2),
            execution_feasibility=round(execution_feasibility, 2),
            innovation_potential=round(innovation_potential, 2),
            overall_score=round(overall_score, 2),
            confidence=round(confidence, 2)
        )
    
    def _score_market_opportunity(self, intelligence: MarketIntelligence) -> float:
        """Score market opportunity (0-1.0)"""
        score = 0.5  # Base score
        
        # Analyze TAM if available
        tam = intelligence.tam_estimate.lower()
        if "billion" in tam or "b" in tam:
            score += 0.3
        elif "million" in tam or "m" in tam:
            score += 0.2
        elif "unknown" not in tam:
            score += 0.1
        
        # Analyze growth rate
        growth = intelligence.growth_rate.lower()
        if any(indicator in growth for indicator in ["15%", "20%", "25%", "30%", "high"]):
            score += 0.2
        elif any(indicator in growth for indicator in ["5%", "10%", "growing"]):
            score += 0.1
        
        # Market stage bonus
        if intelligence.market_stage == MarketStage.GROWING:
            score += 0.2
        elif intelligence.market_stage == MarketStage.EMERGING:
            score += 0.15
        elif intelligence.market_stage == MarketStage.DECLINING:
            score -= 0.2
        
        # Market gaps bonus
        score += min(len(intelligence.market_gaps) * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _score_competitive_landscape(self, intelligence: MarketIntelligence) -> float:
        """Score competitive landscape (0-1.0) - higher score = less competition"""
        score = 1.0  # Start high, reduce based on competition
        
        num_competitors = len(intelligence.competitors)
        
        # Reduce score based on number of competitors
        if num_competitors >= 10:
            score -= 0.4
        elif num_competitors >= 5:
            score -= 0.3
        elif num_competitors >= 2:
            score -= 0.2
        elif num_competitors == 1:
            score -= 0.1
        
        # Analyze competitor strength
        strong_competitors = 0
        for competitor in intelligence.competitors:
            position = competitor.get("market_position", "").lower()
            funding = competitor.get("funding", "").lower()
            users = competitor.get("users", "").lower()
            
            # Check if this is a strong competitor
            if (position == "market leader" or 
                "billion" in funding or "million" in funding or
                "million" in users or "billion" in users):
                strong_competitors += 1
        
        # Additional penalty for strong competitors
        score -= min(strong_competitors * 0.15, 0.4)
        
        return max(score, 0.0)
    
    def _score_execution_feasibility(self, intelligence: MarketIntelligence) -> float:
        """Score execution feasibility (0-1.0)"""
        score = 0.7  # Base feasibility score
        
        # Analyze barriers
        high_barriers = sum(1 for barrier in intelligence.barriers 
                           if barrier.get("severity", "").lower() == "high")
        medium_barriers = sum(1 for barrier in intelligence.barriers 
                             if barrier.get("severity", "").lower() == "medium")
        
        # Reduce score based on barriers
        score -= high_barriers * 0.2
        score -= medium_barriers * 0.1
        
        # Market stage impact on feasibility
        if intelligence.market_stage == MarketStage.MATURE:
            score += 0.2  # Easier to enter mature markets
        elif intelligence.market_stage == MarketStage.EMERGING:
            score -= 0.1  # Harder to navigate emerging markets
        
        # Number of competitors can indicate feasibility
        num_competitors = len(intelligence.competitors)
        if num_competitors > 0:
            score += 0.1  # Proven market demand
        
        return max(min(score, 1.0), 0.0)
    
    def _score_innovation_potential(self, intelligence: MarketIntelligence) -> float:
        """Score innovation potential (0-1.0)"""
        score = 0.5  # Base score
        
        # Market gaps indicate innovation opportunities
        score += min(len(intelligence.market_gaps) * 0.2, 0.4)
        
        # Emerging markets have higher innovation potential
        if intelligence.market_stage == MarketStage.EMERGING:
            score += 0.3
        elif intelligence.market_stage == MarketStage.GROWING:
            score += 0.2
        elif intelligence.market_stage == MarketStage.MATURE:
            score -= 0.1
        
        # Trends can indicate innovation opportunities
        score += min(len(intelligence.trends) * 0.1, 0.2)
        
        # Less competition = more innovation potential
        num_competitors = len(intelligence.competitors)
        if num_competitors <= 2:
            score += 0.2
        elif num_competitors <= 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_confidence(self, intelligence: MarketIntelligence, search_results: Dict[str, Any]) -> float:
        """Calculate confidence in the analysis based on data quality"""
        confidence = 0.3  # Base confidence
        
        # Higher confidence if we have structured market intelligence
        if search_results.get("analysis_type") == "enhanced":
            confidence += 0.4
        elif search_results.get("analysis_type") == "basic":
            confidence += 0.2
        
        # Confidence based on data completeness
        if intelligence.tam_estimate != "Unknown" and intelligence.tam_estimate != "Data not available":
            confidence += 0.1
        
        if intelligence.growth_rate != "Unknown" and intelligence.growth_rate != "Data not available":
            confidence += 0.1
        
        if len(intelligence.competitors) > 0:
            confidence += 0.1
        
        if len(intelligence.market_gaps) > 0:
            confidence += 0.05
        
        if len(intelligence.trends) > 0:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _get_default_intelligence(self) -> MarketIntelligence:
        """Return default market intelligence for error cases"""
        return MarketIntelligence(
            tam_estimate="Analysis unavailable",
            growth_rate="Analysis unavailable",
            market_stage=MarketStage.GROWING,
            competitors=[],
            market_gaps=[],
            trends=[],
            barriers=[],
            recommendations=[]
        )