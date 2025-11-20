import React from 'react';
import { TrendingUp, BarChart2, Search, Eye } from 'lucide-react';

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
    <div className="h-full flex flex-col bg-gray-50 overflow-y-auto">
      {/* Hero Section */}
      <div className="relative bg-slate-900 text-white py-20 px-6 text-center overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('https://images.unsplash.com/photo-1611974765270-ca12586343bb?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80')] opacity-5 bg-cover bg-center" />

        <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center">
          <div className="w-16 h-16 bg-blue-600/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mb-6 border border-blue-500/30">
            <TrendingUp size={36} className="text-blue-400" />
          </div>

          <h1 className="text-4xl md:text-5xl font-bold mb-4 leading-tight tracking-tight text-white">
            智能行情查询系统
          </h1>

          <p className="text-lg md:text-xl text-slate-300 mb-8 max-w-lg leading-relaxed">
            专业的金融市场数据平台，为您提供实时、准确、全面的股票行情信息
          </p>

          <button
            onClick={handleExperienceClick}
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold shadow-lg hover:bg-blue-700 hover:-translate-y-0.5 transition-all duration-300 flex items-center gap-2 group"
          >
            立即体验
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 px-6 max-w-6xl mx-auto w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            核心功能
          </h2>
          <p className="text-gray-500">
            全方位的金融数据服务
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className={`bg-white p-6 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border-t-4 ${feature.color} group`}
            >
              <div className="mb-4 transform group-hover:scale-110 transition-transform duration-300 inline-block">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white py-12 border-y border-gray-100">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {stats.map((stat, index) => (
            <div key={index} className="p-4">
              <div className="text-3xl font-bold text-blue-600 mb-1">
                {stat.value}
                <span className="text-sm text-gray-500 ml-1 font-normal">{stat.suffix}</span>
              </div>
              <div className="text-sm text-gray-500 font-medium">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-slate-900 text-slate-400 py-8 text-center mt-auto">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-violet-600 rounded flex items-center justify-center text-white text-xs">
            <TrendingUp size={14} />
          </div>
          <span className="font-medium text-slate-300">智能行情查询系统</span>
        </div>
        <p className="text-xs">
          © 2024 保留所有权利
        </p>
      </div>
    </div>
  );
};

export default HomePage;