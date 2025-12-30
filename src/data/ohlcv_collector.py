"""
🌙 OHLCV Data Collector
Collects Open-High-Low-Close-Volume data for specified tokens
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Safe config imports with fallbacks
try:
    from src.config import *
except ImportError:
    # Fallback defaults if config doesn't exist
    MONITORED_TOKENS = []
    DAYSBACK_4_DATA = 1
    DATA_TIMEFRAME = '5m'
    SAVE_OHLCV_DATA = False

try:
    from termcolor import colored, cprint
except Exception:
    def cprint(msg, *args, **kwargs):
        print(msg)
    def colored(msg, *args, **kwargs):
        return msg

try:
    import pandas as pd
except Exception:
    pd = None

# ============================================================================
# IMPORT HYPERLIQUID MODULE AT TOP LEVEL - CRITICAL FIX!
# ============================================================================
hl = None
try:
    # Try importing from src/ folder first
    from src import nice_funcs_hyperliquid as hl
    print("✅ Loaded nice_funcs_hyperliquid from src/")
except ImportError:
    try:
        # Try importing from root level as fallback
        import nice_funcs_hyperliquid as hl
        print("✅ Loaded nice_funcs_hyperliquid from root")
    except ImportError:
        print("⚠️ Warning: nice_funcs_hyperliquid not found!")
        hl = None

# Import Solana functions if needed
n = None
try:
    from src import nice_funcs as n
except ImportError:
    n = None

# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

def collect_token_data(token, days_back=1, timeframe='5m', exchange="SOLANA"):
    """Collect OHLCV data for a single token

    Args:
        token: Token symbol (BTC, ETH) for Aster/HyperLiquid/Extended OR contract address for Solana
        days_back: Days of historical data to fetch
        timeframe: Candle timeframe (1m, 5m, 15m, 1H, etc.)
        exchange: "SOLANA", "ASTER", "HYPERLIQUID", or "EXTENDED"
    """
    cprint(f"\n🤖 AI Agent fetching data for {token}...", "white", "on_blue")

    try:
        # Calculate number of bars based on timeframe and days
        bars_per_day = {
            '1m': 1440, '3m': 480, '5m': 288, '15m': 96, '30m': 48,
            '1H': 24, '2H': 12, '4H': 6, '6H': 4, '8H': 3, '12H': 2,
            '1h': 24, '2h': 12, '4h': 6, '6h': 4, '8h': 3, '12h': 2,  # lowercase versions
            '1D': 1, '3D': 1/3, '1W': 1/7, '1M': 1/30,
            '1d': 1, '3d': 1/3, '1w': 1/7, '1month': 1/30  # lowercase versions
        }

        bars_needed = int(days_back * bars_per_day.get(timeframe, 24))  # Default to hourly if unknown
        cprint(f"📊 Calculating bars: {days_back} days × {timeframe} = {bars_needed} bars", "cyan")

        # Convert timeframe to HyperLiquid format (lowercase h for hours)
        hl_timeframe = timeframe.replace('H', 'h').replace('D', 'd').replace('W', 'w').replace('M', 'month')
        if hl_timeframe != timeframe:
            cprint(f"🔄 Converting timeframe: {timeframe} → {hl_timeframe} (for HyperLiquid)", "yellow")

        # Route to appropriate data source based on exchange
        if exchange in ["HYPERLIQUID", "ASTER", "EXTENDED"]:
            # Use HyperLiquid API (works for all perp exchanges)
            cprint(f"🦈 Using HyperLiquid API for {token}", "cyan")
            
            if hl is None:
                cprint(f"❌ HyperLiquid module not available!", "red")
                cprint(f"💡 Make sure nice_funcs_hyperliquid.py exists in src/ folder", "yellow")
                return None
            
            try:
                data = hl.get_data(
                    symbol=token, 
                    timeframe=hl_timeframe, 
                    bars=bars_needed, 
                    add_indicators=True
                )
                cprint(f"✅ Successfully fetched {len(data) if data is not None else 0} bars from HyperLiquid", "green")
            except Exception as e:
                cprint(f"❌ Error fetching from HyperLiquid: {e}", "red")
                import traceback
                traceback.print_exc()
                return None
                
        else:
            # Default: Use Solana/Birdeye API
            cprint(f"🦜 Using Solana/Birdeye API for {token}", "cyan")
            
            if n is None:
                cprint(f"❌ Solana module not available!", "red")
                return None
                
            try:
                data = n.get_data(token, days_back, timeframe)
            except Exception as e:
                cprint(f"⚠️ Solana helper error: {e}", "yellow")
                import traceback
                traceback.print_exc()
                return None

        # Check if data is empty
        is_empty = False
        if data is None:
            is_empty = True
        else:
            if pd is not None:
                try:
                    if hasattr(data, 'empty') and data.empty:
                        is_empty = True
                except Exception:
                    pass
            else:
                # Fallback: check length
                try:
                    if len(data) == 0:
                        is_empty = True
                except Exception:
                    is_empty = False

        if is_empty:
            cprint(f"❌ AI Agent couldn't fetch data for {token}", "white", "on_red")
            return None

        cprint(f"📊 AI Agent processed {len(data)} candles for analysis", "white", "on_blue")
        
        # Save data if configured
        try:
            save_dir = "data" if SAVE_OHLCV_DATA else "temp_data"
            save_path = f"{save_dir}/{token}_latest.csv"
            
            # Ensure directory exists
            os.makedirs(save_dir, exist_ok=True)
            
            # Save to CSV (if supported)
            if hasattr(data, 'to_csv'):
                data.to_csv(save_path)
                cprint(f"💾 AI Agent cached data for {token[:8]}", "white", "on_green")
        except Exception as e:
            cprint(f"⚠️ Failed to save data to CSV for {token}: {e}", "yellow")
        
        return data
        
    except Exception as e:
        cprint(f"❌ AI Agent encountered an error: {str(e)}", "white", "on_red")
        import traceback
        traceback.print_exc()
        return None

def collect_all_tokens(tokens=None, days_back=None, timeframe=None, exchange="SOLANA"):
    """
    Collect OHLCV data for all monitored tokens

    Args:
        tokens: List of token symbols (BTC, ETH for Aster/HyperLiquid/Extended) OR addresses (for Solana)
        days_back: Days of historical data (defaults to DAYSBACK_4_DATA from config)
        timeframe: Bar timeframe (defaults to DATA_TIMEFRAME from config)
        exchange: "SOLANA", "ASTER", "HYPERLIQUID", or "EXTENDED"
    """
    market_data = {}

    # Use defaults from config if not provided
    if tokens is None:
        tokens = MONITORED_TOKENS if MONITORED_TOKENS else []
    if days_back is None:
        days_back = DAYSBACK_4_DATA if 'DAYSBACK_4_DATA' in globals() else 1
    if timeframe is None:
        timeframe = DATA_TIMEFRAME if 'DATA_TIMEFRAME' in globals() else '5m'

    cprint("\n🔍 Moon Dev's AI Agent starting market data collection...", "white", "on_blue")
    cprint(f"🦈 Exchange: {exchange}", "cyan")
    cprint(f"📊 Settings: {days_back} days @ {timeframe} timeframe", "cyan")
    cprint(f"🎯 Tokens: {len(tokens)}", "cyan")

    if not tokens:
        cprint("⚠️ No tokens provided to collect data for!", "yellow")
        return market_data

    for i, token in enumerate(tokens, 1):
        cprint(f"\n[{i}/{len(tokens)}] Processing {token}...", "cyan")
        data = collect_token_data(token, days_back, timeframe, exchange=exchange)
        if data is not None:
            market_data[token] = data
            cprint(f"✅ {token} data collected successfully", "green")
        else:
            cprint(f"⚠️ {token} data collection failed", "yellow")

    cprint(f"\n✨ AI Agent completed market data collection!", "white", "on_green")
    cprint(f"📊 Successfully collected {len(market_data)}/{len(tokens)} tokens", "cyan")

    return market_data

if __name__ == "__main__":
    try:
        # Test collection
        print("\n🧪 Testing OHLCV Collector...")
        
        # Test HyperLiquid data collection
        if hl is not None:
            print("\n📊 Testing HyperLiquid collection...")
            test_data = collect_all_tokens(
                tokens=['BTC', 'ETH'],
                days_back=1,
                timeframe='5m',
                exchange='HYPERLIQUID'
            )
            print(f"✅ Collected data for {len(test_data)} tokens")
        else:
            print("⚠️ HyperLiquid module not available for testing")
            
    except KeyboardInterrupt:
        print("\n👋 OHLCV Collector shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("🔧 Moon Dev suggests checking the logs and trying again!")
