import React from "react";
import { KLineChartArtifact } from "./KLineChartArtifact";
import { FinancialTableArtifact } from "./FinancialTableArtifact";
import { MacroChartArtifact } from "./MacroChartArtifact";
import { PDFPreviewArtifact } from "./PDFPreviewArtifact";
import { WordCloudArtifact } from "./WordCloudArtifact";
import { TechnicalIndicatorArtifact } from "./TechnicalIndicatorArtifact";
import { SearchSourceArtifact } from "./SearchSourceArtifact";

interface ArtifactRendererProps {
  type: string;
  title: string;
  data: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

export const ArtifactRenderer: React.FC<ArtifactRendererProps> = ({
  type,
  title,
  data,
}) => {
  switch (type) {
    case "kline":
      return <KLineChartArtifact data={data} title={title} />;
    case "financial_table":
      return <FinancialTableArtifact data={data} />; // Title is handled by wrapper or component if needed
    case "macro_chart":
      return <MacroChartArtifact data={data} title={title} />;
    case "pdf_preview":
      return <PDFPreviewArtifact data={data} title={title} />;
    case "wordcloud":
      return <WordCloudArtifact data={data} title={title} />;
    case "technical_indicators":
      return <TechnicalIndicatorArtifact data={data} title={title} />;
    case "search_results":
      return <SearchSourceArtifact data={data} title={title} />;
    default:
      return (
        <div className="bg-gray-100 border border-gray-200 p-3 rounded text-sm text-gray-500">
          <p className="font-semibold mb-1">Unknown Artifact: {type}</p>
          <pre className="text-xs overflow-x-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      );
  }
};
