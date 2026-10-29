import React, { useId } from 'react';

/**
 * GapX mark: an "X" whose rising stroke is an arrow bridging the gap in the other stroke,
 * i.e. closing the skill gap and moving up.
 */
export default function GapXLogo({ size = 32, className = '', animated = false }: { size?: number; className?: string; animated?: boolean }) {
  const id = useId().replace(/:/g, '');
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="GapX AI"
    >
      <defs>
        <linearGradient id={`gx-bg-${id}`} x1="4" y1="36" x2="36" y2="4" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4f46e5" />
          <stop offset="0.55" stopColor="#7c3aed" />
          <stop offset="1" stopColor="#c026d3" />
        </linearGradient>
        <linearGradient id={`gx-shine-${id}`} x1="20" y1="0" x2="20" y2="22" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" stopOpacity="0.28" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="38" height="38" rx="11" fill={`url(#gx-bg-${id})`} />
      <rect x="1" y="1" width="38" height="20" rx="11" fill={`url(#gx-shine-${id})`} />
      {/* broken stroke: the gap */}
      <path d="M11.5 11.5 L16.2 16.2" stroke="#ffffff" strokeOpacity="0.78" strokeWidth="3.4" strokeLinecap="round" />
      <path d="M23.8 23.8 L28.5 28.5" stroke="#ffffff" strokeOpacity="0.78" strokeWidth="3.4" strokeLinecap="round" />
      {/* rising arrow bridging the gap */}
      <path d="M11.5 28.5 L27.6 12.4" stroke="#ffffff" strokeWidth="3.4" strokeLinecap="round">
        {animated && <animate attributeName="stroke-dasharray" values="0 30;23 30;23 30" dur="1.6s" repeatCount="indefinite" />}
      </path>
      <path d="M19.4 11.6 H28.4 V20.6" stroke="#ffffff" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
