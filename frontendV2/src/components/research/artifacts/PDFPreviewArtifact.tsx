import React from 'react';
import { FileText, Download, ExternalLink } from 'lucide-react';

interface PDFPreviewArtifactProps {
    data: {
        report_info?: {
            title?: string;
            date?: string;
            download_url?: string;
            market?: string;
        };
        pdf_url?: string; // Local URL
        content?: string;
        [key: string]: any;
    };
    title?: string;
}

export const PDFPreviewArtifact: React.FC<PDFPreviewArtifactProps> = ({ data, title }) => {
    const reportInfo = data.report_info || {};
    const downloadUrl = data.pdf_url || reportInfo.download_url;
    const docTitle = reportInfo.title || title || "Financial Document";
    const date = reportInfo.date || "";

    return (
        <div className="flex flex-col border border-gray-200 rounded-lg bg-white overflow-hidden shadow-sm my-2 max-w-sm">
            <div className="bg-red-50 p-4 border-b border-red-100 flex items-start gap-3">
                <div className="bg-red-100 p-2 rounded text-red-600">
                    <FileText size={24} />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate" title={docTitle}>
                        {docTitle}
                    </h3>
                    {date && <p className="text-xs text-gray-500 mt-0.5">{date}</p>}
                </div>
            </div>
            
            <div className="p-3 bg-gray-50 flex gap-2">
                {downloadUrl && (
                    <a 
                        href={downloadUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex-1 flex items-center justify-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-medium py-2 px-3 rounded transition-colors"
                    >
                        <Download size={14} />
                        Download
                    </a>
                )}
                {/* 
                   If we had a dedicated viewer route, we could add a "View" button here.
                   For now, just download/open.
                */}
            </div>
        </div>
    );
};
