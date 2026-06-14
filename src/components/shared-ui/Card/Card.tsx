import React from 'react';

interface CardProps {
  title?: string;
  isHoverable?: boolean;
  children: React.ReactNode;
  extra?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ 
  title, 
  isHoverable = false, 
  children, 
  extra 
}) => {
  const hoverClass = isHoverable 
    ? 'hover:shadow-lg transition-shadow duration-200' 
    : '';

  return (
    <div className={`p-4 bg-white rounded-xl border border-gray-100 shadow-sm ${hoverClass}`}>
      {(title || extra) && (
        <div className="flex justify-between items-center mb-4 pb-2 border-b border-gray-50">
          {title && <h3 className="text-base font-semibold text-gray-800">{title}</h3>}
          {extra && <div className="text-sm text-gray-500">{extra}</div>}
        </div>
      )}
      <div className="text-sm text-gray-600">
        {children}
      </div>
    </div>
  );
};