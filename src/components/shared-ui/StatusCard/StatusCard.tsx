import React from 'react';

/**
 * @component StatusCard
 * @description 用于展示系统状态的专用卡片，支持高亮模式和状态点击回调。
 * @example
 * <StatusCard status="success" title="Upload Complete" onRetry={handleRetry} />
 * @example
 * <StatusCard status="error" title="Failed" isHighlighted={true} />
 */
interface StatusCardProps {
  status: 'success' | 'error' | 'warning';
  title: string;
  isHighlighted?: boolean;
  onRetry?: () => void;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  status,
  title,
  isHighlighted = false,
  onRetry,
}) => {
  const baseClass = `p-4 border rounded-lg ${isHighlighted ? 'border-2 border-blue-500' : 'border border-gray-200'}`;
  
  return (
    <div className={baseClass}>
      <h3 className="font-bold text-lg">{title}</h3>
      <p className="text-sm capitalize">Status: {status}</p>
      
      {status === 'error' && onRetry && (
        <button 
          onClick={onRetry}
          className="mt-2 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition"
        >
          Retry
        </button>
      )}
    </div>
  );
};