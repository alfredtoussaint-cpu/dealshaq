import React from 'react';

// Full logo image (with text)
const LOGO_FULL_URL = 'https://customer-assets.emergentagent.com/job_surplus-shop-1/artifacts/5xxg0k5q_image.png';

// Icon only (no text)
const LOGO_ICON_URL = 'https://customer-assets.emergentagent.com/job_surplus-shop-1/artifacts/has3vx4v_icon%20png.png';

export default function Logo({ size = 'default', className = '' }) {
  const sizeClasses = {
    small: 'h-8',
    default: 'h-12',
    large: 'h-16',
    xlarge: 'h-20'
  };

  return (
    <img
      src={LOGO_FULL_URL}
      alt="DealShaq Logo"
      className={`${sizeClasses[size]} w-auto object-contain ${className}`}
      onError={(e) => {
        console.error('Logo failed to load:', e);
        e.target.style.display = 'none';
      }}
    />
  );
}

export function LogoIcon({ size = 'default', className = '' }) {
  const sizeClasses = {
    small: 'h-6 w-6',
    default: 'h-8 w-8',
    large: 'h-10 w-10'
  };

  return (
    <img
      src={LOGO_ICON_URL}
      alt="DealShaq"
      className={`${sizeClasses[size]} object-contain rounded ${className}`}
      onError={(e) => {
        console.error('Logo icon failed to load:', e);
        e.target.style.display = 'none';
      }}
    />
  );
}
