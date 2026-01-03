"""
MCP Stock Server - Professional Financial Data Provider

A production-ready Model Context Protocol (MCP) server that provides comprehensive
stock market data functionality. Designed for integration with Claude and other
AI assistants to enable intelligent financial analysis.

Features:
- Real-time stock price retrieval with intelligent fallback
- Stock comparison and relative valuation
- Market fundamentals and key metrics
- Market summary and index tracking
- Robust error handling and logging
- CSV fallback for offline capability
- Type-safe tool definitions with detailed schemas

Available Tools:
1. get_stock_price: Current price for any ticker symbol
2. compare_stocks: Compare two stocks side-by-side
3. get_stock_fundamentals: Key metrics and financial ratios
4. get_market_summary: Overview of major market indices

Architecture:
- Fallback Strategy: Yahoo Finance API → Local CSV file
- Data Sources: yfinance, pandas
- Protocol: Model Context Protocol (MCP)
- Server Framework: FastMCP

Example Claude Integration:
    "What's the current price of Apple stock and how does it compare to Microsoft?"
    → Uses get_stock_price and compare_stocks tools

Author: AI Assistant
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
import yfinance as yf
import pandas as pd
import os

# ============================================================================
# Configuration
# ============================================================================

# Get paths from environment or use defaults
CSV_FILE_PATH = os.getenv(
    "STOCK_CSV_PATH",
    r"d:\AI ML Work\Stock MCP\stocks_data.csv"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Stock Server")


# ============================================================================
# Data Retrieval Functions
# ============================================================================

def get_price_from_csv(symbol: str) -> Optional[float]:
    """
    Retrieve stock price from local CSV file (fallback mechanism).
    
    This function serves as a fallback when Yahoo Finance API is unavailable.
    It reads from a CSV file with the expected format:
        symbol,price
        AAPL,175.64
        MSFT,330.21
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Stock price as float if found, None otherwise
        
    Raises:
        None (logs errors instead)
    """
    try:
        if not os.path.exists(CSV_FILE_PATH):
            logger.warning(f"CSV file not found: {CSV_FILE_PATH}")
            return None
            
        df = pd.read_csv(CSV_FILE_PATH)
        df['symbol'] = df['symbol'].str.upper()
        symbol = symbol.upper()
        
        stock_row = df[df['symbol'] == symbol]
        
        if not stock_row.empty:
            price = float(stock_row['price'].iloc[0])
            logger.info(f"Retrieved {symbol} from CSV fallback: ${price:.2f}")
            return price
        else:
            logger.warning(f"Symbol {symbol} not found in CSV")
            return None
            
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return None


def get_stock_price_with_fallback(symbol: str) -> tuple[Optional[float], str]:
    """
    Retrieve stock price with intelligent fallback mechanism.
    
    Attempts to fetch price from Yahoo Finance first, then falls back to
    local CSV file if API is unavailable. This ensures reliability even
    when external APIs are down.
    
    Data Priority:
    1. Yahoo Finance API (real-time data)
    2. Local CSV file (cached fallback)
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Tuple of (price: float, source: str) where source is 'yfinance' or 'csv'
        Returns (None, 'none') if price cannot be retrieved from any source
        
    Example:
        >>> price, source = get_stock_price_with_fallback("AAPL")
        >>> print(f"${price} from {source}")
        $175.64 from yfinance
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Attempt to get today's data
        data = ticker.history(period="1d")
        
        if not data.empty:
            price = float(data['Close'].iloc[-1])
            logger.info(f"Retrieved {symbol} from Yahoo Finance: ${price:.2f}")
            return price, 'yfinance'
        
        # Fallback to ticker info if daily data unavailable
        info = ticker.info
        price = info.get("regularMarketPrice")
        
        if price is not None:
            logger.info(f"Retrieved {symbol} from Yahoo Finance (info): ${price:.2f}")
            return price, 'yfinance'
    
    except Exception as e:
        logger.debug(f"Yahoo Finance error for {symbol}: {type(e).__name__}")
    
    # Use CSV as final fallback
    csv_price = get_price_from_csv(symbol)
    if csv_price is not None:
        return csv_price, 'csv'
    
    logger.error(f"Could not retrieve price for {symbol} from any source")
    return None, 'none'


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """
    Retrieve the current stock price for a given ticker symbol.
    
    Fetches real-time or near-real-time stock price data using Yahoo Finance API
    with local CSV file as fallback. Automatically handles symbol normalization
    and provides clear error messages.
    
    Data Sources:
    - Primary: Yahoo Finance API (real-time)
    - Fallback: Local CSV file (stocks_data.csv)
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
               Case-insensitive, whitespace-trimmed
    
    Returns:
        Formatted string with current price and data source information
        
    Examples:
        get_stock_price("AAPL")
        → "Current price of AAPL is $175.64 (from Yahoo Finance)"
        
        get_stock_price("INVALID")
        → "ERROR: Could not retrieve price for INVALID..."
    
    Raises:
        None (returns error message instead)
    """
    symbol = symbol.strip().upper()
    logger.info(f"get_stock_price called for {symbol}")
    
    price, source = get_stock_price_with_fallback(symbol)
    
    if price is not None:
        source_text = "from Yahoo Finance" if source == 'yfinance' else "from local data"
        return f"Current price of {symbol} is ${price:.2f} ({source_text})"
    else:
        return (f"ERROR: Could not retrieve price for {symbol}. "
                f"Please verify the symbol is correct. Data sources: "
                f"Yahoo Finance API, local CSV file ({CSV_FILE_PATH})")


