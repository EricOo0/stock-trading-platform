import React, { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
} from "lightweight-charts";

interface KLineChartArtifactProps {
  data: any[];
  title?: string;
}

export const KLineChartArtifact: React.FC<KLineChartArtifactProps> = ({
  data,
  title,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 1. Process Data
    const rawData = Array.isArray(data) ? data : (data as any)?.data || [];
    if (rawData.length === 0) return;

    // Parse and sort data
    const chartData = rawData
      .map((d: any) => {
        // Ensure valid numbers
        const open = parseFloat(d.open ?? d.Open ?? d.close ?? d.Close ?? 0);
        const high = parseFloat(d.high ?? d.High ?? d.close ?? d.Close ?? 0);
        const low = parseFloat(d.low ?? d.Low ?? d.close ?? d.Close ?? 0);
        const close = parseFloat(d.close ?? d.Close ?? 0);

        // Handle date/time
        // lightweight-charts expects 'time' field.
        // If it's a timestamp (number), perfectly fine. If string, needs YYYY-MM-DD.
        let time = d.date || d.timestamp || d.Date || "";

        // If it's an ISO string (e.g. 2025-11-14T00:00:00), extract YYYY-MM-DD
        if (typeof time === "string" && time.includes("T")) {
          time = time.split("T")[0];
        }

        // Simple heuristic: if it looks like a full ISO string, might need processing,
        // but lightweight charts handles many formats. Let's pass it through.

        return { time, open, high, low, close };
      })
      // Filter invalid
      .filter((d: any) => d.open && d.close && d.time)
      .sort((a: any, b: any) => {
        const tA = new Date(a.time).getTime();
        const tB = new Date(b.time).getTime();
        return tA - tB;
      })
      // Remove duplicates? Lightweight charts errors on duplicate times.
      // Let's deduce distinct times just in case.
      .filter(
        (item: any, index: number, self: any[]) =>
          index === self.findIndex((t: any) => t.time === item.time),
      );

    if (chartInstanceRef.current) {
      chartInstanceRef.current.remove();
    }

    // 2. Create Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "white" },
        textColor: "#333",
      },
      width: chartContainerRef.current.clientWidth,
      height: 320,
      grid: {
        vertLines: { color: "#f0f0f0" },
        horzLines: { color: "#f0f0f0" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "#d1d5db",
        entireTextOnly: true,
      },
      timeScale: {
        borderColor: "#d1d5db",
        timeVisible: true,
      },
    });

    chartInstanceRef.current = chart;

    // 3. Add Candlestick Series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    candlestickSeries.setData(chartData);
    chart.timeScale().fitContent();

    // 4. Handle Resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, [data]);

  return (
    <div className="w-full bg-white border border-gray-200 rounded-lg p-3 my-2 shadow-sm">
      <div className="flex justify-between items-center mb-2">
        <h4 className="text-sm font-semibold text-gray-700 uppercase">
          {title || "K-Line Chart"}
        </h4>
        <div className="text-xs text-gray-400 italic">
          Powered by Lightweight Charts
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full h-[320px]" />
    </div>
  );
};
