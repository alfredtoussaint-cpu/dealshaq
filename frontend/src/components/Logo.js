import React from 'react';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_surplus-shop-1/artifacts/vgpaeu9m_youtube%20%20%20cover%20photo.jpg';

export default function Logo({ size = 'default', className = '' }) {
  const sizeClasses = {
    small: 'h-8',
    default: 'h-12',
    large: 'h-16',
    xlarge: 'h-20'
  };

  return (
    <img
      src={LOGO_URL}
      alt="DealShaq Logo"
      className={`${sizeClasses[size]} w-auto object-contain ${className}`}
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
      src={LOGO_URL}
      alt="DealShaq"
      className={`${sizeClasses[size]} object-contain ${className}`}
    />
  );
}
