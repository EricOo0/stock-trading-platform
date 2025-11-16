# 快速开始指南 - Feature2 功能修复

## 概述

本指南帮助开发者快速理解并实现 Feature2 市场数据对比功能的修复。修复工作主要集中在解决 TypeScript 编译错误、组件布局问题以及恢复市场数据功能。

## 前置要求

检查以下环境是否符合要求：

### 前端环境
```bash
# 检查 Node.js 版本 (需要 18+)
node --version

# 检查 npm 版本
npm --version

# 检查 TypeScript 编译
npx tsc --version
```

### 后端环境
```bash
# 检查 Python 版本 (需要 3.8+)
python3 --version

# 验证市场数据工具
python3 -c "import skills.market_data_tool; print('成功')"
```

### 开发环境验证
```bash
# 验证前端开发服务器
cd frontend && npm run dev

# 应该显示: VITE v6.4.1 ready in X ms
# 访问: http://localhost:3000
```

## 修复步骤

### 第一步：解决 TypeScript 编译错误 (预计时间: 2-3小时)

**问题描述**: 目前有 150+ TypeScript 编译错误，主要集中在类型定义缺失。

**操作步骤**:

1. **备份当前代码**
```bash
git stash save "修复前备份"
```

2. **修复类型定义文件**
```bash
# 检查类型错误
cd frontend
npm run type-check  # 如果有此脚本，或直接使用 tsc

# 主要修复文件:
# - src/types/market.types.ts (45% 的错误来源)
# - src/services/websocketManager.ts (WebSocket 类型错误)
# - src/components/DashboardLayout/DashboardLayout.tsx (布局组件类型)
```

3. **修复组件 Props 类型**
```typescript
// 示例: 修复 AppNotification 组件
// 文件: src/components/AppNotification/AppNotification.tsx
// 错误: 'id' does not exist in type 'Omit<Notification, "id">'
// 解决方案: 确保 Props 类型正确定义

interface AppNotificationProps {
  notification: Omit<Notification, "id"> & { id?: string };
  onDismiss: (id: string) => void;
}
```

4. **验证修复结果**
```bash
# 重新检查类型错误
npx tsc --noEmit
# 应该显示 0 错误
```

### 第二步：解决导入循环问题 (预计时间: 1小时)

**问题描述**: 存在导入循环导致模块加载失败。

**操作步骤**:

1. **识别导入循环**
```bash
# 使用工具检测循环依赖
npm install --save-dev madge
npx madge --circular frontend/src
```

2. **重构服务模块**
```typescript
// 创建统一的服务接口
// 文件: src/services/types.ts
export interface WebSocketServiceInterface {
  connect: () => void;
  disconnect: () => void;
  subscribe: (symbol: string) => void;
}

// 文件: src/services/index.ts
export * from './websocketManager';
export * from './apiService';
export type { WebSocketServiceInterface } from './types';
```

3. **修复循环引用**
```typescript
// 重构相互引用的模块
// 使用依赖注入而不是直接导入
```

### 第三步：修复组件布局问题 (预计时间: 1-2小时)

**问题描述**: 组件"挤在一起"，缺乏合适的间距和对齐。

**操作步骤**:

1. **分析布局问题**
```bash
# 打开浏览器开发工具，检查:
# - 组件间距 (padding, margin)
# - 响应式断点
# - Grid/Flexbox 使用情况
```

2. **应用 Tailwind CSS 修复**
```typescript
// 修复前 (组件挤在一起):
<div className="grid grid-cols-3 gap-0">
  {/* 组件内容 */}
</div>

// 修复后 (适当间距):
<div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
  {/* 组件内容 */}
</div>
```

3. **添加响应式布局**
```typescript
// 使用 Tailwind 响应式类
<div className="
  container mx-auto
  px-4 sm:px-6 lg:px-8
  grid grid-cols-1
  md:grid-cols-2
  lg:grid-cols-3
  gap-4 md:gap-6 lg:gap-8
">
  {/* 组件内容 */}
</div>
```

### 第四步：恢复 Feature2 功能 (预计时间: 2-3小时)

**问题描述**: Feature2 的市场对比功能未正常工作。

**操作步骤**:

1. **分析现有 Feature2 代码**
```bash
# 搜索 Feature2 相关代码
grep -r "feature2\|Feature2" frontend/src/ --include="*.tsx" --include="*.ts"
grep -r "comparison\|compare" frontend/src/ --include="*.tsx" --include="*.ts"
```

