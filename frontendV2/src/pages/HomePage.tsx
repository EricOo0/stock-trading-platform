import React from 'react';
import { TrendingUp, BarChart2, Search, Eye } from 'lucide-react';
import { motion } from 'framer-motion';

interface HomePageProps {
  onNavigate?: (tab: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const features = [
    {
      icon: <TrendingUp size={32} className="text-blue-500" />,
      title: '实时行情',
      description: 'A股、美股、港股实时数据',
      color: 'border-blue-500'
    },
    {
      icon: <BarChart2 size={32} className="text-emerald-500" />,
      title: '技术分析',
      description: '专业K线图和技术指标',
      color: 'border-emerald-500'
    },
    {
      icon: <Search size={32} className="text-violet-500" />,
      title: '智能搜索',
      description: '多方式股票搜索',
      color: 'border-violet-500'
    },
    {
      icon: <Eye size={32} className="text-amber-500" />,
      title: '自选管理',
      description: '个性化股票监控',
      color: 'border-amber-500'
    }
  ];

  const stats = [
    { label: '支持市场', value: '3+', suffix: '个' },
    { label: '股票数据', value: '10000+', suffix: '只' },
    { label: '实时更新', value: '1', suffix: '秒' },
    { label: '用户信赖', value: '10000+', suffix: '人' }
  ];

  const handleExperienceClick = () => {
    if (onNavigate) {
      onNavigate('market-query');
    }
  };

  return (
    <div className="min-h-full flex flex-col bg-slate-900">
      {/* Hero Section */}
      <div className="relative bg-slate-900 text-white py-20 px-6 text-center overflow-hidden flex-shrink-0 border-b border-slate-700">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1611974765270-ca12586343bb?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80')] opacity-5 bg-cover bg-center" />

        <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="w-16 h-16 bg-blue-600/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mb-6 border border-blue-500/30"
          >
            <TrendingUp size={36} className="text-blue-400" />
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="text-5xl md:text-6xl font-bold mb-2 leading-tight tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-violet-400"
          >
            AI-Fundin
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="text-xl md:text-2xl font-medium text-white mb-6"
          >
            智能行情查询系统
          </motion.p>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="text-lg text-slate-300 mb-8 max-w-lg leading-relaxed"
          >
            专业的金融市场数据平台，为您提供实时、准确、全面的股票行情信息
          </motion.p>

          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            onClick={handleExperienceClick}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold shadow-lg hover:bg-blue-700 hover:-translate-y-0.5 transition-all duration-300 flex items-center gap-2 group"
          >
            立即体验
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </motion.button>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 px-6 max-w-6xl mx-auto w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-3">
            核心功能
          </h2>
          <p className="text-slate-400">
            全方位的金融数据服务
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className={`bg-slate-800 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border-t-4 ${feature.color} group border-x border-b border-slate-700`}
            >
              <div className="mb-4 transform group-hover:scale-110 transition-transform duration-300 inline-block">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-slate-800 py-12 border-y border-slate-700">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map((stat, index) => (
            <div key={index} className="p-4">
              <div className="text-3xl font-bold text-blue-400 mb-1">
                {stat.value}
                <span className="text-sm text-slate-400 ml-1 font-normal">{stat.suffix}</span>
              </div>
              <div className="text-sm text-slate-400 font-medium">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-slate-900 text-slate-400 py-3 flex items-center justify-center gap-3 mt-auto border-t border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 bg-gradient-to-br from-blue-500 to-violet-600 rounded-md flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <TrendingUp size={12} strokeWidth={3} />
          </div>
          <span className="font-semibold text-slate-300 text-sm tracking-wide">智能行情查询系统</span>
        </div>
        <div className="w-px h-3 bg-slate-700" />
        <p className="text-xs text-slate-500 font-medium">
          © 2024 保留所有权利
        </p>
      </div>
    </div>
  );
};

export default HomePage;