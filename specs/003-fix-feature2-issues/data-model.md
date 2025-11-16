# Data Model: Feature2 Market Data Dashboard

**Date**: 2025-11-15
**Feature**: `003-fix-feature2-issues`

## Core Entities

### Market Data Entity
**Purpose**: Represents individual market data points for stocks across different markets

```typescript
interface MarketData {
  symbol: string;              // Stock symbol (e.g., "AAPL", "000001.SZ", "0700.HK")
  name: string;                // Company name (中文优先 - Chinese primary)
  market: MarketType;          // Market classification
  price: number;               // Current price
  change: number;              // Price change
  changePercent: number;       // Percentage change
  volume: number;              // Trading volume
  marketCap?: number;          // Market capitalization
  lastUpdated: Date;           // Timestamp of last update
  currency: string;            // Price currency
  dataSource: DataSource;      // Source of data
}

enum MarketType {
  ASHARE = "ASHARE",    // A股
  US = "US",           // 美股
  HK = "HK"            // 港股
}

enum DataSource {
  SINA = "SINA",       // 新浪财经
  YAHOO = "YAHOO",     // Yahoo Finance
  MANUAL = "MANUAL"    // Manual input
}
```

### Market Comparison Entity
**Purpose**: Enables Feature2 functionality for comparing multiple stocks/markets

```typescript
interface MarketComparison {
  id: string;                  // Unique comparison identifier
  userId?: string;             // User identification (for personalization)
  name: string;                // Comparison name (中文优先)
  description?: string;        // Description of comparison
  symbols: string[];           // Array of stock symbols being compared
  timeRange: TimeRange;        // Historical data range
  metrics: ComparisonMetric[]; // Metrics to compare
  createdAt: Date;             // Creation timestamp
  updatedAt: Date;             // Last update timestamp
  isActive: boolean;           // Active comparison flag
}

interface TimeRange {
  start: Date;                 // Start date for historical data
  end: Date;                   // End date for historical data
  interval: TimeInterval;      // Data granularity
}

enum TimeInterval {
  ONE_MIN = "1m",
  FIVE_MIN = "5m",
  ONE_HOUR = "1h",
  ONE_DAY = "1d",
  ONE_WEEK = "1w",
  ONE_MONTH = "1m"
}

interface ComparisonMetric {
  type: MetricType;
  value?: number;
  displayName: string;         // Localized display name
}

enum MetricType {
  PRICE_CHANGE = "PRICE_CHANGE",
  VOLUME_CHANGE = "VOLUME_CHANGE",
  MARKET_CAP = "MARKET_CAP",
  VOLATILITY = "VOLATILITY",
  P_E_RATIO = "P_E_RATIO",
  DIVIDEND_YIELD = "DIVIDEND_YIELD"
}
```

### WebSocket Message Entity
**Purpose**: Real-time data updates from backend to frontend

```typescript
interface WebSocketMessage {
  type: MessageType;
  payload: MessagePayload;
  timestamp: Date;
  market: MarketType;
  symbol?: string;
}

enum MessageType {
  PRICE_UPDATE = "PRICE_UPDATE",
  VOLUME_UPDATE = "VOLUME_UPDATE",
  MARKET_OPEN = "MARKET_OPEN",
  MARKET_CLOSE = "MARKET_CLOSE",
  ERROR = "ERROR",
  HEARTBEAT = "HEARTBEAT"
}

type MessagePayload =
  | PriceUpdatePayload
  | VolumeUpdatePayload
  | MarketStatusPayload
  | ErrorPayload;

interface PriceUpdatePayload {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

interface VolumeUpdatePayload {
  symbol: string;
  volume: number;
  volumeChange: number;
}

interface MarketStatusPayload {
  market: MarketType;
  isOpen: boolean;
  nextOpenTime?: Date;
  nextCloseTime?: Date;
}

interface ErrorPayload {
  code: string;
  message: string;               // User-friendly error message (中文)
  details?: Record<string, any>;
}
```

### Error and Notification Entity
**Purpose**: Application error handling with Chinese language support

```typescript
interface AppError {
  id: string;
  code: ErrorCode;
  message: string;               // Chinese error message
  details: Record<string, any>;
  severity: ErrorSeverity;
  timestamp: Date;
  symbol?: string;               // Related stock symbol
  market?: MarketType;           // Related market
}

enum ErrorCode {
  // 数据相关错误
  MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE",
  INVALID_SYMBOL = "INVALID_SYMBOL",
  RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED",
  NETWORK_ERROR = "NETWORK_ERROR",
  PARSE_ERROR = "PARSE_ERROR",

  // 系统错误
  INTERNAL_ERROR = "INTERNAL_ERROR",
  CONFIGURATION_ERROR = "CONFIGURATION_ERROR",

  // 用户操作错误
  INVALID_COMPARISON = "INVALID_COMPARISON",
  COMPARISON_LIMIT_EXCEEDED = "COMPARISON_LIMIT_EXCEEDED"
}

enum ErrorSeverity {
  LOW = "LOW",           // 不影响使用
  MEDIUM = "MEDIUM",     // 部分功能受限
  HIGH = "HIGH",         // 主要功能受损
  CRITICAL = "CRITICAL"  // 系统不可用
}

interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;                 // Chinese title
  message: string;               // Chinese message
  icon?: string;
  isRead: boolean;
  timestamp: Date;
  action?: NotificationAction;
}

enum NotificationType {
  MARKET_OPEN = "MARKET_OPEN",
  MARKET_CLOSE = "MARKET_CLOSE",
  PRICE_ALERT = "PRICE_ALERT",
  COMPARISON_COMPLETE = "COMPARISON_COMPLETE",
  ERROR_NOTIFICATION = "ERROR_NOTIFICATION"
}

interface NotificationAction {
  text: string;                  // Button text (中文)
  action: string;                // Action identifier
  payload?: Record<string, any>;
}
```

