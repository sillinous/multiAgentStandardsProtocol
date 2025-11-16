# APQC 3.1.2 - Analyze Market Trends
## Complete Level 4/5 Decomposition

**Process**: 3.1.2 - Analyze Market Trends (Level 3)
**Parent**: 3.1 - Understand markets, customers, capabilities
**Category**: 3.0 - Market and Sell Products and Services

---

## Level 4 Activities (To Implement)

### 3.1.2.1 - Collect Market Data
**Purpose**: Gather comprehensive market data from multiple sources
**Inputs**: Data source configurations, time periods, market segments
**Outputs**: Normalized, validated market dataset

#### Level 5 Atomic Tasks:
- **3.1.2.1.1** - Gather price data (from market APIs, databases)
- **3.1.2.1.2** - Gather volume data (transaction volumes, search volumes)
- **3.1.2.1.3** - Gather sentiment data (social media, news, reviews)
- **3.1.2.1.4** - Normalize data sources (standardize formats, handle missing data)
- **3.1.2.1.5** - Validate data quality (check completeness, accuracy, timeliness)

---

### 3.1.2.2 - Identify Trend Patterns
**Purpose**: Detect and classify different types of market trends
**Inputs**: Normalized market data, time series
**Outputs**: Identified patterns with classifications

#### Level 5 Atomic Tasks:
- **3.1.2.2.1** - Detect seasonal patterns (quarterly, annual cycles)
- **3.1.2.2.2** - Detect cyclical patterns (business cycles, economic cycles)
- **3.1.2.2.3** - Detect irregular movements (shocks, anomalies)
- **3.1.2.2.4** - Identify trend direction (upward, downward, sideways)
- **3.1.2.2.5** - Classify trend strength (weak, moderate, strong)
- **3.1.2.2.6** - Calculate moving averages (SMA, EMA, WMA)

---

### 3.1.2.3 - Analyze Trend Significance
**Purpose**: Determine statistical and business significance of trends
**Inputs**: Identified patterns, historical baselines
**Outputs**: Significance scores, confidence levels

#### Level 5 Atomic Tasks:
- **3.1.2.3.1** - Calculate statistical significance (p-values, confidence intervals)
- **3.1.2.3.2** - Assess trend duration (short-term, medium-term, long-term)
- **3.1.2.3.3** - Evaluate trend momentum (acceleration, deceleration)
- **3.1.2.3.4** - Compare to historical trends (deviation from baseline)
- **3.1.2.3.5** - Determine business impact (revenue implications, market share)

---

### 3.1.2.4 - Forecast Future Trends
**Purpose**: Project trends into the future with confidence intervals
**Inputs**: Historical trends, pattern analysis
**Outputs**: Forecasts with confidence bands

#### Level 5 Atomic Tasks:
- **3.1.2.4.1** - Generate short-term forecast (1-3 months)
- **3.1.2.4.2** - Generate medium-term forecast (3-12 months)
- **3.1.2.4.3** - Generate long-term forecast (12+ months)
- **3.1.2.4.4** - Calculate confidence intervals (upper/lower bounds)
- **3.1.2.4.5** - Identify forecast scenarios (optimistic, baseline, pessimistic)

---

### 3.1.2.5 - Calculate Market Opportunity Scores ✅ COMPLETE
**Purpose**: Score market opportunities based on trend analysis
**Inputs**: Trend data, competitive analysis, market sizing
**Outputs**: Opportunity scores, recommendations

**Status**: ✅ **FULLY IMPLEMENTED**
**File**: `market_opportunity_scoring_agent.py` (536 lines)

#### Level 5 Atomic Tasks (All Implemented):
- ✅ 3.1.2.5.1 - Score market size
- ✅ 3.1.2.5.2 - Score demand level
- ✅ 3.1.2.5.3 - Score competition level
- ✅ 3.1.2.5.4 - Score pricing potential
- ✅ 3.1.2.5.5 - Score customer fit
- ✅ 3.1.2.5.6 - Calculate composite score
- ✅ 3.1.2.5.7 - Generate recommendations

---

## Implementation Priority

### Phase 1: Most Granular (Level 5 Atomic Tasks)
**Start with highest-value atomic tasks:**

