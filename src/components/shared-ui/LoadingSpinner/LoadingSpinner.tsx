import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  tip?: string;
}

export const LoadingSpinner: React.FC<SpinnerProps> = ({ 
  size = 'md', 
  tip 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 space-y-2">
      <div 
        className={`${sizeClasses[size]} border-blue-600 border-t-transparent rounded-full animate-spin`} 
      />
      {tip && <p className="text-xs text-gray-400 font-medium">{tip}</p>}
    </div>
  );
};