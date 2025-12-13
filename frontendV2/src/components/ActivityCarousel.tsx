import React from 'react';
import { FiSearch, FiExternalLink, FiCheckCircle, FiLoader } from 'react-icons/fi';

export interface ActivityCard {
    id: string;
    type: 'tool' | 'thought' | 'report';
    title: string;
    detail: string;
    status: 'pending' | 'completed' | 'failed';
    timestamp: number;
}

interface ActivityCarouselProps {
    activities: ActivityCard[];
}

const ActivityCarousel: React.FC<ActivityCarouselProps> = ({ activities }) => {
    // Show only the most relevant activities (reverse order or scrollable)
    // For a carousel, we might want a horizontal scroll or just a list of cards.
    // Given the name "Carousel", let's make it a horizontal scroll container.

    if (activities.length === 0) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
                    <FiSearch size={24} className="opacity-50" />
                </div>
                <p className="text-sm font-medium">Ready to research</p>
                <p className="text-xs opacity-60 mt-1">Enter a topic to begin deep analysis</p>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar-light">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 pb-10">
                {activities.map((activity) => (
                    <div
                        key={activity.id}
                        className={`
                            group relative p-5 rounded-2xl border transition-all duration-300
                            ${activity.status === 'pending'
                                ? 'bg-white border-orange-200 shadow-[0_4px_20px_-4px_rgba(251,146,60,0.15)] ring-1 ring-orange-100'
                                : 'bg-white border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200'
                            }
                        `}
                    >
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <div className={`
                                    w-8 h-8 rounded-lg flex items-center justify-center
                                    ${activity.status === 'pending' ? 'bg-orange-50 text-orange-600' : 'bg-gray-50 text-gray-600'}
                                `}>
                                    {activity.status === 'pending' ? <FiLoader className="animate-spin" /> : <FiSearch />}
                                </div>
                                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                                    {new Date(activity.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                            </div>
                            {activity.status === 'completed' && <FiCheckCircle className="text-green-500" />}
                        </div>

                        <h4 className="text-sm font-bold text-gray-900 mb-2 line-clamp-1 group-hover:text-blue-600 transition-colors">
                            {activity.title}
                        </h4>

                        <div className="text-xs text-gray-500 leading-relaxed max-h-32 overflow-y-auto custom-scrollbar-light mb-3 whitespace-pre-wrap font-mono bg-gray-50 p-2 rounded">
                            {activity.detail}
                        </div>

                        <div className="mt-auto pt-3 border-t border-gray-50 flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                                <span className={`w-1.5 h-1.5 rounded-full ${activity.status === 'pending' ? 'bg-orange-400 animate-pulse' : 'bg-green-400'}`} />
                                <span className="text-[10px] font-medium text-gray-400 capitalize">{activity.status}</span>
                            </div>

                            {/* Attempt to find a URL in the detail to make the button functional */}
                            {(() => {
                                const urlMatch = activity.detail.match(/https?:\/\/[^\s"',]+/);
                                const url = urlMatch ? urlMatch[0] : null;

                                return url ? (
                                    <a
                                        href={url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[10px] font-semibold text-blue-600 flex items-center gap-1 hover:underline decoration-blue-200"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        View Source <FiExternalLink />
                                    </a>
                                ) : (
                                    <span className="text-[10px] text-gray-300 cursor-not-allowed flex items-center gap-1">
                                        No Link <FiExternalLink />
                                    </span>
                                );
                            })()}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ActivityCarousel;