1. **3.1.2.2.6** - Calculate moving averages (foundation for many analyses)
2. **3.1.2.2.1** - Detect seasonal patterns (common business need)
3. **3.1.2.2.4** - Identify trend direction (basic classification)
4. **3.1.2.3.1** - Calculate statistical significance (validation)
5. **3.1.2.4.1** - Generate short-term forecast (immediate value)

### Phase 2: Compose into Activities (Level 4)
**After implementing 5-7 atomic tasks, compose them:**

1. **3.1.2.2** - Identify Trend Patterns (uses tasks 3.1.2.2.1-.6)
2. **3.1.2.3** - Analyze Trend Significance (uses tasks 3.1.2.3.1-.5)
3. **3.1.2.4** - Forecast Future Trends (uses tasks 3.1.2.4.1-.5)

### Phase 3: Orchestrate into Process (Level 3)
**Finally, create the orchestrator:**

1. **3.1.2** - Analyze Market Trends (orchestrates activities 3.1.2.1-.5)

---

## Agent Composition Pattern

```python
# Level 5 Atomic Task Agent (Single Responsibility)
class DetectSeasonalPatternsAgent:
    """3.1.2.2.1 - Detect seasonal patterns"""
    async def execute(self, time_series_data):
        # Single focused algorithm
        return seasonal_patterns

# Level 4 Activity Agent (Composes Level 5 Tasks)
class IdentifyTrendPatternsAgent:
    """3.1.2.2 - Identify trend patterns"""
    def __init__(self):
        # Compose atomic task agents
        self.seasonal_detector = DetectSeasonalPatternsAgent()
        self.cyclical_detector = DetectCyclicalPatternsAgent()
        self.direction_classifier = IdentifyTrendDirectionAgent()

    async def execute(self, market_data):
        # Orchestrate atomic tasks
        patterns = {
            "seasonal": await self.seasonal_detector.execute(data),
            "cyclical": await self.cyclical_detector.execute(data),
            "direction": await self.direction_classifier.execute(data)
        }
        return patterns

# Level 3 Process Agent (Orchestrates Level 4 Activities)
class AnalyzeMarketTrendsAgent:
    """3.1.2 - Analyze market trends"""
    def __init__(self):
        # Orchestrate activity agents
        self.pattern_identifier = IdentifyTrendPatternsAgent()
        self.significance_analyzer = AnalyzeTrendSignificanceAgent()
        self.forecaster = ForecastFutureTrendsAgent()
        self.opportunity_scorer = MarketOpportunityScoringAgent()

    async def execute(self, market_input):
        # Multi-step workflow
        patterns = await self.pattern_identifier.execute(data)
        significance = await self.significance_analyzer.execute(patterns)
        forecast = await self.forecaster.execute(patterns)
        scores = await self.opportunity_scorer.execute(forecast)
        return comprehensive_analysis
```

---

## Estimated Effort

### Per Level 5 Atomic Task: 1-2 hours each
- Single algorithm implementation
- Focused unit tests
- Clear input/output schemas
- Simple, reusable

### Per Level 4 Activity: 2-3 hours each
- Compose 4-7 atomic tasks
- Orchestration logic
- Integration tests
- Error handling

### Level 3 Process: 3-4 hours
- Orchestrate 4-5 activities
- End-to-end workflow
- Comprehensive tests
- Documentation

---

## Total Implementation

**For complete 3.1.2 - Analyze Market Trends:**
- **~25 Level 5 atomic tasks** × 1.5 hours = 37.5 hours
- **~5 Level 4 activities** × 2.5 hours = 12.5 hours
- **1 Level 3 process** × 3.5 hours = 3.5 hours
- **Total**: ~53 hours for complete implementation

**But we can start with MVP:**
- **5 key Level 5 tasks** × 1.5 hours = 7.5 hours
- **2 Level 4 activities** × 2.5 hours = 5 hours
- **1 Level 3 process (basic)** × 2 hours = 2 hours
- **MVP Total**: ~14.5 hours

---

## Next Steps

1. **Choose 5 atomic tasks** to implement first
2. **Implement them as single-purpose agents**
3. **Write comprehensive tests**
4. **Compose into 2 activity agents**
5. **Create basic Level 3 orchestrator**
6. **Update APQC_PCF_TRACKING.md** as we go

---

**Last Updated**: 2025-11-16
**Status**: Planning document for bottom-up APQC implementation
