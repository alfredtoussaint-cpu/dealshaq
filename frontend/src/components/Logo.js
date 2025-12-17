import React from 'react';

// Full logo image (with text) - Icon Left version
const LOGO_FULL_URL = '/dealshaq-logo.png';

// Icon only (no text)
const LOGO_ICON_URL = '/dealshaq-icon.png';

export default function Logo({ size = 'default', className = '' }) {
  const sizeClasses = {
    small: 'h-10',
    default: 'h-16',
    large: 'h-24',
    xlarge: 'h-32'
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