## State Management Entities

### Redux State Structure

```typescript
interface RootState {
  market: MarketState;
  comparison: ComparisonState;
  ui: UIState;
  user: UserState;
}

interface MarketState {
  data: Record<string, MarketData>;        // symbol -> MarketData
  loading: boolean;
  error: AppError | null;
  activeMarkets: MarketType[];
  lastUpdate: Date | null;
}

interface ComparisonState {
  comparisons: MarketComparison[];
  activeComparisonId: string | null;
  historicalData: Record<string, MarketData[]>; // symbol -> historical data
  isLoading: boolean;
  error: AppError | null;
}

interface UIState {
  layout: LayoutConfiguration;
  notifications: AppNotification[];
  theme: ThemeConfiguration;
  isWebSocketConnected: boolean;
  sidebarCollapsed: boolean;
}

interface UserState {
  preferences: UserPreferences;
  recentComparisons: string[];            // comparison IDs
  favoriteStocks: string[];               // stock symbols
  settings: UserSettings;
}
```

## Data Validation Rules

### Market Data Validation

```typescript
const marketDataValidation = {
  symbol: {
    required: true,
    pattern: /^[A-Z0-9]+\.[A-Z]{2}$|^[A-Z0-9]{1,10}$/, // Stock symbol format
    maxLength: 20
  },
  market: {
    required: true,
    enum: Object.values(MarketType)
  },
  price: {
    required: true,
    min: 0,
    max: 100000 // Reasonable stock price limit
  },
  change: {
    min: -1000, // Allow for large price movements
    max: 1000
  },
  changePercent: {
    min: -99.99,
    max: 999.99
  },
  volume: {
    required: true,
    min: 0,
    max: 1000000000000 // Maximum volume limit
  }
};
```

### Comparison Validation

```typescript
const comparisonValidation = {
  symbols: {
    required: true,
    minLength: 2,          // Minimum 2 stocks for comparison
    maxLength: 10,         // Maximum 10 stocks per comparison
    unique: true          // No duplicate symbols
  },
  timeRange: {
    required: true,
    validate: (range: TimeRange) => {
      return range.start < range.end &&
             range.end <= new Date() && // Cannot be in the future
             range.end.getTime() - range.start.getTime() <= 365 * 24 * 60 * 60 * 1000; // Max 1 year
    }
  },
  name: {
    required: true,
    maxLength: 100,
    minLength: 1
  }
};
```

## API Response Formats

### Market Data API Response

```json
{
  "symbol": "000001.SZ",
  "name": "平安银行",
  "market": "ASHARE",
  "price": 12.34,
  "change": 0.56,
  "changePercent": 4.75,
  "volume": 1234567,
  "marketCap": 1234567890,
  "lastUpdated": "2025-11-15T12:34:56Z",
  "currency": "CNY",
  "dataSource": "SINA"
}
```

### Comparison API Response

```json
{
  "id": "cmp-123456",
  "name": "银行股对比",
  "description": "主要银行股表现对比分析",
  "symbols": ["000001.SZ", "601398.SH", "601988.SH"],
  "timeRange": {
    "start": "2025-10-01T00:00:00Z",
    "end": "2025-11-15T23:59:59Z",
    "interval": "1d"
  },
  "metrics": [
    {
      "type": "PRICE_CHANGE",
      "value": 5.67,
      "displayName": "价格变化"
    }
  ],
  "createdAt": "2025-11-15T12:00:00Z",
  "updatedAt": "2025-11-15T12:30:00Z",
  "isActive": true
}
```

## Error Response Format

```json
{
  "error": {
    "code": "MARKET_DATA_UNAVAILABLE",
    "message": "市场数据暂时不可用，请稍后再试",
    "severity": "HIGH",
    "timestamp": "2025-11-15T12:34:56Z",
    "symbol": "000001.SZ",
    "market": "ASHARE"
  }
}
```

## Data Relationships

1. **MarketComparison** contains multiple **MarketData** entries (one-to-many)
2. **MarketData** belongs to one **MarketType** (many-to-one)
3. **WebSocketMessage** references **MarketData** for real-time updates (one-to-one)
4. **AppError** optionally references **MarketData** for context-specific errors (many-to-one)
5. **AppNotification** related to **MarketComparison** events (one-to-many)

## Security Requirements

### Data Protection

1. **Market-sensitive data** must be encrypted in transit and at rest
2. **User comparison data** implements end-to-end encryption
3. **API keys** for data sources must be securely managed
4. **Rate limiting** prevents API abuse (A-share: 120/hr, US/HK: 60/hr)

### Compliance Requirements

1. **Financial data regulations** compliance for multi-market data
2. **User privacy** protection under GDPR and Chinese data protection laws
3. **Audit logging** for all data access and comparison operations
4. **Error masking** to prevent sensitive information leakage

## Performance Guidelines

### Data Fetching

- **Batch requests** for multiple symbols to reduce API calls
- **Caching strategy** with LRU eviction for frequently accessed data
- **Pagination** for historical data retrieval
- **Compression** for large datasets

### State Management

- **Redux normalization** for efficient state updates
- **Memoization** for expensive calculations
- **Selective rendering** to prevent unnecessary re-renders
- **Lazy loading** for non-critical components