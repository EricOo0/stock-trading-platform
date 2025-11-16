import React, { useEffect } from 'react';

const DebugPage: React.FC = () => {
  useEffect(() => {
    console.log('=== 调试信息 ===');
    console.log('1. 检查Tailwind类名是否生效');
    console.log('2. 检查颜色变量是否定义');
    console.log('3. 检查CSS是否正确加载');
    
    // 创建测试元素
    const testDiv = document.createElement('div');
    testDiv.className = 'bg-blue-600 text-white p-4';
    testDiv.textContent = '如果看到这个蓝色背景的div，说明Tailwind正常工作';
    document.body.appendChild(testDiv);
    
    // 检查CSS变量
    const computedStyle = window.getComputedStyle(document.body);
    console.log('Body背景色:', computedStyle.backgroundColor);
    
    return () => {
      document.body.removeChild(testDiv);
    };
  }, []);

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f0f0f0',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#333', textAlign: 'center' }}>调试页面</h1>
      
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        margin: '20px 0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2>样式测试</h2>
        <div style={{
          display: 'flex',
          gap: '10px',
          marginTop: '10px'
        }}>
          <div style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '10px',
            borderRadius: '4px'
          }}>
            蓝色测试
          </div>
          <div style={{
            backgroundColor: '#10b981',
            color: 'white',
            padding: '10px',
            borderRadius: '4px'
          }}>
            绿色测试
          </div>
          <div style={{
            backgroundColor: '#ef4444',
            color: 'white',
            padding: '10px',
            borderRadius: '4px'
          }}>
            红色测试
          </div>
        </div>
      </div>
      
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        margin: '20px 0'
      }}>
        <h2>内联样式测试</h2>
        <p>如果上面的颜色块正常显示，说明基础样式功能正常</p>
        <p>请检查浏览器控制台是否有错误信息</p>
      </div>
    </div>
  );
};

export default DebugPage;