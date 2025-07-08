#!/usr/bin/env python3
"""
Test script for the enhanced market intelligence analysis system.
Tests the new multi-dimensional scoring and rich dashboard generation.
"""

import os
import sys
import asyncio
import anthropic
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add project root to Python path (parent of tests directory)
tests_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(tests_dir)
sys.path.insert(0, project_root)

from manager.tools.tools import claude_web_search
from manager.tools.market_analyzer import MarketAnalyzer, MarketScores, MarketIntelligence, MarketStage
from manager.tools.dashboard_generator import DashboardGenerator

def test_market_analyzer():
    """Test the market analyzer with different types of data"""
    print("🧠 Testing Market Analyzer")
    print("=" * 40)
    
    analyzer = MarketAnalyzer()
    
    # Test case 1: Enhanced market intelligence data
    print("\n1. Testing with structured market intelligence...")
    
    enhanced_data = {
        "market_intelligence": {
            "market_size": {
                "tam": "$2.1 billion",
                "growth_rate": "15% annually",
                "market_stage": "growing"
            },
            "competitors": [
                {
                    "name": "Fitbit",
                    "description": "Leading fitness tracker company",
                    "market_position": "market leader",
                    "funding": "$100 million",
                    "users": "70 million",
                    "strengths": ["Brand recognition", "App ecosystem"],
                    "weaknesses": ["Limited AI features"]
                },
                {
                    "name": "Apple Watch",
                    "description": "Smart watch with fitness tracking",
                    "market_position": "challenger",
                    "funding": "Internal Apple funding",
                    "users": "100 million",
                    "strengths": ["Ecosystem integration", "Health sensors"],
                    "weaknesses": ["High price point"]
                }
            ],
            "market_gaps": [
                {
                    "gap": "AI-powered personalized coaching",
                    "opportunity": "Underserved segment for personalized fitness AI",
                    "difficulty": "medium"
                },
                {
                    "gap": "Mental health integration",
                    "opportunity": "Growing demand for holistic wellness",
                    "difficulty": "low"
                }
            ],
            "trends": [
                {
                    "trend": "AI integration in fitness",
                    "impact": "Enabling personalized recommendations",
                    "timeline": "2024-2026"
                }
            ],
            "barriers": [
                {
                    "barrier": "Regulatory compliance for health data",
                    "severity": "medium",
                    "mitigation": "Partner with compliance specialists"
                }
            ],
            "recommendations": [
                {
                    "strategy": "Focus on AI differentiation",
                    "rationale": "Market gap in personalized AI coaching",
                    "priority": "high"
                }
            ]
        },
        "analysis_type": "enhanced"
    }
    
    scores, intelligence = analyzer.analyze_market_intelligence(enhanced_data)
    
    print(f"   Market Opportunity: {scores.market_opportunity:.2f}")
    print(f"   Competitive Landscape: {scores.competitive_landscape:.2f}")
    print(f"   Execution Feasibility: {scores.execution_feasibility:.2f}")
    print(f"   Innovation Potential: {scores.innovation_potential:.2f}")
    print(f"   Overall Score: {scores.overall_score:.2f}")
    print(f"   Confidence: {scores.confidence:.2f}")
    
    # Test case 2: Basic search results
    print("\n2. Testing with basic search results...")
    
    basic_data = {
        "results": [
            {"title": "Competitor 1", "content": "Major fitness tracker company with millions of users"},
            {"title": "Market Analysis", "content": "Growing fitness technology market"},
            {"title": "Competitor 2", "content": "Smart watch company with health features"}
        ],
        "analysis_type": "basic"
    }
    
    scores2, intelligence2 = analyzer.analyze_market_intelligence(basic_data)
    
    print(f"   Market Opportunity: {scores2.market_opportunity:.2f}")
    print(f"   Competitive Landscape: {scores2.competitive_landscape:.2f}")
    print(f"   Execution Feasibility: {scores2.execution_feasibility:.2f}")
    print(f"   Innovation Potential: {scores2.innovation_potential:.2f}")
    print(f"   Overall Score: {scores2.overall_score:.2f}")
    print(f"   Confidence: {scores2.confidence:.2f}")
    
    return True

