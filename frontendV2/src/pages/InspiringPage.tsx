import React from "react";
import { useResearchStream } from "../hooks/useResearchStream";
import { ChatPanel } from "../components/research/ChatPanel";
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
      <div className="flex-1 h-full border-l border-gray-200">
        <DashboardPanel events={events} />
      </div>
    </div>
  );
};

export default InspiringPage;
