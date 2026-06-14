import React from 'react';

export interface ZhengKaiMagicBoxProps {
  magicSecret: string;
  onExplode?: (power: number) => void;
  isEnchanted: boolean;
}

export const ZhengKaiMagicBox: React.FC<ZhengKaiMagicBoxProps> = ({
  magicSecret,
  onExplode,
  isEnchanted
}) => {
  return (
    <div className="p-4 border-2 border-purple-500 rounded bg-black text-white">
      <h3>✨ Magic Box: {magicSecret}</h3>
      {isEnchanted && <p>🔮 This box is enchanted!</p>}
      <button onClick={() => onExplode?.(999)} className="mt-2 p-1 bg-red-600 rounded">
        Trigger Explode
      </button>
    </div>
  );
};