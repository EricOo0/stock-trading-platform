import React from 'react';
import { 
  Users, 
  Brain, 
  TrendingUp, 
  Activity, 
  Github, 
  Database, 
  Globe, 
  Newspaper,
  ArrowRight,
  LineChart,
  Zap
} from 'lucide-react';
import { motion } from 'framer-motion';

import { SectorFlowCard } from '../components/Home/SectorFlowCard';

interface HomePageProps {
  onNavigate?: (tab: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  const coreModules = [
    {
      id: 'council',
      title: 'AI 顾问团',
      subtitle: 'Council of Agents',
      description: '多智能体协同决策系统。模拟专业投委会，集成宏观、技术、舆情等多维度专家Agent，提供全方位的投资建议。',
      icon: <Users size={32} className="text-blue-400" />,
      color: 'from-blue-500/20 to-indigo-500/20',
      border: 'hover:border-blue-500/50',
      action: '进入会议室'
    },
    {
      id: 'inspiring',
      title: '深度投研 Agent',
      subtitle: 'Deep Research',
      description: '具备长短期记忆的自主研究员。自动拆解任务，搜集全网信息，通过反思与迭代生成深度的研报内容。',
      icon: <Brain size={32} className="text-purple-400" />,
      color: 'from-purple-500/20 to-pink-500/20',
      border: 'hover:border-purple-500/50',
      action: '开始研究'
    }
  ];

  const functionalModules = [
    {
      id: 'market-query',
      title: '市场全景',
      description: '实时行情与资金流向',
      icon: <TrendingUp size={24} className="text-emerald-400" />,
      delay: 0.2
    },
    {
      id: 'macro-data',
      title: '宏观数据',
      description: '经济指标与政策追踪',
      icon: <Globe size={24} className="text-cyan-400" />,
      delay: 0.3
    },
    {
      id: 'news-sentiment',
      title: '舆情分析',
      description: '全网新闻情感量化',
      icon: <Newspaper size={24} className="text-orange-400" />,
      delay: 0.4
    },
    {
      id: 'stock-simulation',
      title: '模拟回测',
      description: '策略验证与沙盘推演',
      icon: <Activity size={24} className="text-red-400" />,
      delay: 0.5
    },
    {
      id: 'technical-analysis',
      title: '技术分析',
      description: '专业K线与指标系统',
      icon: <LineChart size={24} className="text-yellow-400" />,
      delay: 0.6
    },
    {
      id: 'memory-viz',
      title: '记忆可视化',
      description: 'Agent 记忆库透视',
      icon: <Database size={24} className="text-teal-400" />,
      delay: 0.7
    }
  ];

  return (
    <div className="min-h-full flex flex-col bg-[#0B1120] text-slate-200">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 flex-1 flex flex-col max-w-7xl mx-auto w-full px-6 py-12">
        
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-8 space-y-4"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium mb-2">
            <Zap size={12} />
            <span>Next-Gen AI Investment Platform</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
              AI-Driven
            </span> Financial Intelligence
          </h1>
          
          <p className="max-w-2xl mx-auto text-base text-slate-400 leading-relaxed">
            融合多智能体协作、深度记忆系统与实时市场数据的下一代投资研究平台。
            让 AI 成为您的私人首席投资官。
          </p>

          <div className="flex items-center justify-center gap-4 pt-2">
            <button 
              onClick={() => window.open('https://github.com/EricOo0/stock-trading-platform', '_blank')}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition-all hover:scale-105 text-sm"
            >
              <Github size={18} />
              <span>View on GitHub</span>
            </button>
            <button 
              onClick={() => onNavigate && onNavigate('inspiring')}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 transition-all hover:scale-105 font-medium text-sm"
            >
              <Brain size={18} />
              <span>开始深度投研</span>
            </button>
          </div>
        </motion.div>

        {/* Sector Analysis Card */}
        <SectorFlowCard />

        {/* Core Modules (Big Cards) */}

        {/* Functional Modules (Grid) */}
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
            <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Analysis Tools</span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
          </div>

          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {functionalModules.map((module) => (
              <motion.div
                key={module.id}
                variants={itemVariants}
                onClick={() => onNavigate && onNavigate(module.id)}
                className="group flex items-center gap-4 p-4 rounded-xl bg-slate-800/30 border border-slate-700/30 hover:bg-slate-800/80 hover:border-slate-600 transition-all cursor-pointer"
              >
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 group-hover:border-slate-600 transition-colors">
                  {module.icon}
                </div>
                <div>
                  <h4 className="text-base font-semibold text-slate-200 group-hover:text-white transition-colors">
                    {module.title}
                  </h4>
                  <p className="text-xs text-slate-500 group-hover:text-slate-400 transition-colors">
                    {module.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Footer */}
        <div className="mt-auto pt-20 pb-6 text-center">
          <div className="flex items-center justify-center gap-2 text-slate-500 mb-4 hover:text-blue-400 transition-colors cursor-pointer" onClick={() => window.open('https://github.com/EricOo0/stock-trading-platform', '_blank')}>
            <Github size={16} />
            <span className="text-sm font-medium">EricOo0/stock-trading-platform</span>
          </div>
          <p className="text-xs text-slate-600">
            © 2025 AI Investment Research Platform. Open Source Community Edition.
          </p>
        </div>

      </div>
    </div>
  );
};

export default HomePage;
