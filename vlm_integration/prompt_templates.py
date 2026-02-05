"""
Prompt Templates for VLM Financial Analysis
============================================

This module contains all prompt templates used for the Visual-Time-Series
Reasoning Pipeline. These prompts are specifically designed to help LLaVA
understand and analyze financial dashboard screenshots.

Key Components:
- System prompts for financial analyst context
- Chat prompts for user questions
- Snapshot summary prompts for automatic descriptions
- Correlation analysis prompts
- Trend detection prompts
"""

from typing import Optional, Dict, List


class PromptTemplates:
    """
    Collection of prompt templates for VLM-based financial analysis.

    All prompts are designed to:
    1. Provide clear context about the financial dashboard
    2. Guide the model to focus on relevant visual elements
    3. Request structured, actionable insights
    4. Handle various types of user questions
    """

    # =========================================================================
    # SYSTEM PROMPTS
    # =========================================================================

    FINANCIAL_ANALYST_SYSTEM = """You are an expert financial analyst AI assistant specializing in visual analysis of market dashboards and time-series data.

Your capabilities:
- Analyze price charts and identify trends (upward, downward, sideways)
- Detect correlations between different commodities (gold, silver, oil)
- Identify volatility patterns and significant price movements
- Provide clear, actionable insights based on visual data
- Explain complex financial patterns in simple terms

When analyzing dashboard images:
1. Focus on the actual chart data visible in the image
2. Identify the time period shown
3. Note any significant price changes or patterns
4. Compare different commodities if relevant
5. Be specific about what you observe

Always be:
- Accurate: Only describe what you can clearly see
- Concise: Provide focused, relevant answers
- Helpful: Explain the significance of patterns
- Cautious: Don't make unsupported predictions"""  # noqa: E501

    # =========================================================================
    # SNAPSHOT SUMMARY PROMPTS
    # =========================================================================

    SNAPSHOT_SUMMARY_PROMPT = """Analyze this financial dashboard snapshot and provide a brief summary.

Focus on:
1. Current price levels for Gold, Silver, and Oil (from KPI cards)
2. Recent price trends (from the line charts)
3. Any notable patterns or significant changes
4. The relative performance of each commodity

Provide a 2-3 sentence summary that captures the key market state shown in this dashboard.
Be specific about the values and trends you observe."""  # noqa: E501

    DETAILED_ANALYSIS_PROMPT = """Perform a comprehensive analysis of this financial dashboard.

Analyze each section:

1. KPI CARDS (Top Section):
   - Current prices for Gold, Silver, Oil
   - 24-hour changes (up/down indicators)

2. COMPARISON CHARTS (Bar/Pie):
   - Relative price levels
   - Distribution of values

3. TREND CHARTS (Line Charts):
   - Gold price trend direction and pattern
   - Silver price trend direction and pattern
   - Oil price trend direction and pattern
   - Any crossovers or divergences

4. OVERALL MARKET STATE:
   - Which commodities are performing well/poorly
   - Volatility assessment
   - Any correlations between commodities

Provide a structured analysis with specific observations."""

    # =========================================================================
    # CORRELATION ANALYSIS PROMPTS
    # =========================================================================

    CORRELATION_PROMPT_TEMPLATE = """Analyze the correlation between {commodity1} and {commodity2} based on the charts in this dashboard.

Look for:
1. Do they move in the same direction (positive correlation)?
2. Do they move in opposite directions (negative correlation)?
3. Is there no clear relationship (no correlation)?

Examine the trend charts and explain:
- The visual pattern you observe
- When the prices moved together or diverged
- The strength of any correlation (strong, moderate, weak)

Provide a clear explanation based on what you see in the charts."""  # noqa: E501

    # =========================================================================
    # TREND ANALYSIS PROMPTS
    # =========================================================================

    TREND_ANALYSIS_TEMPLATE = """Analyze the {commodity} price trend shown in this dashboard.

Focus on:
1. Overall direction (upward, downward, or sideways)
2. Trend strength (steep or gradual)
3. Any reversal points or significant changes
4. Recent momentum (accelerating or decelerating)
5. Current price level relative to the trend

Describe the trend pattern and what it might indicate about market sentiment."""

    VOLATILITY_ANALYSIS_PROMPT = """Assess the volatility of each commodity shown in this dashboard.

For each (Gold, Silver, Oil), examine:
1. Price swing amplitude (high peaks vs low troughs)
2. Frequency of price changes
3. Stability vs instability of the trend line

Rank them from most to least volatile and explain your assessment."""

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @classmethod
    def build_chat_prompt(
        cls,
        user_question: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Build a complete prompt for user chat questions.

        Args:
            user_question: The user's question about the dashboard
            context: Optional context data (commodity prices, dates, etc.)

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add context if available
        if context:
            prompt_parts.append("Dashboard Context:")
            if "latest_date" in context:
                prompt_parts.append(f"- Data as of: {context['latest_date']}")
            if "commodities" in context:
                for name, data in context["commodities"].items():
                    if "price" in data:
                        prompt_parts.append(f"- {name}: ${data['price']:.2f}")
            prompt_parts.append("")

        # Add the user's question
        prompt_parts.append(f"User Question: {user_question}")
        prompt_parts.append("")

        # Add analysis instructions
        prompt_parts.append("""Analyze the dashboard image to answer this question.
Be specific about what you observe in the charts and KPI cards.
If the question asks about correlations, compare the trend lines.""")

        return "\n".join(prompt_parts)

    @classmethod
    def build_correlation_prompt(cls, commodity1: str, commodity2: str) -> str:
        """Build a prompt for correlation analysis between two commodities."""
        return cls.CORRELATION_PROMPT_TEMPLATE.format(
            commodity1=commodity1,
            commodity2=commodity2
        )

    @classmethod
    def build_trend_prompt(cls, commodity: str) -> str:
        """Build a prompt for trend analysis of a specific commodity."""
        return cls.TREND_ANALYSIS_TEMPLATE.format(commodity=commodity)

    @classmethod
    def get_example_questions(cls) -> List[str]:
        """Return a list of example questions users can ask."""
        return [
            "What's the correlation between gold and oil prices?",
            "Which commodity is most volatile right now?",
            "Is gold trending upward or downward?",
            "How do silver prices compare to gold?",
            "What are the current price levels for all commodities?",
            "Are there any significant price changes in the last 24 hours?",
            "What's the overall market sentiment based on these charts?",
            "Which commodity has performed best recently?",
        ]
