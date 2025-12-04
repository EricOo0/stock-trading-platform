import React from 'react';
import { Bell, Settings, User, TrendingUp } from 'lucide-react';

interface HeaderProps {
  title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  return (
    <div className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-700 flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 text-white">
          <TrendingUp size={20} />
        </div>
        <h1 className="text-xl font-bold text-white tracking-tight">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <button className="w-10 h-10 rounded-xl border border-slate-700 bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white hover:border-slate-600 transition-all flex items-center justify-center">
          <Bell size={18} />
        </button>

        <button className="w-10 h-10 rounded-xl border border-slate-700 bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white hover:border-slate-600 transition-all flex items-center justify-center">
          <Settings size={18} />
        </button>

        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl flex items-center justify-center cursor-pointer shadow-lg shadow-blue-500/20 text-white hover:scale-105 hover:shadow-blue-500/30 transition-all duration-200">
          <User size={18} />
        </div>
      </div>
    </div>
  );
};

export default Header;