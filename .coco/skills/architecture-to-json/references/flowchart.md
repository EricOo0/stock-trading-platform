# Flowchart Extraction Guidelines

## Flowchart JSON Structure

```json
{
  "canvas": {
    "width": 1080,
    "height": 1920,
    "background": {
      "type": "gradient",
      "colors": ["#0A0E27", "#1A1F3A", "#0F1419"],
      "direction": "vertical"
    }
  },
  "title": {
    "text": "Deep Wiki 工作原理",
    "position": { "x": 540, "y": 120 },
    "style": {
      "fontSize": 72,
      "fontWeight": "bold",
      "color": "#FFFFFF",
      "textAlign": "center"
    }
  },
  "subtitle": {
    "text": "多层次知识探索系统",
    "position": { "x": 540, "y": 200 },
    "style": {
      "fontSize": 32,
      "color": "#A0AEC0",
      "textAlign": "center"
    }
  },
  "sections": [
    {
      "id": "input",
      "title": "1. 用户输入",
      "position": { "x": 540, "y": 320 },
      "icon": "search",
      "iconColor": "#4299E1",
      "content": {
        "text": "提出研究问题或主题",
        "examples": ["\"AI Agent 的架构设计\"", "\"量子计算的应用\""]
      },
      "style": {
        "backgroundColor": "#1A202C",
        "borderColor": "#4299E1",
        "borderWidth": 2,
        "borderRadius": 16,
        "padding": 24,
        "width": 900
      }
    },
    {
      "id": "arrow1",
      "type": "arrow",
      "from": { "x": 540, "y": 450 },
      "to": { "x": 540, "y": 520 },
      "style": {
        "color": "#4299E1",
        "width": 3,
        "animated": true
      }
    },
    {
      "id": "search",
      "title": "2. 智能搜索",
      "position": { "x": 540, "y": 600 },
      "icon": "globe",
      "iconColor": "#48BB78",
      "content": {
        "text": "多源检索 + 语义理解",
        "features": [
          "Web Search",
          "Academic Papers",
          "Documentation",
          "Community Discussions"
        ]
      },
      "style": {
        "backgroundColor": "#1A202C",
        "borderColor": "#48BB78",
        "borderWidth": 2,
        "borderRadius": 16,
        "padding": 24,
        "width": 900
      }
    },
    {
      "id": "arrow2",
      "type": "arrow",
      "from": { "x": 540, "y": 780 },
      "to": { "x": 540, "y": 850 },
      "style": {
        "color": "#48BB78",
        "width": 3,
        "animated": true
      }
    },
    {
      "id": "analysis",
      "title": "3. 深度分析",
      "position": { "x": 540, "y": 930 },
      "icon": "brain",
      "iconColor": "#9F7AEA",
      "content": {
        "text": "多角度解构知识",
        "layers": [
          {
            "name": "基础层",
            "description": "概念定义、历史背景"
          },
          {
            "name": "技术层",
            "description": "实现原理、架构设计"
          },
          {
            "name": "应用层",
            "description": "实际案例、最佳实践"
          }
        ]
      },
      "style": {
        "backgroundColor": "#1A202C",
        "borderColor": "#9F7AEA",
        "borderWidth": 2,
        "borderRadius": 16,
        "padding": 24,
        "width": 900
      }
    },
    {
      "id": "arrow3",
      "type": "arrow",
      "from": { "x": 540, "y": 1160 },
      "to": { "x": 540, "y": 1230 },
      "style": {
        "color": "#9F7AEA",
        "width": 3,
        "animated": true
      }
    },
    {
      "id": "synthesis",
      "title": "4. 知识合成",
      "position": { "x": 540, "y": 1310 },
      "icon": "network",
      "iconColor": "#F6AD55",
      "content": {
        "text": "构建知识图谱",
        "processes": [
          "信息去重与验证",
          "逻辑关系梳理",
          "观点对比分析",
          "引用溯源"
        ]
      },
      "style": {
        "backgroundColor": "#1A202C",
        "borderColor": "#F6AD55",
        "borderWidth": 2,
        "borderRadius": 16,
        "padding": 24,
        "width": 900
      }
    },
    {
      "id": "arrow4",
      "type": "arrow",
      "from": { "x": 540, "y": 1510 },
      "to": { "x": 540, "y": 1580 },
      "style": {
        "color": "#F6AD55",
        "width": 3,
        "animated": true
      }
    },
    {
      "id": "output",
      "title": "5. 输出报告",
      "position": { "x": 540, "y": 1660 },
      "icon": "document",
      "iconColor": "#FC8181",
      "content": {
        "text": "结构化知识文档",
        "formats": [
          "Executive Summary",
          "详细技术文档",
          "可视化图表",
          "参考文献列表"
        ]
      },
      "style": {
        "backgroundColor": "#1A202C",
        "borderColor": "#FC8181",
        "borderWidth": 2,
        "borderRadius": 16,
        "padding": 24,
        "width": 900
      }
    }
  ],
  "footer": {
    "text": "Powered by AI Multi-Agent System",
    "position": { "x": 540, "y": 1860 },
    "style": {
      "fontSize": 24,
      "color": "#718096",
      "textAlign": "center"
    }
  },
  "decorations": [
    {
      "type": "particles",
      "count": 50,
      "colors": ["#4299E1", "#48BB78", "#9F7AEA", "#F6AD55"],
      "opacity": 0.3,
      "animation": "float"
    },
    {
      "type": "grid",
      "style": "dots",
      "color": "#2D3748",
      "opacity": 0.2
    }
  ]
}
```
