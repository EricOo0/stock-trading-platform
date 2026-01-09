import React from "react";
import { useResearchStream } from "../hooks/useResearchStream";
import { ChatPanel } from "../components/research/ChatPanel";
import { DeepResearchCard } from "../components/research/DeepResearchCard";
import { DashboardPanel } from "../components/research/DashboardPanel";
import { HistoryDrawer } from "../components/research/HistoryDrawer";

const InspiringPage: React.FC = () => {
  const { job, events, startResearch, restoreJob, reset } =
    useResearchStream();

  // Restore job from localStorage on mount
  React.useEffect(() => {
    const savedJobId = localStorage.getItem("research_job_id");
    if (savedJobId) {
      restoreJob(savedJobId);
    }
  }, [restoreJob]);

  const handleSendMessage = (msg: string) => {
    if (!job) {
      startResearch(msg).then(() => {
        // We need to wait for job to be set, but startResearch is async.
        // Actually startResearch sets state. We can use an effect or just wait.
        // Better: Update startResearch to return job ID or use effect on job change.
      });
    } else {
      // TODO: call addRemark API if job is running
      console.log("Adding remark:", msg);
      // This part needs `addRemark` in the hook but for prototype we just log
      fetch(`http://localhost:8000/api/research/${job.id}/remark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ remark: msg }),
      });
    }
  };

  const handleNewChat = () => {
    reset();
    localStorage.removeItem("research_job_id");
    setIsHistoryOpen(false); // Should already be closed by Drawer but good for safety
  };

  // specific effect to save job id
  React.useEffect(() => {
    if (job?.id) {
      localStorage.setItem("research_job_id", job.id);
    }
  }, [job?.id]);

  const [isHistoryOpen, setIsHistoryOpen] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<'result' | 'process'>('result');

  // Parse the latest DeepResearchReport from artifacts
  // We look for an artifact event with type 'deep_research_report'
  const latestReport = React.useMemo(() => {
    const reportEvent = [...events].reverse().find(
      e => e.type === 'artifact' && e.payload?.type === 'deep_research_report'
    );
    if (reportEvent && reportEvent.payload?.data) {
      // If the data is a string (JSON stringified), parse it. 
      // The hook might have already parsed the payload, but let's be safe about 'data' field.
      const data = reportEvent.payload.data;
      // Pydantic .json() returns a string, so we might need to parse if it wasn't auto-parsed
      return typeof data === 'string' ? JSON.parse(data) : data;
    }
    return null;
  }, [events]);

  // Auto-switch to result tab when a report arrives
  React.useEffect(() => {
    if (latestReport) {
      setActiveTab('result');
    }
  }, [latestReport]);

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden relative">
      {" "}
      {/* Added relative for drawer positioning */}
      {/* History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectJob={restoreJob}
        onNewChat={handleNewChat}
        currentJobId={job?.id}
      />
      {/* Split View */}
      {/* Left Panel: Chat (65%) */}
      <div className="w-[65%] min-w-[450px] flex flex-col relative">
        {/* Header Overlay for History Button */}
        <div className="absolute top-4 right-4 z-10">
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="p-2 bg-white rounded-full shadow-md hover:bg-gray-50 text-gray-600 transition-colors"
            title="View History"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
        </div>

        <ChatPanel
          events={events}
          onSendMessage={handleSendMessage}
          isLoading={job?.status === "running" || job?.status === "starting"}
          initialQuery={job?.query}
        />
      </div>
      {/* Right Panel: Dashboard (35%) */}
      <div className="flex-1 h-full border-l border-gray-200 relative flex flex-col bg-gray-900">

        {/* Fixed Header Row */}
        <div className="flex-shrink-0 h-14 border-b border-gray-800 flex items-center justify-between px-4 bg-gray-900/50 backdrop-blur z-20">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider">
            Research Hub
          </div>
          <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
            <button
              onClick={() => setActiveTab('result')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'result' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
            >
              Deep Research
            </button>
            <button
              onClick={() => setActiveTab('process')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'process' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'}`}
            >
              Process Log
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden relative">

          {/* View: Deep Research Result */}
          {activeTab === 'result' && (
            <div className="absolute inset-0 overflow-y-auto p-6 flex flex-col items-center">
              {latestReport ? (
                <div className="w-full max-w-md pb-10">
                  <DeepResearchCard
                    signals={latestReport.signals}
                    analysis={latestReport.analysis}
                    outlook={latestReport.outlook}
                    references={latestReport.references}
                  />
                </div>
              ) : (
                <div className="text-center text-gray-500 mt-20">
                  <div className="animate-pulse mb-3 text-4xl">🔍</div>
                  <p>Analysis in progress...</p>
                  <p className="text-xs mt-2 opacity-60">Wait for the agent to submit the final report.</p>
                  <button onClick={() => setActiveTab('process')} className="mt-4 text-blue-400 hover:underline text-xs">View Process</button>
                </div>
              )}
            </div>
          )}

          {/* View: Process Log */}
          {activeTab === 'process' && (
            <div className="h-full">
              <DashboardPanel events={events} />
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default InspiringPage;
