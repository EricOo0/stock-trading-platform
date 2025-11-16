# Frontend Architecture: Market Data Dashboard

**Technical Design Document for Frontend Implementation**

## Overview

This document outlines the technical architecture for the market data dashboard frontend application. The system implements a responsive, bilingual web interface with real-time market data visualization, technical analysis tools, and fundamental data display.

## Tech Stack Selection

### Recommended Framework: React 18+ with TypeScript
```json
{
  "framework": "React 18.3.0",
  "language": "TypeScript 5.2+",
  "state_management": "Redux Toolkit + RTK Query",
  "routing": "React Router v6",
  "styling": "Tailwind CSS 3.4+",
  "ui_components": "Headless UI + Custom",
  "charts": "Lightweight Charts by TradingView",
  "icons": "Lucide React",
  "i18n": "react-i18next",
  "axios": "axios 1.6+"
}
```

### Alternative: Vue 3 + Composition API
```json
{
  "framework": "Vue 3.4+",
  "language": "TypeScript 5.2+",
  "state_management": "Pinia",
  "routing": "Vue Router v4",
  "styling": "Tailwind CSS 3.4+",
  "ui_components": "Headless UI Vue",
  "charts": "vue-chartjs",
  "icons": "Lucide Vue",
  "i18n": "vue-i18n"
}
```

## Component Architecture

### Layout Structure
```
App
├── LayoutContainer
│   ├── CollapsibleSidebar
│   │   ├── SidebarHeader (logo, collapse button)
│   │   ├── NavigationMenu
│   │   │   ├── MarketDataNavItem (primary feature)
│   │   │   └── [Future navigation items]
│   │   └── SidebarFooter (language toggle)
│   └── ContentArea
│       ├── HeaderBar (title, search, controls)
│       └── DashboardContent
│           ├── MarketOverview (indices widget)
│           ├── StockSearchPanel
│           ├── ChartSection
│           │   ├── ChartControls (timeframe, indicators)
│           │   ├── MainChart (candlestick + indicators)
│           │   ├── VolumeChart
│           │   └── ChartToolbar
│           ├── TechnicalIndicators
│           └── FundamentalDataPanel
│               ├── KeyMetrics
│               ├── FinancialStatements
│               └── CompanyInfo
```

### Key Components Design

#### MarketDataProvider (Context/Hook)
```typescript
interface MarketDataContext {
  currentStock: StockData | null;
  marketIndices: MarketIndex[];
  watchlist: WatchlistItem[];
  searchResults: SearchResult[];
  isLoading: boolean;
  error: string | null;
  search(query: string): Promise<void>;
  selectStock(symbol: string): Promise<void>;
  addToWatchlist(symbol: string): void;
  removeFromWatchlist(symbol: string): void;
  refreshData(): Promise<void>;
}
```

#### Chart Component Integration
```typescript
interface ChartProps {
  symbol: string;
  timeframe: Timeframe;
  indicators: TechnicalIndicator[];
  onIndicatorToggle: (indicator: string) => void;
  onTimeframeChange: (timeframe: Timeframe) => void;
}
```

## Data Flow Architecture

### State Management Pattern
1. **Global State (Redux/Pinia)**:
   - User preferences (language, theme, watchlist)
   - Application state (sidebar collapsed, selected stock)
   - Market data cache (with TTL)

2. **Component State**:
   - UI interactions (search input, chart selections)
   - Loading states (api calls, chart rendering)
   - Form data (filters, settings)

3. **Server State (RTK Query/SWR)**:
   - Real-time market data (with intelligent caching)
   - Historical chart data (cached aggressively)
   - Search results (cached briefly)

### API Integration Pattern
```typescript
// API Service Layer
class MarketDataService {
  // Use existing skill API from task 1
  static async getRealtimeData(symbols: string[]): Promise<MarketData[]> {
    return callSkill('market_data_tool.get_realtime_data', { symbols });
  }

  static async getHistoricalData(symbol: string, period: Timeframe): Promise<HistoricalData> {
    return callSkill('market_data_tool.get_historical_data', { symbol, period });
  }

  static async searchStocks(query: string): Promise<SearchResult[]> {
    return callSkill('market_data_tool.search_stocks', { query });
  }
}
```

## Responsive Design Strategy

### Breakpoint Strategy
```css
/* Mobile First Approach */
@layer utilities {
  /* Sidebar collapses automatically on mobile */
  .sidebar {
    @apply fixed lg:relative transform -translate-x-full lg:translate-x-0;
    transition: transform 0.3s ease;
  }

  .sidebar-open {
    @apply translate-x-0;
  }

  /* Chart responsive scaling */
  .chart-container {
    @apply min-h-[400px] md:min-h-[500px] lg:min-h-[600px];
  }
}
```

### Mobile Adaptations
- Touch-friendly interactions (swipe gestures)
- Optimized chart readability on smaller screens
- Simplified technical indicators display
- Context-aware data loading

## Chart Implementation Strategy

