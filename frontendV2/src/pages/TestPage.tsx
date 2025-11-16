import React from 'react';

const TestPage: React.FC = () => {
  return (
    <div style={{ 
      backgroundColor: '#3b82f6', 
      color: 'white', 
      padding: '20px',
      textAlign: 'center',
      fontSize: '24px',
      fontWeight: 'bold'
    }}>
      测试页面 - 如果看到蓝色背景和白色文字，说明样式正常
    </div>
  );
};

export default TestPage;