2. **修复市场对比服务**
```typescript
// 文件: src/services/comparisonService.ts
export interface ComparisonData {
  symbols: string[];
  marketData: MarketData[];
  timeRange: TimeRange;
  metrics: ComparisonMetric[];
}

export async function fetchComparisonData(
  symbols: string[],
  timeRange: TimeRange
): Promise<ComparisonData> {
  try {
    const response = await fetch(`/api/comparison`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbols, timeRange }),
    });

    if (!response.ok) {
      throw new Error(`获取对比数据失败: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('对比数据获取失败:', error);
    throw new Error('无法加载市场对比数据');
  }
}
```

3. **实现交互组件**
```typescript
// 文件: src/components/MarketComparison/MarketComparison.tsx
const MarketComparison: React.FC = () => {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = useCallback(async () => {
    if (symbols.length < 2) {
      // 显示错误信息
      return;
    }

    setLoading(true);
    try {
      const data = await fetchComparisonData(symbols, timeRange);
      setComparisonData(data);
    } catch (error) {
      // 处理错误
    } finally {
      setLoading(false);
    }
  }, [symbols, timeRange]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">市场对比</h3>
      {/* 对比界面 */}
    </div>
  );
};
```

## 测试验证

### 单元测试

1. **类型检查测试**
```bash
cd frontend
npx tsc --noEmit
# 必须显示 0 错误
```

2. **组件渲染测试**
```bash
npm run test
# 验证修复的组件正常渲染
```

3. **功能测试**
```bash
# 验证市场对比功能
npm run test:comparison
```

### 集成测试

1. **WebSocket 连接测试**
```bash
# 验证实时数据更新
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:3000" \
  -H "Origin: http://localhost:3000" \
  http://localhost:3000/ws
```

2. **API 集成测试**
```bash
# 测试后端接口
curl -X POST http://localhost:8000/api/comparison \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["000001.SZ", "601398.SH"]}'
```

## 性能优化

### 构建性能

1. **优化构建配置**
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['lightweight-charts'],
          state: ['@reduxjs/toolkit', 'react-redux'],
        },
      },
    },
    target: 'esnext',
    minify: 'terser',
  },
});
```

2. **代码分割**
```typescript
// 实现路由级别的代码分割
const MarketComparison = lazy(() =>
  import('./components/MarketComparison/MarketComparison')
);
```

### 运行时性能

1. **内存优化**
```typescript
// 使用 React.memo 防止不必要的重渲染
const MemoizedMarketData = memo(MarketDataComponent);

// 使用 useMemo 缓存计算结果
const calculatedMetrics = useMemo(() => {
  return calculateMetrics(marketData);
}, [marketData]);
```

2. **网络请求优化**
```typescript
// 实现请求去重和缓存
const cachedComparisonData = useRef<Map<string, ComparisonData>>(new Map());
```

## 部署检查清单

### 构建前检查

- [ ] TypeScript 编译错误数量: 0
- [ ] 所有测试通过
- [ ] 组件布局显示正常
- [ ] 响应式设计在不同屏幕尺寸下工作
- [ ] WebSocket 连接正常
- [ ] 市场对比功能完整

### 生产环境检查

- [ ] 使用生产构建 (`npm run build`)
- [ ] 性能指标符合要求
- [ ] 错误处理机制生效
- [ ] 安全性检查通过
- [ ] 实时监控配置完成

## 故障排除

### 常见问题

1. **类型错误持续存在**
   - 清除 TypeScript 缓存: `npx tsc --clearCache`
   - 检查 tsconfig.json 配置是否冲突

2. **组件样式不生效**
   - 检查 Tailwind CSS 配置
   - 确认类名拼写正确
   - 验证 CSS 导入顺序

3. **WebSocket 连接失败**
   - 检查网络代理设置
   - 验证 WebSocket 服务器地址
   - 确认防火墙配置

4. **市场对比功能失败**
   - 检查后端 API 响应
   - 验证请求数据格式
   - 确认符号代码正确性

## 成功标准

根据 [功能规约](spec.md) 中的要求:

1. **编译成功率**: 100% - 零 TypeScript 错误
2. **导入依赖**: 全部正常 - 无 "模块未找到" 错误
3. **组件布局**: 标准屏幕 (1024x768+) 上元素无重叠
4. **Feature2 成功率**: 95% - 市场对比功能预期操作
5. **启动时间**: <30 秒 - 应用启动时间
6. **代码组织**: 90% - 遵循既定项目规范

## 下一步

完成此快速开始指南后，您可以:

1. 继续详细的功能实现
2. 查看[数据模型](data-model.md)了解数据结构详情
3. 查看[API 合同](contracts/)了解接口规格
4. 使用 `speckit.tasks` 命令生成详细任务清单

---

*本指南遵循 AI投资项目Agent宪法 原则，确保代码质量、安全性和用户体验。*