### Primary Chart Library: Lightweight Charts
```typescript
import { createChart } from 'lightweight-charts';

class CandlestickChart {
  private chart: IChartApi;
  private candlestickSeries: ISeriesApi<'Candlestick'>;
  private volumeSeries: ISeriesApi<'Histogram'>;

  constructor(container: HTMLElement) {
    this.chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        backgroundColor: 'rgba(0, 0, 0, 0)',
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: {
          color: 'rgba(197, 203, 206, 0.5)',
        },
        horzLines: {
          color: 'rgba(197, 203, 206, 0.5)',
        },
      },
    });
  }
}
```

### Technical Indicators Overlay
```typescript
interface TechnicalIndicator {
  id: string;
  name: string;
  data: number[];
  color: string;
  type: 'line' | 'histogram' | 'area';
}

class IndicatorOverlay {
  addMA(period: number, data: OHLCData[]): LineSeries {
    const maData = this.calculateMA(period, data);
    return this.chart.addLineSeries({
      color: this.getColorForPeriod(period),
      lineWidth: 2,
    });
  }

  addRSI(data: OHLCData[]): void {
    const rsiData = this.calculateRSI(data);
    // Create separate RSI panel
  }

  addMACD(data: OHLCData[]): void {
    const macdData = this.calculateMACD(data);
    // Create MACD histogram and signal line
  }
}
```

## Bilingual Support Implementation

### Language Structure
```typescript
// i18n configuration
const resources = {
  zh: {
    navigation: {
      marketData: '行情数据',
      search: '搜索',
      addToWatchlist: '添加到自选',
      technicalIndicators: '技术指标'
    },
    charts: {
      candlestick: 'K线图',
      volume: '成交量',
      timeframe: {
        '1D': '日K',
        '1W': '周K',
        '1M': '月K',
        '1Y': '年K'
      }
    }
  },
  en: {
    navigation: {
      marketData: 'Market Data',
      search: 'Search',
      addToWatchlist: 'Add to Watchlist',
      technicalIndicators: 'Technical Indicators'
    },
    charts: {
      candlestick: 'Candlestick Chart',
      volume: 'Volume',
      timeframe: {
        '1D': 'Daily',
        '1W': 'Weekly',
        '1M': 'Monthly',
        '1Y': 'Yearly'
      }
    }
  }
};
```

### Market-Specific Localization
```typescript
const marketLocalization = {
  formatters: {
    currency: (value: number, currency: string, locale: string) => {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    },
    date: (date: Date, locale: string) => {
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }).format(date);
    }
  }
};
```

## Performance Optimization Strategy

### Caching Strategy
```typescript
interface CacheConfig {
  realtime_data: 30_000; // 30 seconds
  historical_data: 300_000; // 5 minutes
  search_results: 60_000; // 1 minute
  fundamental_data: 3_600_000; // 1 hour
}
```

### Bundle Optimization
```typescript
// Code splitting example
const ChartComponent = lazy(() => import('./components/ChartComponent'));
const TechnicalAnalysis = lazy(() => import('./components/TechnicalAnalysis'));
```

### Data Virtualization
```typescript
// For large datasets
interface VirtualizationConfig {
  viewportItemCount: 100;
  overscan: 20;
  itemHeight: 50;
  bufferTime: 16; // ~60fps
}
```

## Security Considerations

### API Security
```typescript
const securityConfig = {
  rateLimiting: 'client-side throttling with exponential backoff',
  inputValidation: 'strict validation for all user inputs and API parameters',
  errorHandling: 'generic error messages for security, detailed for UX',
  dataSanitization: 'sanitize all data from external APIs before display'
};
```

### Content Security Policy
```typescript
const cspConfig = {
  directives: {
    'script-src': ["'self'", 'trusted-cdn.com'],
    'connect-src': ["'self'", 'market-data-api.example.com'],
    'img-src': ["'self'", 'data:', 'trusted-image-cdn.com']
  }
};
```

## Testing Strategy

### Test Coverage Requirements
```typescript
const testingStrategy = {
  unitTests: '80% coverage for business logic',
  integrationTests: 'API integration and data flow validation',
  e2eTests: 'Critical user flows: search, chart display, watchlist',
  performanceTests: 'Chart rendering under 2 seconds for 1-year data'
};
```

### Key Test Scenarios
```typescript
// Example test cases
describe('Market Data Dashboard', () => {
  it('should load market data within 2 seconds', () => {
    // Performance test
  });

  it('should handle API errors gracefully', () => {
    // Error boundary testing
  });

  it('should switch between timeframes smoothly', () => {
    // UX testing
  });
});
```

## Deployment Considerations

### Build Configuration
```typescript
const buildConfig = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: -10
        }
      }
    }
  },
  lazyLoading: 'for chart components and indicator overlays'
};
```

### Environment Configuration
```typescript
interface EnvironmentConfig {
  development: {
    apiUrl: 'http://localhost:8000',
    debugMode: true,
    loggerLevel: 'debug'
  };
  production: {
    apiUrl: 'https://api.market-data.com',
    debugMode: false,
    loggerLevel: 'error'
  };
}
```

This architecture provides a robust foundation for implementing a professional-grade market data dashboard with excellent performance, maintainability, and user experience.