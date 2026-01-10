# Sequence Diagram Extraction Guidelines

## Sequence Diagram JSON Structure

```json
{
  "canvas": {
    "width": 1080,
    "height": 1920,
    "background": {
      "type": "gradient",
      "colors": ["#0F172A", "#1E293B", "#0F172A"],
      "direction": "vertical"
    }
  },
  "header": {
    "title": {
      "text": "SSE 工作原理",
      "position": { "x": 540, "y": 80 },
      "style": {
        "fontSize": 68,
        "fontWeight": "bold",
        "color": "#FFFFFF",
        "textAlign": "center"
      }
    },
    "subtitle": {
      "text": "Server-Sent Events 数据流交互",
      "position": { "x": 540, "y": 150 },
      "style": {
        "fontSize": 28,
        "color": "#94A3B8",
        "textAlign": "center"
      }
    }
  },
  "swimlanes": [
    {
      "id": "client",
      "title": "客户端 (Browser)",
      "position": { "x": 140, "y": 220 },
      "width": 380,
      "color": "#3B82F6",
      "icon": "monitor"
    },
    {
      "id": "network",
      "title": "网络层",
      "position": { "x": 540, "y": 220 },
      "width": 380,
      "color": "#8B5CF6",
      "icon": "network"
    },
    {
      "id": "server",
      "title": "服务端 (Server)",
      "position": { "x": 940, "y": 220 },
      "width": 380,
      "color": "#10B981",
      "icon": "server"
    }
  ],
  "timeline": {
    "startY": 300,
    "stepHeight": 180,
    "steps": [
      {
        "id": "step1",
        "time": "T0",
        "yOffset": 0,
        "actions": [
          {
            "swimlane": "client",
            "type": "process",
            "title": "创建 EventSource",
            "code": "const es = new EventSource('/stream')",
            "position": { "x": 140, "y": 300 },
            "style": {
              "backgroundColor": "#1E3A8A",
              "borderColor": "#3B82F6",
              "width": 340,
              "height": 120,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "arrow",
            "direction": "right",
            "label": "HTTP GET Request",
            "from": { "x": 330, "y": 360 },
            "to": { "x": 750, "y": 360 },
            "style": {
              "color": "#8B5CF6",
              "strokeWidth": 3,
              "dashed": false
            }
          }
        ]
      },
      {
        "id": "step2",
        "time": "T1",
        "yOffset": 180,
        "actions": [
          {
            "swimlane": "server",
            "type": "process",
            "title": "建立连接",
            "details": [
              "Content-Type: text/event-stream",
              "Cache-Control: no-cache",
              "Connection: keep-alive"
            ],
            "position": { "x": 940, "y": 480 },
            "style": {
              "backgroundColor": "#065F46",
              "borderColor": "#10B981",
              "width": 340,
              "height": 140,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "arrow",
            "direction": "left",
            "label": "HTTP 200 + Headers",
            "from": { "x": 750, "y": 550 },
            "to": { "x": 330, "y": 550 },
            "style": {
              "color": "#8B5CF6",
              "strokeWidth": 3,
              "dashed": false
            }
          }
        ]
      },
      {
        "id": "step3",
        "time": "T2",
        "yOffset": 360,
        "actions": [
          {
            "swimlane": "client",
            "type": "process",
            "title": "监听事件",
            "code": "es.onmessage = (e) => {\n  console.log(e.data)\n}",
            "position": { "x": 140, "y": 660 },
            "style": {
              "backgroundColor": "#1E3A8A",
              "borderColor": "#3B82F6",
              "width": 340,
              "height": 120,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "connection",
            "label": "持久连接",
            "from": { "x": 330, "y": 720 },
            "to": { "x": 750, "y": 720 },
            "style": {
              "color": "#8B5CF6",
              "strokeWidth": 4,
              "pattern": "solid",
              "opacity": 0.8
            }
          }
        ]
      },
      {
        "id": "step4",
        "time": "T3",
        "yOffset": 540,
        "actions": [
          {
            "swimlane": "server",
            "type": "process",
            "title": "推送数据",
            "format": "data: {\"msg\": \"Hello\"}\n\n",
            "position": { "x": 940, "y": 840 },
            "style": {
              "backgroundColor": "#065F46",
              "borderColor": "#10B981",
              "width": 340,
              "height": 120,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "arrow",
            "direction": "left",
            "label": "Stream Data Chunk",
            "from": { "x": 750, "y": 900 },
            "to": { "x": 330, "y": 900 },
            "style": {
              "color": "#10B981",
              "strokeWidth": 3,
              "dashed": false,
              "animated": true
            }
          }
        ]
      },
      {
        "id": "step5",
        "time": "T4",
        "yOffset": 720,
        "actions": [
          {
            "swimlane": "client",
            "type": "process",
            "title": "接收并处理",
            "action": "触发 onmessage 回调",
            "position": { "x": 140, "y": 1020 },
            "style": {
              "backgroundColor": "#1E3A8A",
              "borderColor": "#3B82F6",
              "width": 340,
              "height": 100,
              "borderRadius": 12
            }
          }
        ]
      },
      {
        "id": "step6",
        "time": "T5",
        "yOffset": 900,
        "actions": [
          {
            "swimlane": "server",
            "type": "process",
            "title": "继续推送",
            "details": [
              "data: {\"msg\": \"Update 1\"}\n\n",
              "data: {\"msg\": \"Update 2\"}\n\n",
              "..."
            ],
            "position": { "x": 940, "y": 1200 },
            "style": {
              "backgroundColor": "#065F46",
              "borderColor": "#10B981",
              "width": 340,
              "height": 140,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "arrow",
            "direction": "left",
            "label": "Continuous Stream",
            "from": { "x": 750, "y": 1270 },
            "to": { "x": 330, "y": 1270 },
            "style": {
              "color": "#10B981",
              "strokeWidth": 3,
              "dashed": true,
              "animated": true
            }
          }
        ]
      },
      {
        "id": "step7",
        "time": "T6",
        "yOffset": 1080,
        "actions": [
          {
            "swimlane": "client",
            "type": "decision",
            "title": "连接状态",
            "options": [
              {
                "condition": "正常",
                "action": "继续接收"
              },
              {
                "condition": "断开",
                "action": "自动重连"
              }
            ],
            "position": { "x": 140, "y": 1380 },
            "style": {
              "backgroundColor": "#1E3A8A",
              "borderColor": "#3B82F6",
              "width": 340,
              "height": 140,
              "borderRadius": 12
            }
          }
        ]
      },
      {
        "id": "step8",
        "time": "T7",
        "yOffset": 1260,
        "actions": [
          {
            "swimlane": "client",
            "type": "process",
            "title": "关闭连接",
            "code": "es.close()",
            "position": { "x": 140, "y": 1560 },
            "style": {
              "backgroundColor": "#1E3A8A",
              "borderColor": "#3B82F6",
              "width": 340,
              "height": 100,
              "borderRadius": 12
            }
          },
          {
            "swimlane": "network",
            "type": "arrow",
            "direction": "right",
            "label": "Close Connection",
            "from": { "x": 330, "y": 1610 },
            "to": { "x": 750, "y": 1610 },
            "style": {
              "color": "#EF4444",
              "strokeWidth": 3,
              "dashed": false
            }
          },
          {
            "swimlane": "server",
            "type": "process",
            "title": "释放资源",
            "action": "清理连接",
            "position": { "x": 940, "y": 1560 },
            "style": {
              "backgroundColor": "#065F46",
              "borderColor": "#10B981",
              "width": 340,
              "height": 100,
              "borderRadius": 12
            }
          }
        ]
      }
    ]
  },
  "keyFeatures": {
    "position": { "x": 540, "y": 1720 },
    "title": "SSE 核心特性",
    "features": [
      {
        "icon": "arrow-right",
        "text": "单向推送",
        "color": "#3B82F6"
      },
      {
        "icon": "refresh",
        "text": "自动重连",
        "color": "#10B981"
      },
      {
        "icon": "zap",
        "text": "文本数据",
        "color": "#8B5CF6"
      },
      {
        "icon": "check",
        "text": "简单易用",
        "color": "#F59E0B"
      }
    ],
    "style": {
      "backgroundColor": "#1E293B",
      "borderRadius": 16,
      "padding": 20,
      "width": 1000
    }
  },
  "footer": {
    "text": "SSE vs WebSocket: 适用于服务端主动推送场景",
    "position": { "x": 540, "y": 1860 },
    "style": {
      "fontSize": 22,
      "color": "#64748B",
      "textAlign": "center"
    }
  },
  "annotations": [
    {
      "type": "note",
      "text": "HTTP/1.1 长连接",
      "position": { "x": 540, "y": 720 },
      "style": {
        "fontSize": 18,
        "color": "#8B5CF6",
        "backgroundColor": "#1E293B",
        "padding": 8,
        "borderRadius": 6
      }
    },
    {
      "type": "highlight",
      "text": "单向通信，仅服务端 → 客户端",
      "position": { "x": 540, "y": 1100 },
      "style": {
        "fontSize": 18,
        "color": "#F59E0B",
        "backgroundColor": "#1E293B",
        "padding": 8,
        "borderRadius": 6
      }
    }
  ],
  "decorations": [
    {
      "type": "grid",
      "style": "lines",
      "color": "#334155",
      "opacity": 0.1,
      "spacing": 40
    },
    {
      "type": "glow",
      "elements": ["arrows", "connections"],
      "color": "#8B5CF6",
      "intensity": 0.6
    }
  ]
}
```
