import React from 'react';
import { Home, BarChart2, TrendingUp, Search, Eye, ChevronLeft, ChevronRight, Globe, Gamepad2, FileText, Brain } from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggle,
  activeTab,
  onTabChange
}) => {
  const menuItems: MenuItem[] = [
    {
      id: 'home',
      label: '首页',
      icon: <Home size={20} />,
      color: 'text-violet-500'
    },
    {
      id: 'council',
      label: 'AI 顾问团',
      icon: <Gamepad2 size={20} />,
      color: 'text-pink-500'
    },
    {
      id: 'macro-data',
      label: '宏观数据',
      icon: <Globe size={20} />,
      color: 'text-cyan-500'
    },
    {
      id: 'stock-simulation',
      label: '模拟回测',
      icon: <TrendingUp size={20} />,
      color: 'text-orange-500'
    },
    {
      id: 'market-query',
      label: '行情查询',
      icon: <TrendingUp size={20} />,
      color: 'text-blue-500'
    },
    {
      id: 'financial-analysis',
      label: '新财报分析',
      icon: <FileText size={20} />,
      color: 'text-indigo-400'
    },
    {
      id: 'technical-analysis',
      label: '技术分析',
      icon: <BarChart2 size={20} />,
      color: 'text-emerald-500'
    },
    {
      id: 'stock-search',
      label: '股票搜索',
      icon: <Search size={20} />,
      color: 'text-amber-500'
    },
    {
      id: 'watchlist',
      label: '自选股票',
      icon: <Eye size={20} />,
      color: 'text-red-500'
    },
    {
      id: 'memory-viz',
      label: '记忆可视化',
      icon: <Brain size={20} />,
      color: 'text-purple-500'
    }
  ];

  return (
    <div
      className={`
        h-screen bg-slate-900 border-r border-slate-700 flex flex-col shadow-xl transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-20' : 'w-60'}
      `}
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-700 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 text-white">
              <TrendingUp size={24} />
            </div>
            <span className="font-bold text-lg text-white tracking-wide">
              AI-Fundin
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          className={`
            w-8 h-8 rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white transition-all flex items-center justify-center
            ${isCollapsed ? 'mx-auto' : ''}
          `}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Menu */}
      <div className="flex-1 py-6 px-4 overflow-y-auto">
        <nav className="flex flex-col gap-2">
          {menuItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`
                  w-full flex items-center p-3 rounded-2xl transition-all duration-300 group relative overflow-hidden outline-none
                  ${isCollapsed ? 'justify-center' : 'justify-start'}
                  ${isActive
                    ? 'bg-gradient-to-r from-slate-800/80 to-slate-800/40 text-white shadow-lg border border-slate-700/30'
                    : 'text-slate-400 hover:bg-slate-800/30 hover:text-slate-200 border border-transparent'
                  }
                `}
                title={isCollapsed ? item.label : ''}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-r-full shadow-[0_0_12px_rgba(59,130,246,0.5)]" />
                )}

                <div className={`
                  transition-all duration-300
                  ${isActive ? item.color : 'text-slate-500 group-hover:text-slate-300'}
                  ${!isCollapsed && 'mr-3.5'}
                  ${isActive && 'scale-110 drop-shadow-md'}
                `}>
                  {item.icon}
                </div>

                {!isCollapsed && (
                  <span className={`font-medium tracking-wide text-sm transition-colors duration-300 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}

        </nav>
      </div>

      {/* Footer */}
      <div className="p-5 border-t border-slate-700 text-center">
        {!isCollapsed ? (
          <div className="text-xs text-slate-500 leading-relaxed">
            <div className="font-medium text-slate-400">v1.0.0</div>
            <div>© 2024 AI-Fundin</div>
          </div>
        ) : (
          <div className="text-[10px] text-slate-600 font-mono">v1.0</div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;