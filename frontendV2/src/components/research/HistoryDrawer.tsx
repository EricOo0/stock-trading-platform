import React, { useEffect, useState } from 'react';
import type { ResearchJob } from '../../hooks/useResearchStream';

interface HistoryDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    onSelectJob: (jobId: string) => void;
    onNewChat: () => void;
    currentJobId?: string;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({ isOpen, onClose, onSelectJob, onNewChat, currentJobId }) => {
    const [history, setHistory] = useState<ResearchJob[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            fetch('http://localhost:8000/api/research/history')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        setHistory(data.data);
                    }
                })
                .catch(err => console.error("Failed to fetch history:", err))
                .finally(() => setLoading(false));
        }
    }, [isOpen]);

    return (
        <div className={`fixed inset-y-0 right-0 w-80 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-50 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="flex items-center justify-between p-4 border-b">
                <h2 className="text-lg font-semibold text-gray-800">Research History</h2>
                <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div className="p-4 border-b border-gray-100">
                <button
                    onClick={() => {
                        onNewChat();
                        onClose();
                    }}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Chat
                </button>
            </div>

            <div className="p-4 overflow-y-auto h-[calc(100%-130px)]">
                {loading ? (
                    <div className="flex justify-center py-4">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {history.map(job => (
                            <div
                                key={job.id}
                                onClick={() => {
                                    onSelectJob(job.id);
                                    onClose();
                                }}
                                className={`p-3 rounded-lg border cursor-pointer transition-colors ${job.id === currentJobId
                                    ? 'bg-blue-50 border-blue-200 ring-1 ring-blue-300'
                                    : 'bg-white border-gray-200 hover:bg-gray-50'
                                    }`}
                            >
                                <div className="text-sm font-medium text-gray-900 mb-1 line-clamp-2">
                                    {job.query}
                                </div>
                                <div className="flex items-center justify-between text-xs text-gray-500">
                                    <span className={`px-2 py-0.5 rounded-full ${job.status === 'completed' ? 'bg-green-100 text-green-800' :
                                        job.status === 'failed' ? 'bg-red-100 text-red-800' :
                                            'bg-blue-100 text-blue-800'
                                        }`}>
                                        {job.status}
                                    </span>
                                    {/* Ideally show date here if available in ResearchJob interface */}
                                </div>
                            </div>
                        ))}
                        {history.length === 0 && (
                            <div className="text-center text-gray-500 py-8">
                                No history found
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
