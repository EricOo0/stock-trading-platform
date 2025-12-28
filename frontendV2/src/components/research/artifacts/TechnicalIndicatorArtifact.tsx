import React from "react";

interface TechnicalIndicatorArtifactProps {
  data: {
    trend?: {
      status: string;
      ma5?: number;
      ma20?: number;
      ma60?: number;
    };
    rsi?: {
      value: number;
      status: string;
    };
    macd?: {
      macd: number;
      signal: number;
      status: string;
    };
    bollinger?: {
      upper: number;
      lower: number;
      status: string;
    };
    error?: string;
  };
  title?: string;
}

export const TechnicalIndicatorArtifact: React.FC<
  TechnicalIndicatorArtifactProps
> = ({ data, title }) => {
  if (data.error) {
    return (
      <div className="text-red-500 p-3 text-sm italic">Error: {data.error}</div>
    );
  }

  const getStatusColor = (status: string) => {
    const s = status.toUpperCase();
    if (
      s.includes("UP") ||
      s.includes("BULL") ||
      s.includes("GOLDEN") ||
      s.includes("OVERBOUGHT")
    ) {
      return "text-green-600 bg-green-50 border-green-100";
    }
    if (
      s.includes("DOWN") ||
      s.includes("BEAR") ||
      s.includes("DEATH") ||
      s.includes("OVERSOLD")
    ) {
      return "text-red-600 bg-red-50 border-red-100";
    }
    return "text-gray-600 bg-gray-50 border-gray-100";
  };

  const renderBadge = (status: string) => (
    <span
      className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${getStatusColor(status)}`}
    >
      {status.replace("_", " ")}
    </span>
  );

  return (
    <div className="w-full bg-white border border-gray-200 rounded-lg p-3 my-2 shadow-sm">
      <h4 className="text-xs font-bold text-gray-500 mb-3 uppercase flex items-center gap-2">
        <span className="w-1.5 h-3 bg-blue-500 rounded-full"></span>
        {title || "Technical Indicators Analysis"}
      </h4>

      <div className="grid grid-cols-2 gap-3">
        {/* Trend Card */}
        {data.trend && (
          <div className="p-2 border border-gray-50 rounded bg-gray-50/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[11px] text-gray-400 font-medium">
                TREND
              </span>
              {renderBadge(data.trend.status)}
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">MA5</span>
                <span className="font-mono font-medium">
                  {data.trend.ma5?.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">MA20</span>
                <span className="font-mono font-medium">
                  {data.trend.ma20?.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">MA60</span>
                <span className="font-mono font-medium">
                  {data.trend.ma60?.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* MACD Card */}
        {data.macd && (
          <div className="p-2 border border-gray-50 rounded bg-gray-50/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[11px] text-gray-400 font-medium">
                MACD
              </span>
              {renderBadge(data.macd.status)}
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">DIF</span>
                <span className="font-mono font-medium">
                  {data.macd.macd?.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">DEA</span>
                <span className="font-mono font-medium">
                  {data.macd.signal?.toFixed(3)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* RSI Card */}
        {data.rsi && (
          <div className="p-2 border border-gray-50 rounded bg-gray-50/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[11px] text-gray-400 font-medium">
                RSI (14)
              </span>
              {renderBadge(data.rsi.status)}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-gray-700">
                {data.rsi.value?.toFixed(1)}
              </span>
              <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${data.rsi.value > 70 ? "bg-red-400" : data.rsi.value < 30 ? "bg-green-400" : "bg-blue-400"}`}
                  style={{ width: `${data.rsi.value}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {/* Bollinger Card */}
        {data.bollinger && (
          <div className="p-2 border border-gray-50 rounded bg-gray-50/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[11px] text-gray-400 font-medium">
                BOLLINGER
              </span>
              {renderBadge(data.bollinger.status)}
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Upper</span>
                <span className="font-mono font-medium">
                  {data.bollinger.upper?.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Lower</span>
                <span className="font-mono font-medium">
                  {data.bollinger.lower?.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
