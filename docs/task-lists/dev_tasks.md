[dev_tasks.md](https://github.com/user-attachments/files/24407611/dev_tasks.md)
# Development Tasks

**Focus**: Backend functionality, trading logic, data infrastructure  
**Timeline**: 6-8 weeks  
**Priority**: Complete Phases 1-3 before UI work  

---

## Phase 1: Bug Fixes & Cleanup (Week 1)

### 1.1 Fix Duplicate Logs ⚠️ CRITICAL
**Problem**: Same log entries appearing multiple times in front-end  
**Impact**: Console cluttered, hard to debug  
**Solution**:
- Identify source of duplicate emissions
- Add log deduplication logic
- Test with multiple position decisions

**Files**:
- `src/agents/trading_agent.py`
- `src/utils/logger.py`

---

### 1.2 Remove Robot Emojis
**Problem**: 🤖 emoji used inconsistently throughout logs  
**Solution**:
- Find all instances of 🤖 emoji
- Remove from all log statements
- Maintain clean, professional output

**Files**:
- Search globally for `🤖` or `:robot:`

---

### 1.3 Standardize SWARM Logs with ♾️
**Problem**: Swarm mode logs not visually distinct  
**Solution**:
- Use ♾️ emoji for ALL swarm action logs
- Add prefix to swarm-specific log messages
- Clear distinction between Single AI and Swarm mode

**Example**:
```python
# Single AI mode
logger.info("📊 Analyzing market conditions...")

# Swarm mode
logger.info("♾️ Swarm analyzing market conditions...")
logger.info("♾️ Agent 1 suggests LONG BTC")
logger.info("♾️ Agent 2 suggests SHORT ETH")
logger.info("♾️ Consensus reached: LONG BTC")
```

**Files**:
- `src/agents/swarm_agent.py`
- Any swarm-related logging

---

## Phase 2: WebSocket Integration (Week 2-3)

### 2.1 Hyperliquid WebSocket Connection
**Goal**: Replace API polling with real-time WebSocket feed  
**Tasks**:
- Create WebSocket client class
- Connect to `wss://api.hyperliquid.xyz/ws`
- Implement reconnection logic
- Handle connection drops gracefully
- Add error logging

**Files**:
- `src/websocket/hyperliquid_ws.py` (NEW)

---

### 2.2 Price Data Streaming
**Goal**: Real-time price updates  
**Tasks**:
- Subscribe to price channels for monitored tokens
- Parse incoming price messages
- Update internal state
- Emit events for UI updates

**Data Format**:
```json
{
  "channel": "ticker",
  "data": {
    "coin": "BTC",
    "price": 96234.50,
    "volume24h": 2400000000,
    "change24h": 2.3
  }
}
```

---

### 2.3 Order Book Data Feed
**Goal**: Real-time Level 2 orderbook data  
**Tasks**:
- Subscribe to `l2Book` channel
- Parse bid/ask levels
- Calculate orderbook depth
- Update every 100ms

**Data Structure**:
```python
{
  "bids": [
    {"price": 96200, "size": 1.5},
    {"price": 96195, "size": 2.1},
    # ... top 20 levels
  ],
  "asks": [
    {"price": 96210, "size": 0.8},
    {"price": 96215, "size": 1.2},
    # ...
  ]
}
```

**Files**:
- `src/websocket/orderbook_feed.py` (NEW)

---

### 2.4 Replace API Polling
**Goal**: Reduce API calls by using WebSocket data  
**Tasks**:
- Identify all API polling locations
- Replace with WebSocket subscriptions
- Maintain backward compatibility
- Add feature flag for gradual rollout

**Before**:
```python
# Poll every 5 seconds
price = api.get_price("BTC")
```

**After**:
```python
# Real-time from WebSocket
price = ws_client.get_current_price("BTC")
```

---

## Phase 3: Trading Logic Improvements (Week 3-4)

### 3.1 Fix Order of Operations ⚠️ CRITICAL
**Problem**: Bot opens new positions BEFORE closing existing ones  
**Impact**: Allocation conflicts, incorrect position sizing  

**Required Flow**:
```
1. CLOSE existing positions
   ├─ Verify closure is complete
   ├─ Check balance is freed up
   └─ Log closed position details

2. RE-EVALUATE allocation
   ├─ Calculate available balance
   ├─ Determine new position sizes
   └─ Check risk limits

3. OPEN new positions
   ├─ Use updated allocation
   ├─ Execute with correct sizing
   └─ Log new position details
```

**Applies to**:
- Single AI mode
- Swarm mode

**Implementation**:
```python
async def execute_trading_cycle():
    # 1. Close phase
    closed_positions = await close_all_signals()
    await verify_all_closed(closed_positions)
    
    # 2. Re-evaluate phase
    available_balance = get_available_balance()
    allocations = calculate_allocations(available_balance)
    
    # 3. Open phase
    new_positions = await open_new_positions(allocations)
```

**Files**:
- `src/agents/trading_agent.py`
- `src/agents/swarm_agent.py`
- `src/execution/order_manager.py`

---

### 3.2 Smart Leverage System
**Goal**: Agent decides leverage based on confidence + market conditions  
**Requirements**:
- Minimum position value: $12
- Leverage range: 1x to MAX_LEVERAGE
- Dynamic based on:
  - Confidence score (0.0 - 1.0)
  - Market volatility
  - Current drawdown

**Logic**:
```python
def calculate_leverage(confidence, volatility, drawdown):
    base_leverage = 1 + (confidence * 9)  # 1x to 10x
    
    # Reduce in high volatility
    if volatility > 0.05:
        base_leverage *= 0.7
    
    # Reduce if currently in drawdown
    if drawdown > 0.05:
        base_leverage *= 0.5
    
    return max(1.0, min(base_leverage, MAX_LEVERAGE))
```

**Files**:
- `src/risk/leverage_calculator.py` (NEW)

---

### 3.3 Dynamic TP/SL Based on Confidence
**Goal**: TP and SL percentages scale with confidence  
**Ranges**:
- Take Profit: +3% to +8%
- Stop Loss: -1% to -3%

**Logic**:
```python
def calculate_tp_sl(confidence):
    # High confidence = wider TP, tighter SL
    if confidence > 0.8:
        tp = 7.0 + (confidence - 0.8) * 5  # 7-8%
        sl = -1.0 - (confidence - 0.8) * 2  # -1 to -1.4%
    
    # Medium confidence
    elif confidence > 0.6:
        tp = 5.0  # 5%
        sl = -2.0  # -2%
    
    # Low confidence = tighter TP, wider SL
    else:
        tp = 3.0  # 3%
        sl = -3.0  # -3%
    
    return tp, sl
```

**Files**:
- `src/risk/tp_sl_calculator.py` (NEW)

---

### 3.4 Smart P&L Calculation with Fees ⚠️ IMPORTANT
**Goal**: Accurate WIN/LOSS calculation including all costs  
**Problem**: Current calculations don't account for slippage and fees  

**Exit Condition Calculations Must Include**:

1. **Slippage** (realistic execution price vs expected)
   - Estimate: 0.03-0.05% per trade
   - More in volatile markets
   - Track actual vs expected fill prices

2. **Exchange Fees**:
   - **Maker Fee**: ~-0.01% to 0% (rebate or zero)
   - **Taker Fee**: ~0.03-0.05%
   - Calculate based on order type used

3. **Operational Costs** (per cycle):
   - **AI API Cost**: Track tokens used per cycle
   - Example: 10,000 tokens @ $3/million = $0.03 per cycle
   - **Goal**: Agent must WIN enough to cover its own costs
   - **Intrinsic Motivation**: Agent aware it costs money to run

**Implementation**:
```python
def calculate_true_pnl(position):
    # Base P&L
    if position.direction == "LONG":
        price_pnl = (exit_price - entry_price) / entry_price
    else:
        price_pnl = (entry_price - exit_price) / entry_price
    
    # Subtract costs
    slippage = estimate_slippage(position)  # ~0.04%
    entry_fee = get_fee(position.entry_order_type)  # 0.03% taker or -0.01% maker
    exit_fee = get_fee(position.exit_order_type)   # 0.03% taker or -0.01% maker
    
    # Calculate net P&L
    net_pnl = price_pnl - slippage - entry_fee - exit_fee
    
    return net_pnl

def calculate_cycle_cost(tokens_used):
    # AI API cost
    cost_per_million = 3.00  # Claude Sonnet pricing
    api_cost = (tokens_used / 1_000_000) * cost_per_million
    
    return api_cost

def evaluate_cycle_profitability(trades, tokens_used):
    # Total P&L from trades
    total_pnl = sum(calculate_true_pnl(t) for t in trades)
    
    # Operational cost
    cycle_cost = calculate_cycle_cost(tokens_used)
    
    # Net profit (after costs)
    net_profit = total_pnl - cycle_cost
    
    # Agent should see this
    return {
        "gross_pnl": total_pnl,
        "api_cost": cycle_cost,
        "net_pnl": net_profit,
        "profitable": net_profit > 0
    }
```

**Agent Awareness**:
```python
# Include in agent context
cycle_economics = f"""
Your operational costs this cycle:
- AI API tokens used: {tokens_used:,}
- API cost: ${cycle_cost:.4f}
- You need to WIN at least ${cycle_cost:.4f} to break even
- Target: +${cycle_cost * 10:.4f} (10x your cost)
"""
```

**Why This Matters**:
- Agent understands it has operational costs
- Creates motivation to be profitable
- Prevents "trading for the sake of trading"
- Encourages quality over quantity

**Files**:
- `src/risk/tp_sl_calculator.py` (NEW)
- `src/risk/fee_calculator.py` (NEW)
- `src/analytics/cycle_economics.py` (NEW)

---

### 3.5 Trailing Stop Loss
**Goal**: Update SL for winning positions every cycle  
**Rules**:
- Only update for profitable positions
- SL only moves in favorable direction
- Update frequency: Every trading cycle

**Logic**:
```python
def update_trailing_stop(position):
    if not position.is_profitable():
        return
    
    current_price = get_current_price(position.token)
    unrealized_profit_pct = position.get_profit_pct(current_price)
    
    if position.direction == "LONG":
        # Move SL up
        new_sl = current_price * (1 - 0.02)  # 2% below current
        if new_sl > position.stop_loss:
            position.stop_loss = new_sl
    
    else:  # SHORT
        # Move SL down
        new_sl = current_price * (1 + 0.02)  # 2% above current
        if new_sl < position.stop_loss:
            position.stop_loss = new_sl
```

**Files**:
- `src/risk/trailing_stop.py` (NEW)

---

### 3.5 Market Participation Strategy
**Goal**: Agent prefers staying in market  
**Changes**:
- Reduce premature exits
- Hold positions longer (respect cycle minutes)
- Only close on clear signals or SL/TP

**Files**:
- `src/agents/trading_agent.py`

---

### 3.6 Cycle Duration Integration
**Goal**: Agent aware of minimum hold duration  
**Implementation**:
- Add `cycle_minutes` to agent prompt
- Agent considers time remaining in cycle
- Prevents opening positions near cycle end

**Example**:
```python
cycle_info = {
    "cycle_minutes": 15,
    "time_elapsed": 3,
    "time_remaining": 12
}
# Include in agent context
```

**Files**:
- `src/agents/trading_agent.py`
- `src/config/trading_config.py`

---

## Phase 4: Smart Execution Engine (Week 4-5)

### 4.1 Order Book Depth Analysis
**Goal**: Analyze orderbook to inform execution  
**Metrics**:
- Bid/ask depth at top 5 levels
- Cumulative volume
- Orderbook imbalance ratio

```python
def analyze_orderbook(orderbook):
    bid_depth = sum(level["size"] for level in orderbook["bids"][:5])
    ask_depth = sum(level["size"] for level in orderbook["asks"][:5])
    
    imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
    
    return {
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "imbalance": imbalance  # >0 = more bids, <0 = more asks
    }
```

**Files**:
- `src/execution/orderbook_analyzer.py` (NEW)

---

### 4.2 Market vs Limit Order Decision
**Goal**: Choose order type to minimize fees  
**Logic**:
```python
def decide_order_type(spread_pct, urgency, orderbook_depth):
    # Market order if urgent exit
    if urgency == "high":
        return "market"
    
    # Limit order if spread reasonable and depth exists
    if spread_pct < 0.1 and orderbook_depth > THRESHOLD:
        return "limit"
    
    # Market order if spread too wide
    return "market"
```

**Files**:
- `src/execution/order_strategy.py` (NEW)

---

### 4.3 Optimal Limit Price Selection
**Goal**: Place limit orders at optimal price  
**Strategy**:
- BUY: Best bid + 1 tick (for maker rebate)
- SELL: Best ask - 1 tick (for maker rebate)
- Adjust based on urgency

**Files**:
- `src/execution/price_selection.py` (NEW)

---

### 4.4 60-Second Fill Timeout
**Goal**: Ensure limit orders fill quickly  
**Implementation**:
- Place limit order
- Monitor order status
- If not filled in 60s:
  - Cancel limit order
  - Place market order
- Log execution details

**Files**:
- `src/execution/order_manager.py`

---

### 4.5 Execution Quality Tracking
**Goal**: Monitor execution performance  
**Metrics**:
- Limit order fill rate
- Average slippage per trade
- Fee savings vs market orders
- Execution speed

**Files**:
- `src/execution/execution_stats.py` (NEW)

---

## Phase 5: Strategy Integration (Week 6-7)

### 5.1 Bypass strategy_agent.py
**Goal**: Load strategies directly, skip strategy_agent  
**Changes**:
- Keep `strategy_agent.py` file (don't delete)
- Don't call it in execution flow
- Call strategies directly from trading_agent

**Files**:
- `src/agents/trading_agent.py`

---

### 5.2 Dynamic Strategy Loading
**Goal**: Load strategies from custom folder  
**Implementation**:
```python
def load_available_strategies():
    strategy_dir = Path("src/strategies/custom")
    strategies = []
    
    for file in strategy_dir.glob("*.py"):
        if file.name != "__init__.py":
            strategy = import_strategy(file)
            strategies.append(strategy)
    
    return strategies
```

**Files**:
- `src/strategies/strategy_loader.py` (NEW)

---

### 5.3 Front-End Strategy Selector
**Goal**: User selects strategy from UI  
**UI Component**:
```jsx
<StrategySelector>
  <option value="example_strategy">Example Strategy</option>
  <option value="momentum_strategy">Momentum Strategy</option>
  <option value="mean_reversion">Mean Reversion</option>
</StrategySelector>
```

**Files**:
- `src/ui/components/StrategySelector.tsx` (NEW)

---

### 5.4 Direct Strategy Execution
**Goal**: Trading agent calls strategy directly  
**Flow**:
```python
# In trading_agent.py
selected_strategy = config.get_selected_strategy()
strategy_module = load_strategy(selected_strategy)

# Call strategy
signals = strategy_module.generate_signals(market_data)
```

**Files**:
- `src/agents/trading_agent.py`

---

## Phase 6: Memory System Framework (Week 7-8)

### 6.1 Trade Memory Storage Setup
**Goal**: Create infrastructure for trade logging  
**Implementation**:
- Create `data/` directory
- Set up `trade_memory.json` structure
- Create manager functions

**Files**:
- `src/memory/memory_manager.py` (NEW)
- `data/trade_memory.json` (NEW)

---

### 6.2 Thinking Memory Infrastructure
**Goal**: Set up rotating markdown files  
**Implementation**:
- Create `data/thinking/` directory
- Implement 10-file rotation (max 5 MB)
- File naming: `thoughts_001.md` to `thoughts_010.md`

**Files**:
- `src/memory/thinking_manager.py` (NEW)
- `data/thinking/*.md` (NEW)

---

### 6.3 Memory Integration Points
**Goal**: Add hooks for memory system  
**Implementation**:
- Add callback on position close
- Add memory load at cycle start
- Prepare for agent integration

**Files**:
- `src/agents/trading_agent.py`
- `src/agents/cycle_manager.py` (NEW)

---

## Priority Summary

**Week 1**: Phase 1 (Bug fixes) - CRITICAL  
**Week 2-3**: Phase 2 (WebSocket) - HIGH  
**Week 3-4**: Phase 3 (Trading logic) - HIGH  
**Week 4-5**: Phase 4 (Smart execution) - MEDIUM  
**Week 6-7**: Phase 5 (Strategies) - MEDIUM  
**Week 7-8**: Phase 6 (Memory framework) - MEDIUM  

---

## Testing Checklist

- [ ] No duplicate logs appear
- [ ] SWARM logs show ♾️ emoji
- [ ] WebSocket stays connected
- [ ] Order book updates in real-time
- [ ] Positions close before opening
- [ ] Smart leverage calculates correctly
- [ ] TP/SL adjusts with confidence
- [ ] Trailing stop updates properly
- [ ] Limit orders fill within 60s
- [ ] Strategies load from custom folder
- [ ] Memory files created correctly

---

## Technical Notes

### WebSocket Reconnection
```python
async def maintain_connection():
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                await handle_messages(ws)
        except:
            logger.error("WebSocket disconnected, reconnecting in 5s...")
            await asyncio.sleep(5)
```

### Order Verification
```python
async def verify_position_closed(position_id):
    max_attempts = 10
    for i in range(max_attempts):
        status = await check_position_status(position_id)
        if status == "closed":
            return True
        await asyncio.sleep(0.5)
    return False
```

### Memory File Rotation
```python
def rotate_thinking_files():
    files = sorted(Path("data/thinking").glob("thoughts_*.md"))
    total_size = sum(f.stat().st_size for f in files)
    
    if total_size > 5_000_000:  # 5 MB
        oldest = files[0]
        oldest.unlink()
        logger.info(f"Rotated thinking memory: deleted {oldest}")
```
