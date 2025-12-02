import React from 'react';
import { Home, BarChart2, LineChart, TrendingUp, Search, Eye, ChevronLeft, ChevronRight, Globe, Gamepad2 } from 'lucide-react';

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
      id: 'market-query',
      label: '行情查询',
      icon: <TrendingUp size={20} />,
      color: 'text-blue-500'
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
      id: 'macro-data',
      label: '宏观数据',
      icon: <Globe size={20} />,
      color: 'text-cyan-500'
    }
  ];

  return (
    <div
      className={`
        h-screen bg-slate-900 border-r border-slate-800 flex flex-col shadow-xl transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-20' : 'w-72'}
      `}
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
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
                  w-full flex items-center p-3 rounded-xl transition-all duration-200 group relative overflow-hidden
                  ${isCollapsed ? 'justify-center' : 'justify-start'}
                  ${isActive
                    ? 'bg-gradient-to-r from-slate-800 to-slate-800/50 text-white shadow-md border border-slate-700/50'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                  }
                `}
                title={isCollapsed ? item.label : ''}
              >
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 rounded-l-xl" />
                )}

                <div className={`
                  transition-transform duration-200
                  ${isActive ? item.color : 'text-slate-400 group-hover:text-white'}
                  ${!isCollapsed && 'mr-3'}
                  ${isActive && 'scale-110'}
                `}>
                  {item.icon}
                </div>

                {!isCollapsed && (
                  <span className="font-medium tracking-wide text-sm">
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}

        </nav>
      </div>

      {/* Footer */}
      <div className="p-5 border-t border-slate-800 text-center">
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