@mcp.tool()
def compare_stocks(symbol1: str, symbol2: str) -> str:
    """
    Compare the current prices of two stock symbols.
    
    Retrieves prices for both symbols and provides a detailed comparison
    including absolute difference and percentage change. Useful for relative
    valuation and investment decision-making.
    
    Args:
        symbol1: First stock ticker symbol
        symbol2: Second stock ticker symbol
    
    Returns:
        Formatted comparison string with price difference and percentage
        
    Examples:
        compare_stocks("AAPL", "MSFT")
        → "AAPL ($175.64) is $154.57 (46.88%) lower than MSFT ($330.21)"
        
        compare_stocks("AAPL", "AAPL")
        → "Both AAPL and AAPL have the same price ($175.64)"
    
    Raises:
        None (returns error message instead)
    """
    symbol1 = symbol1.strip().upper()
    symbol2 = symbol2.strip().upper()
    
    logger.info(f"compare_stocks called: {symbol1} vs {symbol2}")
    
    price1, _ = get_stock_price_with_fallback(symbol1)
    price2, _ = get_stock_price_with_fallback(symbol2)
    
    if price1 is None:
        return f"ERROR: Could not retrieve price for {symbol1}"
    if price2 is None:
        return f"ERROR: Could not retrieve price for {symbol2}"
    
    difference = abs(price1 - price2)
    min_price = min(price1, price2)
    percentage = (difference / min_price * 100) if min_price > 0 else 0
    
    if price1 > price2:
        return (f"{symbol1} (${price1:.2f}) is ${difference:.2f} "
                f"({percentage:.2f}%) higher than {symbol2} (${price2:.2f})")
    elif price1 < price2:
        return (f"{symbol1} (${price1:.2f}) is ${difference:.2f} "
                f"({percentage:.2f}%) lower than {symbol2} (${price2:.2f})")
    else:
        return f"Both {symbol1} and {symbol2} have the same price (${price1:.2f})"


@mcp.tool()
def get_stock_fundamentals(symbol: str) -> str:
    """
    Retrieve key financial fundamentals and metrics for a stock.
    
    Provides essential financial ratios and metrics including P/E ratio,
    market cap, dividend yield, and 52-week range. Useful for fundamental
    analysis and value assessment.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        Formatted string with key financial metrics
        
    Examples:
        get_stock_fundamentals("AAPL")
        → "Apple Inc (AAPL) Fundamentals:
           Market Cap: $2.9T
           P/E Ratio: 28.5
           Dividend Yield: 0.42%
           52-Week Range: $154.30 - $199.62"
    
    Notes:
        - Not all metrics are available for all stocks
        - Data sourced from Yahoo Finance
        - Metrics may be delayed by 15-20 minutes
    
    Raises:
        None (returns error message instead)
    """
    symbol = symbol.strip().upper()
    logger.info(f"get_stock_fundamentals called for {symbol}")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract key fundamentals
        name = info.get("longName", "N/A")
        market_cap = info.get("marketCap")
        pe_ratio = info.get("trailingPE")
        dividend_yield = info.get("dividendYield")
        week_52_high = info.get("fiftyTwoWeekHigh")
        week_52_low = info.get("fiftyTwoWeekLow")
        current_price = info.get("regularMarketPrice")
        
        # Format output
        result = f"**{name} ({symbol}) - Financial Fundamentals**\n\n"
        
        if current_price:
            result += f"Current Price: ${current_price:.2f}\n"
        if market_cap:
            market_cap_formatted = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
            result += f"Market Capitalization: {market_cap_formatted}\n"
        if pe_ratio:
            result += f"P/E Ratio: {pe_ratio:.2f}\n"
        if dividend_yield:
            result += f"Dividend Yield: {dividend_yield*100:.2f}%\n"
        if week_52_low and week_52_high:
            result += f"52-Week Range: ${week_52_low:.2f} - ${week_52_high:.2f}\n"
        
        if result == f"**{name} ({symbol}) - Financial Fundamentals**\n\n":
            return f"Limited fundamental data available for {symbol}. Some metrics may not be available."
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving fundamentals for {symbol}: {e}")
        return f"ERROR: Could not retrieve fundamentals for {symbol}. {str(e)}"


