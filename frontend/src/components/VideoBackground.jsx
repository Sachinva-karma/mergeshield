import React, { useEffect, useRef, useState } from 'react';

const LIGHT_VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260815_034306_165449ef-7d2e-4e81-850f-1939c5cb442d.mp4';
const DARK_VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260815_030633_1712fc71-4979-4e14-98f9-9f95702ab3da.mp4';

/**
 * Theme-aware background video layer.
 * Plays the light video when light theme is active,
 * and the dark video when dark theme is active.
 * Completely non-interactive, sits behind all content.
 */
export default function VideoBackground({ effectiveTheme }) {
  const videoRef = useRef(null);
  const [hasError, setHasError] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  // Track prefers-reduced-motion
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const videoSrc = effectiveTheme === 'dark' ? DARK_VIDEO_URL : LIGHT_VIDEO_URL;

  // Attempt seamless autoplay on video element mount / source update
  useEffect(() => {
    if (videoRef.current && !reducedMotion && !hasError) {
      const playPromise = videoRef.current.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          // Silent fallback if autoplay is restricted by browser policy
        });
      }
    }
  }, [videoSrc, reducedMotion, hasError]);

  return (
    <div
      className="video-bg-container"
      aria-hidden="true"
      role="presentation"
    >
      {!reducedMotion && !hasError && (
        <video
          key={videoSrc}
          ref={videoRef}
          className="video-bg-element"
          src={videoSrc}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          onError={() => setHasError(true)}
        />
      )}
      <div className={`video-bg-overlay theme-${effectiveTheme}`} />
    </div>
  );
}
