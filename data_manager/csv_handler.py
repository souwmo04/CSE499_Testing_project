"""
CSV Handler - Data Loading and Processing
==========================================

This module handles loading and processing of financial CSV data.
Provides utilities for the dashboard and VLM integration.
"""

import os
import pandas as pd
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class CSVHandler:
    """
    Handler for financial CSV data operations.

    Provides:
    - Data loading and caching
    - Statistical calculations
    - Data formatting for charts
    - Change detection
    """

    def __init__(self, csv_path: str):
        """
        Initialize the CSV handler.

        Args:
            csv_path: Path to the financial data CSV file
        """
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._last_modified: Optional[float] = None

    def _check_file_changed(self) -> bool:
        """Check if the CSV file has been modified since last load."""
        try:
            current_mtime = os.path.getmtime(self.csv_path)
            if self._last_modified is None or current_mtime > self._last_modified:
                return True
            return False
        except OSError:
            return True

    def load(self, force: bool = False) -> Optional[pd.DataFrame]:
        """
        Load the CSV data, with caching.

        Args:
            force: Force reload even if cached

        Returns:
            DataFrame with the loaded data or None if failed
        """
        if not force and self._df is not None and not self._check_file_changed():
            return self._df

        try:
            self._df = pd.read_csv(self.csv_path)
            self._last_modified = os.path.getmtime(self.csv_path)
            logger.info(f"Loaded CSV with {len(self._df)} rows")
            return self._df
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return None

    def get_chart_data(self) -> Dict[str, List]:
        """
        Get data formatted for Chart.js.

        Returns:
            Dict with dates, gold, silver, oil lists
        """
        df = self.load()
        if df is None:
            return {"dates": [], "gold": [], "silver": [], "oil": []}

        return {
            "dates": df['date'].tolist(),
            "gold": df['gold_price'].tolist(),
            "silver": df['silver_price'].tolist(),
            "oil": df['oil_price'].tolist()
        }

    def get_latest_values(self) -> Dict[str, Any]:
        """
        Get the most recent values from the data.

        Returns:
            Dict with latest prices and date
        """
        df = self.load()
        if df is None or len(df) == 0:
            return {}

        latest = df.iloc[-1]
        return {
            "date": latest['date'],
            "gold": float(latest['gold_price']),
            "silver": float(latest['silver_price']),
            "oil": float(latest['oil_price'])
        }

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics for each commodity.

        Returns:
            Dict with min, max, mean, std for each commodity
        """
        df = self.load()
        if df is None or len(df) == 0:
            return {}

        stats = {}
        for col in ['gold_price', 'silver_price', 'oil_price']:
            name = col.replace('_price', '')
            stats[name] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "latest": float(df[col].iloc[-1])
            }

        return stats

    def get_changes(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate price changes (daily and from start).

        Returns:
            Dict with change information for each commodity
        """
        df = self.load()
        if df is None or len(df) < 2:
            return {}

        changes = {}
        for col in ['gold_price', 'silver_price', 'oil_price']:
            name = col.replace('_price', '')
            latest = df[col].iloc[-1]
            previous = df[col].iloc[-2]
            first = df[col].iloc[0]

            daily_change = latest - previous
            total_change = latest - first
            daily_pct = (daily_change / previous) * 100 if previous != 0 else 0
            total_pct = (total_change / first) * 100 if first != 0 else 0

            changes[name] = {
                "daily_change": float(daily_change),
                "daily_pct": float(daily_pct),
                "total_change": float(total_change),
                "total_pct": float(total_pct)
            }

        return changes

    def get_summary_for_vlm(self) -> str:
        """
        Generate a text summary of the data for VLM context.

        Returns:
            String summary of current market state
        """
        stats = self.get_statistics()
        changes = self.get_changes()
        latest = self.get_latest_values()

        if not stats or not latest:
            return "No data available"

        lines = [
            f"Data as of: {latest.get('date', 'Unknown')}",
            "",
            "Current Prices:",
            f"  Gold: ${latest.get('gold', 0):.2f}",
            f"  Silver: ${latest.get('silver', 0):.2f}",
            f"  Oil: ${latest.get('oil', 0):.2f}",
            "",
            "24-Hour Changes:",
        ]

        for name in ['gold', 'silver', 'oil']:
            if name in changes:
                c = changes[name]
                direction = "↑" if c['daily_change'] >= 0 else "↓"
                lines.append(
                    f"  {name.title()}: {direction} ${abs(c['daily_change']):.2f} ({c['daily_pct']:+.1f}%)"
                )

        return "\n".join(lines)


def get_csv_handler(base_dir: str) -> CSVHandler:
    """
    Get a CSV handler instance for the default data file.

    Args:
        base_dir: Django BASE_DIR path

    Returns:
        CSVHandler instance
    """
    csv_path = os.path.join(base_dir, 'data', 'financial_data.csv')
    return CSVHandler(csv_path)
