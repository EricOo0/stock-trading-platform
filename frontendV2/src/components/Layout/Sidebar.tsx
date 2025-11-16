import React from 'react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  color: string;
  activeColor: string;
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
      icon: '🏠',
      color: '#8b5cf6',
      activeColor: '#7c3aed'
    },
    {
      id: 'market-query',
      label: '行情查询',
      icon: '📈',
      color: '#3b82f6',
      activeColor: '#2563eb'
    },
    {
      id: 'technical-analysis',
      label: '技术分析',
      icon: '📊',
      color: '#10b981',
      activeColor: '#059669'
    },
    {
      id: 'stock-search',
      label: '股票搜索',
      icon: '🔍',
      color: '#f59e0b',
      activeColor: '#d97706'
    },
    {
      id: 'watchlist',
      label: '自选股票',
      icon: '👁️',
      color: '#ef4444',
      activeColor: '#dc2626'
    }
  ];

  return (
    <div style={{
      width: isCollapsed ? '80px' : '280px',
      height: '100vh',
      background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      borderRight: '1px solid rgba(255,255,255,0.1)',
      transition: 'all 0.3s ease',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '4px 0 20px rgba(0,0,0,0.1)'
    }}>
      {/* 头部 - Logo和折叠按钮 */}
      <div style={{
        padding: '24px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {!isCollapsed && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}>
              📈
            </div>
            <span style={{
              fontWeight: '600',
              fontSize: '18px',
              color: 'white',
              letterSpacing: '0.5px'
            }}>
              行情系统
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            border: 'none',
            background: 'rgba(255,255,255,0.1)',
            color: 'rgba(255,255,255,0.7)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            marginLeft: isCollapsed ? 'auto' : '0'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.color = 'white';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
            e.currentTarget.style.color = 'rgba(255,255,255,0.7)';
          }}
        >
          <span style={{
            fontSize: '18px',
            transition: 'transform 0.3s ease'
          }}>
            {isCollapsed ? '→' : '←'}
          </span>
        </button>
      </div>

      {/* 菜单项 */}
      <div style={{
        flex: 1,
        padding: '16px 0'
      }}>
        <nav style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          padding: '0 16px'
        }}>
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: isCollapsed ? 'center' : 'flex-start',
                padding: '16px',
                borderRadius: '12px',
                border: 'none',
                background: activeTab === item.id 
                  ? `linear-gradient(135deg, ${item.activeColor}, ${item.color})` 
                  : 'transparent',
                color: activeTab === item.id ? 'white' : 'rgba(255,255,255,0.7)',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseOver={(e) => {
                if (activeTab !== item.id) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                  e.currentTarget.style.color = 'white';
                }
              }}
              onMouseOut={(e) => {
                if (activeTab !== item.id) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'rgba(255,255,255,0.7)';
                }
              }}
              title={isCollapsed ? item.label : ''}
            >
              <div style={{
                fontSize: '20px',
                marginRight: isCollapsed ? '0' : '12px',
                filter: activeTab === item.id ? 'brightness(1.2)' : 'none'
              }}>
                {item.icon}
              </div>
              {!isCollapsed && (
                <span style={{
                  fontWeight: '500',
                  fontSize: '15px',
                  letterSpacing: '0.3px'
                }}>
                  {item.label}
                </span>
              )}
              {activeTab === item.id && (
                <div style={{
                  position: 'absolute',
                  right: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: '6px',
                  height: '24px',
                  background: 'rgba(255,255,255,0.8)',
                  borderRadius: '3px',
                  boxShadow: '0 2px 8px rgba(255,255,255,0.3)'
                }} />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* 底部信息 */}
      <div style={{
        padding: '20px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        textAlign: 'center'
      }}>
        {!isCollapsed && (
          <div style={{
            fontSize: '12px',
            color: 'rgba(255,255,255,0.6)',
            lineHeight: '1.5'
          }}>
            <div>版本 1.0.0</div>
            <div style={{ marginTop: '4px' }}>© 2024 行情系统</div>
          </div>
        )}
        {isCollapsed && (
          <div style={{
            fontSize: '10px',
            color: 'rgba(255,255,255,0.4)'
          }}>
            v1.0
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;