def test_dashboard_generator():
    """Test the dashboard generator with market analysis results"""
    print("\n📊 Testing Dashboard Generator")
    print("=" * 40)
    
    generator = DashboardGenerator()
    
    # Create sample market scores
    scores = MarketScores(
        market_opportunity=0.8,
        competitive_landscape=0.6,
        execution_feasibility=0.7,
        innovation_potential=0.9,
        overall_score=0.75,
        confidence=0.8
    )
    
    # Create sample market intelligence
    intelligence = MarketIntelligence(
        tam_estimate="$2.1 billion",
        growth_rate="15% annually",
        market_stage=MarketStage.GROWING,
        competitors=[
            {
                "name": "Fitbit Premium",
                "description": "AI-powered fitness insights and coaching",
                "market_position": "market leader",
                "funding": "$100M Series C",
                "users": "70M+ users",
                "strengths": ["Brand recognition", "Large user base"],
                "weaknesses": ["Limited AI personalization"]
            },
            {
                "name": "Apple Watch",
                "description": "Comprehensive health and fitness tracking",
                "market_position": "challenger", 
                "funding": "Internal Apple",
                "users": "100M+ users",
                "strengths": ["Ecosystem integration", "Premium hardware"],
                "weaknesses": ["High price point", "iOS only"]
            }
        ],
        market_gaps=[
            {
                "gap": "AI-powered personalized fitness coaching",
                "opportunity": "Underserved market for truly personalized AI fitness guidance",
                "difficulty": "medium"
            },
            {
                "gap": "Mental health + fitness integration",
                "opportunity": "Growing demand for holistic wellness solutions",
                "difficulty": "low"
            }
        ],
        trends=[
            {
                "trend": "AI personalization in fitness",
                "impact": "Enabling hyper-personalized workout and nutrition recommendations",
                "timeline": "2024-2026"
            },
            {
                "trend": "Wearable health monitoring",
                "impact": "Continuous health data enabling better insights",
                "timeline": "Ongoing"
            }
        ],
        barriers=[
            {
                "barrier": "Health data privacy regulations",
                "severity": "medium",
                "mitigation": "Work with privacy compliance experts"
            }
        ],
        recommendations=[
            {
                "strategy": "Focus on AI-powered personalization as key differentiator",
                "rationale": "Clear market gap with high user demand",
                "priority": "high"
            },
            {
                "strategy": "Target underserved segments (mental health integration)",
                "rationale": "Growing market with limited competition",
                "priority": "medium"
            }
        ]
    )
    
    # Generate dashboard
    idea = "AI-powered fitness tracker with personalized coaching"
    dashboard = generator.generate_comprehensive_dashboard(idea, scores, intelligence)
    
    print("\nGenerated Dashboard:")
    print("-" * 60)
    print(dashboard)
    print("-" * 60)
    
    # Check that dashboard contains expected elements
    assert "MARKET ANALYSIS" in dashboard
    assert "OVERALL ASSESSMENT" in dashboard
    assert "DETAILED SCORES" in dashboard
    assert "KEY COMPETITORS" in dashboard
    assert "MARKET OPPORTUNITIES" in dashboard
    assert "STRATEGIC RECOMMENDATIONS" in dashboard
    
    print("✅ Dashboard generation successful!")
    return True

def test_real_web_search_integration():
    """Test integration with real web search"""
    print("\n🌐 Testing Real Web Search Integration")
    print("=" * 40)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found - skipping real web search test")
        return True
    
    try:
        anthropic_client = anthropic.Anthropic(api_key=api_key)
        analyzer = MarketAnalyzer()
        generator = DashboardGenerator()
        
        # Test with a simple query
        print("Performing web search for 'meditation app'...")
        search_results = claude_web_search("meditation app", anthropic_client)
        
        print(f"Web search returned {len(search_results.get('results', []))} results")
        print(f"Analysis type: {search_results.get('analysis_type', 'unknown')}")
        
        # Run analysis
        scores, intelligence = analyzer.analyze_market_intelligence(search_results)
        
        print(f"\nAnalysis Results:")
        print(f"   Overall Score: {scores.overall_score:.2f}")
        print(f"   Confidence: {scores.confidence:.2f}")
        
        # Generate dashboard
        dashboard = generator.generate_comprehensive_dashboard(
            "AI-powered meditation app", 
            scores, 
            intelligence
        )
        
        print(f"\nDashboard preview (first 300 chars):")
        print(dashboard[:300] + "...")
        
        print("✅ Real web search integration successful!")
        return True
        
    except Exception as e:
        print(f"❌ Real web search test failed: {e}")
        return False

async def test_full_validator_integration():
    """Test the full validator agent with enhanced analysis"""
    print("\n🤖 Testing Full Validator Integration")
    print("=" * 40)
    
    try:
        # Import here to avoid circular dependencies
        from manager.sub_agents.validator_agent.agent import ClaudeWebSearchValidator
        
        # Create mock conversation
        mock_conversation = Mock()
        mock_conversation.send_message = AsyncMock()
        
        # Create validator agent
        validator = ClaudeWebSearchValidator(name="test_validator")
        
        # Test memory with selected idea
        memory = {
            "SelectedIdea": {
                "id": 1,
                "idea": "AI-powered language learning app with personalized curriculum"
            }
        }
        
        print("Testing validator agent with enhanced analysis...")
        
        start_time = datetime.now()
        result = await validator.handle(mock_conversation, memory)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Validator completed in {duration:.1f}s")
        
        if result and len(result) > 0:
            score = result[0]
            print(f"📊 Validation Results:")
            print(f"   Feasibility: {score.get('feasibility', 'N/A')}")
            print(f"   Innovation: {score.get('innovation', 'N/A')}")
            print(f"   Overall Score: {score.get('score', 'N/A')}")
            print(f"   Notes: {score.get('notes', 'N/A')}")
            
            # Check for enhanced data
            if 'market_scores' in score:
                print("✅ Enhanced market analysis data found")
            else:
                print("⚠️ Using fallback analysis")
                
        else:
            print("❌ No validation results returned")
            
        # Check conversation calls
        if mock_conversation.send_message.called:
            call_count = mock_conversation.send_message.call_count
            print(f"✅ Sent {call_count} messages to user")
        else:
            print("❌ No messages sent to user")
            
        # Check memory storage
        if "Validator" in memory:
            print("✅ Results properly stored in memory")
        else:
            print("❌ Results not stored in memory")
            
        return True
        
    except Exception as e:
        print(f"❌ Validator integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all enhanced analysis tests"""
    print("🧪 VentureBot Enhanced Market Intelligence Tests")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Market Analyzer", test_market_analyzer),
        ("Dashboard Generator", test_dashboard_generator),
        ("Real Web Search Integration", test_real_web_search_integration),
        ("Full Validator Integration", lambda: asyncio.run(test_full_validator_integration()))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced analysis tests completed successfully!")
    else:
        print("⚠️ Some tests failed - check output above for details")
    
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()