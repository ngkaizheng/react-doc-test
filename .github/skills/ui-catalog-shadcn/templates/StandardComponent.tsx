import React from 'react';

/**
 * @component ComponentName
 * @description What this component does — keep concise, used in spec generation.
 * @example
 * <ComponentName prop1="value" />
 */
type ComponentNameProps = React.ComponentPropsWithRef<'div'> & {
  /** Short description of this prop */
  prop1: string;
  /** Optional prop — defaults to false */
  prop2?: boolean;
};

export function ComponentName({ 
  prop1, 
  prop2 = false, 
  children, 
  ref, // Passed seamlessly as a prop in React 19
  className = '',
  ...props 
}: ComponentNameProps) {
  return (
    <div 
      ref={ref} 
      className={`relative overflow-hidden ${className}`} 
      {...props}
    >
      {/* Animation content / Motion UI logic */}
      <span className={prop2 ? "animate-pulse" : ""}>{prop1}</span>
      {children}
    </div>
  );
}