// Lightweight analytics tracker (privacy-first, no external services)
export function trackPageView(path: string) {
  if (typeof window === 'undefined') return;
  // Log page views to console (replace with actual analytics service)
  console.log(`[Analytics] Page view: ${path} at ${new Date().toISOString()}`);
}

export function trackEvent(event: string, data?: Record<string, any>) {
  if (typeof window === 'undefined') return;
  console.log(`[Analytics] Event: ${event}`, data);
}
