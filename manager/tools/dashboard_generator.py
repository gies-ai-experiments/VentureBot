#!/usr/bin/env python3
"""
Rich Visual Analysis Dashboard Generator for VentureBot
Creates comprehensive market analysis visualizations for users.
"""

import logging
from typing import Dict, List, Any
from .market_analyzer import MarketScores, MarketIntelligence, MarketStage

logger = logging.getLogger(__name__)

class DashboardGenerator:
    """Generate rich visual analysis dashboards"""
    
    def __init__(self):
        self.score_colors = {
            'high': '🟢',
            'medium': '🟡', 
            'low': '🔴'
        }
        
        self.progress_bars = {
            'full': '████████████',
            'high': '█████████░░░',
            'medium': '██████░░░░░░',
            'low': '███░░░░░░░░░',
            'empty': '░░░░░░░░░░░░'
        }
    
    def generate_comprehensive_dashboard(self, 
                                       idea: str, 
                                       scores: MarketScores, 
                                       intelligence: MarketIntelligence) -> str:
        """
        Generate a comprehensive market analysis dashboard
        
        Args:
            idea: The startup idea being analyzed
            scores: Multi-dimensional market scores
            intelligence: Structured market intelligence data
            
        Returns:
            Formatted dashboard string for user display
        """
        try:
            # Build dashboard sections
            header = self._generate_header(idea, scores)
            score_breakdown = self._generate_score_breakdown(scores)
            competitors = self._generate_competitor_analysis(intelligence.competitors)
            opportunities = self._generate_opportunity_analysis(intelligence.market_gaps)
            trends = self._generate_trend_analysis(intelligence.trends)
            barriers = self._generate_barrier_analysis(intelligence.barriers)
            recommendations = self._generate_recommendations(intelligence.recommendations, scores)
            
            # Combine all sections
            dashboard = f"""
{header}

{score_breakdown}

{competitors}

{opportunities}

{trends}

{barriers}

{recommendations}

📈 **ANALYSIS CONFIDENCE:** {self._format_confidence(scores.confidence)}
💡 **Next Steps:** Review recommendations above and proceed to product development when ready.

**__Would you like to proceed to product development, or explore a different idea?__**
"""
            
            logger.info("Comprehensive dashboard generated successfully")
            return dashboard.strip()
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}")
            return self._generate_fallback_dashboard(idea, scores)
    
    def _generate_header(self, idea: str, scores: MarketScores) -> str:
        """Generate dashboard header with overall assessment"""
        
        overall_rating = scores.overall_score * 10
        overall_color = self._get_score_color(scores.overall_score)
        
        confidence_bar = self._get_progress_bar(scores.confidence)
        
        return f"""🎯 **MARKET ANALYSIS:** {idea}

📊 **OVERALL ASSESSMENT:** {overall_rating:.1f}/10 {overall_color}
🔍 **Analysis Confidence:** {confidence_bar} ({scores.confidence:.1f}/1.0)"""
    
    def _generate_score_breakdown(self, scores: MarketScores) -> str:
        """Generate detailed score breakdown with visual indicators"""
        
        market_bar = self._get_progress_bar(scores.market_opportunity)
        market_color = self._get_score_color(scores.market_opportunity)
        
        competitive_bar = self._get_progress_bar(scores.competitive_landscape)
        competitive_color = self._get_score_color(scores.competitive_landscape)
        
        execution_bar = self._get_progress_bar(scores.execution_feasibility)
        execution_color = self._get_score_color(scores.execution_feasibility)
        
        innovation_bar = self._get_progress_bar(scores.innovation_potential)
        innovation_color = self._get_score_color(scores.innovation_potential)
        
        return f"""📈 **DETAILED SCORES:**
├── **Market Opportunity:** {market_bar} {scores.market_opportunity:.1f}/1.0 {market_color}
├── **Competitive Position:** {competitive_bar} {scores.competitive_landscape:.1f}/1.0 {competitive_color}
├── **Execution Feasibility:** {execution_bar} {scores.execution_feasibility:.1f}/1.0 {execution_color}
└── **Innovation Potential:** {innovation_bar} {scores.innovation_potential:.1f}/1.0 {innovation_color}"""
    
    def _generate_competitor_analysis(self, competitors: List[Dict[str, Any]]) -> str:
        """Generate competitor analysis section"""
        
        if not competitors:
            return """🏢 **COMPETITIVE LANDSCAPE:**
No major competitors identified - this could indicate a new market opportunity or insufficient data."""
        
        # Limit to top 5 competitors for readability
        top_competitors = competitors[:5]
        
        competitor_lines = []
        for i, competitor in enumerate(top_competitors, 1):
            name = competitor.get("name", f"Competitor {i}")
            description = competitor.get("description", "No description available")
            position = competitor.get("market_position", "unknown")
            funding = competitor.get("funding", "Unknown")
            users = competitor.get("users", "Unknown")
            
            # Create position emoji
            position_emoji = {
                "market leader": "👑",
                "challenger": "⚔️", 
                "niche player": "🎯"
            }.get(position.lower(), "🏢")
            
            # Truncate description if too long
            if len(description) > 80:
                description = description[:77] + "..."
            
            competitor_lines.append(
                f"• **{name}** {position_emoji} - {description}"
            )
            
            # Add details if available
            details = []
            if funding != "Unknown":
                details.append(f"💰 {funding}")
            if users != "Unknown":
                details.append(f"👥 {users}")
            
            if details:
                competitor_lines.append(f"  {' | '.join(details)}")
        
        competitor_text = "\n".join(competitor_lines)
        
        total_competitors = len(competitors)
        if total_competitors > 5:
            competitor_text += f"\n... and {total_competitors - 5} more competitors"
        
        return f"""🏢 **KEY COMPETITORS IDENTIFIED:**
{competitor_text}"""
    
    def _generate_opportunity_analysis(self, market_gaps: List[Dict[str, Any]]) -> str:
        """Generate market opportunity analysis section"""
        
        if not market_gaps:
            return """💡 **MARKET OPPORTUNITIES:**
No specific market gaps identified in current analysis. Consider conducting deeper market research."""
        
        gap_lines = []
        for i, gap in enumerate(market_gaps[:3], 1):  # Limit to top 3
            gap_desc = gap.get("gap", f"Opportunity {i}")
            opportunity = gap.get("opportunity", "Market opportunity identified")
            difficulty = gap.get("difficulty", "medium").lower()
            
            # Difficulty emoji
            difficulty_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🔴"
            }.get(difficulty, "🟡")
            
            # Truncate if too long
            if len(gap_desc) > 100:
                gap_desc = gap_desc[:97] + "..."
            
            gap_lines.append(f"• **{gap_desc}** {difficulty_emoji}")
            if opportunity and opportunity != gap_desc:
                gap_lines.append(f"  └─ {opportunity}")
        
        return f"""💡 **MARKET OPPORTUNITIES IDENTIFIED:**
{chr(10).join(gap_lines)}"""
    
    def _generate_trend_analysis(self, trends: List[Dict[str, Any]]) -> str:
        """Generate market trends analysis section"""
        
        if not trends:
            return """📊 **MARKET TRENDS:**
No specific market trends identified in current analysis."""
        
        trend_lines = []
        for trend in trends[:3]:  # Limit to top 3
            trend_desc = trend.get("trend", "Market trend")
            impact = trend.get("impact", "Market impact")
            timeline = trend.get("timeline", "Ongoing")
            
            # Truncate if too long
            if len(trend_desc) > 80:
                trend_desc = trend_desc[:77] + "..."
            
            trend_lines.append(f"• **{trend_desc}** ({timeline})")
            if impact and impact != trend_desc:
                trend_lines.append(f"  └─ {impact}")
        
        return f"""📊 **RELEVANT MARKET TRENDS:**
{chr(10).join(trend_lines)}"""
    
    def _generate_barrier_analysis(self, barriers: List[Dict[str, Any]]) -> str:
        """Generate market barriers analysis section"""
        
        if not barriers:
            return """⚠️ **ENTRY BARRIERS:**
No major entry barriers identified - this suggests good market accessibility."""
        
        barrier_lines = []
        for barrier in barriers[:3]:  # Limit to top 3
            barrier_desc = barrier.get("barrier", "Entry barrier")
            severity = barrier.get("severity", "medium").lower()
            mitigation = barrier.get("mitigation", "")
            
            # Severity emoji
            severity_emoji = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🔴"
            }.get(severity, "🟡")
            
            # Truncate if too long
            if len(barrier_desc) > 80:
                barrier_desc = barrier_desc[:77] + "..."
            
            barrier_lines.append(f"• **{barrier_desc}** {severity_emoji}")
            if mitigation:
                barrier_lines.append(f"  └─ Mitigation: {mitigation}")
        
        return f"""⚠️ **POTENTIAL ENTRY BARRIERS:**
{chr(10).join(barrier_lines)}"""
    
    def _generate_recommendations(self, recommendations: List[Dict[str, Any]], scores: MarketScores) -> str:
        """Generate strategic recommendations section"""
        
        # Always generate some recommendations based on scores
        auto_recommendations = self._generate_auto_recommendations(scores)
        
        rec_lines = []
        
        # Add provided recommendations
        for rec in recommendations[:3]:  # Limit to top 3
            strategy = rec.get("strategy", "Strategic recommendation")
            rationale = rec.get("rationale", "")
            priority = rec.get("priority", "medium").lower()
            
            # Priority emoji
            priority_emoji = {
                "high": "🔥",
                "medium": "📈",
                "low": "💡"
            }.get(priority, "📈")
            
            rec_lines.append(f"{priority_emoji} **{strategy}**")
            if rationale:
                rec_lines.append(f"   └─ {rationale}")
        
        # Add auto-generated recommendations
        for auto_rec in auto_recommendations:
            rec_lines.append(auto_rec)
        
        if not rec_lines:
            rec_lines = ["📈 **Focus on market validation and customer development**", 
                        "💡 **Develop a minimum viable product (MVP)**",
                        "🎯 **Identify and target your core customer segment**"]
        
        return f"""🚀 **STRATEGIC RECOMMENDATIONS:**
{chr(10).join(rec_lines)}"""
    
    def _generate_auto_recommendations(self, scores: MarketScores) -> List[str]:
        """Generate automatic recommendations based on scores"""
        recommendations = []
        
        # Market opportunity recommendations
        if scores.market_opportunity < 0.4:
            recommendations.append("📊 **Consider pivoting to a larger market opportunity**")
        elif scores.market_opportunity > 0.7:
            recommendations.append("🎯 **Excellent market opportunity - focus on execution speed**")
        
        # Competitive landscape recommendations  
        if scores.competitive_landscape < 0.3:
            recommendations.append("⚔️ **Highly competitive market - focus on strong differentiation**")
        elif scores.competitive_landscape > 0.7:
            recommendations.append("🌟 **Low competition advantage - move quickly to establish market position**")
        
        # Execution feasibility recommendations
        if scores.execution_feasibility < 0.4:
            recommendations.append("🛠️ **High execution complexity - consider phased development approach**")
        elif scores.execution_feasibility > 0.7:
            recommendations.append("✅ **Good execution feasibility - prioritize time-to-market**")
        
        # Innovation potential recommendations
        if scores.innovation_potential > 0.7:
            recommendations.append("💡 **High innovation potential - consider intellectual property protection**")
        elif scores.innovation_potential < 0.4:
            recommendations.append("🔄 **Limited innovation - focus on operational excellence and customer experience**")
        
        return recommendations
    
    def _get_score_color(self, score: float) -> str:
        """Get color emoji based on score"""
        if score >= 0.7:
            return self.score_colors['high']
        elif score >= 0.4:
            return self.score_colors['medium']
        else:
            return self.score_colors['low']
    
    def _get_progress_bar(self, score: float) -> str:
        """Get progress bar based on score"""
        if score >= 0.8:
            return self.progress_bars['full']
        elif score >= 0.6:
            return self.progress_bars['high']
        elif score >= 0.4:
            return self.progress_bars['medium']
        elif score >= 0.2:
            return self.progress_bars['low']
        else:
            return self.progress_bars['empty']
    
    def _format_confidence(self, confidence: float) -> str:
        """Format confidence score with description"""
        if confidence >= 0.8:
            return f"{confidence:.1f}/1.0 (Very High) ✅"
        elif confidence >= 0.6:
            return f"{confidence:.1f}/1.0 (High) 🟢"
        elif confidence >= 0.4:
            return f"{confidence:.1f}/1.0 (Medium) 🟡"
        else:
            return f"{confidence:.1f}/1.0 (Low) 🔴"
    
    def _generate_fallback_dashboard(self, idea: str, scores: MarketScores) -> str:
        """Generate a simple fallback dashboard if full generation fails"""
        overall_color = self._get_score_color(scores.overall_score)
        
        return f"""🎯 **MARKET ANALYSIS:** {idea}

📊 **OVERALL ASSESSMENT:** {scores.overall_score:.1f}/1.0 {overall_color}

**Scores:**
• Market Opportunity: {scores.market_opportunity:.1f}/1.0
• Competitive Landscape: {scores.competitive_landscape:.1f}/1.0  
• Execution Feasibility: {scores.execution_feasibility:.1f}/1.0
• Innovation Potential: {scores.innovation_potential:.1f}/1.0

🚀 **Recommendation:** {'Proceed with development' if scores.overall_score > 0.6 else 'Consider refinements before proceeding'}

**__Would you like to proceed to product development, or explore a different idea?__**"""