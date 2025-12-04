export interface FinancialMetric {
  date: string;
  revenue: number;
  net_income: number;
  gross_profit: number;
  operating_income: number;
}

export interface FinancialReport {
  symbol: string;
  metrics: FinancialMetric[];
  latest_report?: {
    market?: string;
    status?: string;
    title?: string;
    form_type?: string;
    filing_date?: string;
    date?: string;
    message?: string;
    download_url?: string;
    ir_url?: string;
    hkexnews_url?: string;
    cninfo_url?: string;
    suggestions?: string[];
  };
}

export interface AnchorInfo {
  type: 'pdf' | 'html';
  page?: number; // For PDF
  rect?: [number, number, number, number]; // [x0, y0, x1, y1] For PDF
  id?: string; // For HTML
  content?: string;
}

export interface Citation {
  id: string;
  content: string;
  page_num: number;
  file_name?: string;
  rect?: [number, number, number, number];
  type?: 'pdf' | 'html';
}

export interface AnchorMap {
  [key: string]: AnchorInfo;
}