@mcp.tool()
def get_market_summary() -> str:
    """
    Retrieve summary data for major market indices.
    
    Provides current price information for key US market indices including
    the S&P 500, Dow Jones Industrial Average, and NASDAQ Composite. Useful
    for assessing overall market health and trends.
    
    Returns:
        Formatted string with current index prices and daily changes
        
    Example:
        get_market_summary()
        → "Market Summary
           S&P 500 (^GSPC): 4,783.45 (+0.52%)
           Dow Jones (^DJI): 42,221.33 (-0.15%)
           NASDAQ (^IXIC): 15,043.24 (+1.23%)"
    
    Notes:
        - Data sourced from Yahoo Finance
        - Indices update during market hours
        - May be delayed 15-20 minutes
        - Percentages show daily change
    
    Raises:
        None (returns error message instead)
    """
    logger.info("get_market_summary called")
    
    indices = {
        "S&P 500": "^GSPC",
        "Dow Jones": "^DJI",
        "NASDAQ": "^IXIC"
    }
    
    try:
        result = "**Market Summary**\n\n"
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                price = info.get("regularMarketPrice")
                change = info.get("regularMarketChange")
                change_pct = info.get("regularMarketChangePercent")
                
                if price:
                    change_str = f"+{change:.2f}" if change and change >= 0 else f"{change:.2f}" if change else "N/A"
                    pct_str = f"+{change_pct:.2f}%" if change_pct and change_pct >= 0 else f"{change_pct:.2f}%" if change_pct else "N/A"
                    
                    result += f"{name} ({symbol}): ${price:,.2f} ({change_str}, {pct_str})\n"
                else:
                    result += f"{name} ({symbol}): Data unavailable\n"
                    
            except Exception as e:
                logger.warning(f"Could not retrieve data for {name}: {e}")
                result += f"{name} ({symbol}): Error retrieving data\n"
        
        result += "\n*Data sourced from Yahoo Finance (may be delayed 15-20 minutes)*"
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving market summary: {e}")
        return f"ERROR: Could not retrieve market summary. {str(e)}"



# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    """
    Entry point for the Stock MCP Server.
    
    Starts the FastMCP server which:
    1. Registers all available tools (get_stock_price, compare_stocks, etc.)
    2. Listens for MCP client connections
    3. Handles tool execution requests from Claude and other AI assistants
    
    The server provides robust financial data retrieval with multiple data sources.
    
    CSV File Format (fallback):
        symbol,price
        AAPL,175.64
        MSFT,330.21
        GOOGL,135.45
    
    Environment Variables:
        STOCK_CSV_PATH: Path to CSV fallback file (optional)
    
    Server Details:
        - Server Name: "Stock Server"
        - Protocol: Model Context Protocol (MCP)
        - Primary Data Source: Yahoo Finance API
        - Fallback Data Source: Local CSV file
        - Tools: 4 (get_stock_price, compare_stocks, get_stock_fundamentals, get_market_summary)
    
    Logs:
        - Standard output (console)
        - Configured via Python logging module
    """
    logger.info("=" * 80)
    logger.info("Stock MCP Server starting...")
    logger.info("Available tools: get_stock_price, compare_stocks, get_stock_fundamentals, get_market_summary")
    logger.info("CSV Fallback Path: " + CSV_FILE_PATH)
    logger.info("=" * 80)
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
