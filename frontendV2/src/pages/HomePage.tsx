import React from 'react';

interface HomePageProps {
  onNavigate?: (tab: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const features = [
    {
      icon: '📈',
      title: '实时行情',
      description: 'A股、美股、港股实时数据',
      color: '#3b82f6'
    },
    {
      icon: '📊',
      title: '技术分析',
      description: '专业K线图和技术指标',
      color: '#10b981'
    },
    {
      icon: '🔍',
      title: '智能搜索',
      description: '多方式股票搜索',
      color: '#8b5cf6'
    },
    {
      icon: '👁️',
      title: '自选管理',
      description: '个性化股票监控',
      color: '#f59e0b'
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
    <div style={{
      height: '100%',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Hero Section - 30% */}
      <div style={{
        flex: '0 0 30%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        color: 'white',
        padding: '20px'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          background: 'rgba(255,255,255,0.2)',
          borderRadius: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '16px',
          fontSize: '28px'
        }}>
          📈
        </div>
        
        <h1 style={{
          fontSize: 'clamp(1.5rem, 3vw, 2.2rem)',
          fontWeight: '700',
          marginBottom: '12px',
          lineHeight: '1.2'
        }}>
          智能行情查询系统
        </h1>
        
        <p style={{
          fontSize: 'clamp(0.85rem, 2vw, 1rem)',
          marginBottom: '20px',
          opacity: '0.9',
          maxWidth: '400px',
          lineHeight: '1.4'
        }}>
          专业的金融市场数据平台，为您提供实时、准确、全面的股票行情信息
        </p>
        
        <button 
          onClick={handleExperienceClick}
          style={{
            background: 'white',
            color: '#667eea',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
          }} 
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
          }} 
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
          }}
        >
          立即体验
        </button>
      </div>

      {/* Features Section - 40% */}
      <div style={{
        flex: '0 0 40%',
        background: 'white',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '20px'
        }}>
          <h2 style={{
            fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)',
            fontWeight: '700',
            color: '#1f2937',
            marginBottom: '8px'
          }}>
            核心功能
          </h2>
          <p style={{
            fontSize: '0.9rem',
            color: '#6b7280',
            maxWidth: '300px',
            margin: '0 auto'
          }}>
            全方位的金融数据服务
          </p>
        </div>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '16px',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          {features.map((feature, index) => (
            <div key={index} style={{
              background: 'white',
              padding: '16px',
              borderRadius: '10px',
              textAlign: 'center',
              boxShadow: '0 2px 10px rgba(0,0,0,0.08)',
              transition: 'all 0.3s ease',
              borderTop: `3px solid ${feature.color}`
            }} onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 15px rgba(0,0,0,0.12)';
            }} onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 10px rgba(0,0,0,0.08)';
            }}>
              <div style={{
                fontSize: '28px',
                marginBottom: '8px'
              }}>
                {feature.icon}
              </div>
              <h3 style={{
                fontSize: '0.95rem',
                fontWeight: '600',
                color: '#1f2937',
                marginBottom: '4px'
              }}>
                {feature.title}
              </h3>
              <p style={{
                color: '#6b7280',
                lineHeight: '1.4',
                fontSize: '0.8rem'
              }}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section - 20% */}
      <div style={{
        flex: '0 0 20%',
        background: '#f9fafb',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
          gap: '16px',
          textAlign: 'center',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          {stats.map((stat, index) => (
            <div key={index}>
              <div style={{
                fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)',
                fontWeight: '700',
                color: '#3b82f6',
                marginBottom: '2px'
              }}>
                {stat.value}
                <span style={{
                  fontSize: '0.8rem',
                  color: '#6b7280',
                  marginLeft: '2px'
                }}>
                  {stat.suffix}
                </span>
              </div>
              <div style={{
                color: '#6b7280',
                fontSize: '0.8rem'
              }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer - 10% */}
      <div style={{
        flex: '0 0 10%',
        background: '#1f2937',
        color: 'white',
        padding: '12px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '4px'
        }}>
          <div style={{
            width: '24px',
            height: '24px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px'
          }}>
            📈
          </div>
          <span style={{
            fontSize: '0.8rem',
            color: '#9ca3af'
          }}>
            智能行情查询系统
          </span>
        </div>
        <p style={{
          color: '#9ca3af',
          margin: 0,
          fontSize: '0.7rem'
        }}>
          © 2024 保留所有权利
        </p>
      </div>
    </div>
  );
};

export default HomePage;