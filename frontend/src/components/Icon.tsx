// Small inline icon set (stroke icons, 24x24) so the app needs no icon library.
const PATHS: Record<string, string> = {
  upload: 'M12 16V4m0 0l-4 4m4-4l4 4M4 20h16',
  gauge: 'M12 14l4-4M3.5 17a9 9 0 1117 0',
  radar: 'M12 3l8 5.5-3 9.5H7L4 8.5 12 3zm0 4l4 3-1.5 5h-5L8 10l4-3z',
  sliders: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0M14 4v4M8 10v4M16 16v4',
  file: 'M14 3H6a1 1 0 00-1 1v16a1 1 0 001 1h12a1 1 0 001-1V8l-5-5zm0 0v5h5M8 13h8M8 17h5',
  map: 'M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2zm0 0v14m6-12v14',
  edit: 'M4 20h4L19 9l-4-4L4 16v4zm9-13l4 4',
  check: 'M4 12l5 5L20 6',
  shield: 'M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3zm-3 9l2 2 4-4',
  chat: 'M4 5h16v11H8l-4 4V5zm4 5h8M8 13h5',
  bookmark: 'M6 3h12v18l-6-4-6 4V3z',
  sun: 'M12 4V2m0 20v-2m8-8h2M2 12h2m13.7-5.7l1.4-1.4M4.9 19.1l1.4-1.4m11.4 1.4l1.4 1.4M4.9 4.9l1.4 1.4M12 17a5 5 0 100-10 5 5 0 000 10z',
  moon: 'M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z',
  monitor: 'M3 4h18v12H3V4zm6 16h6m-3-4v4',
  download: 'M12 4v12m0 0l-4-4m4 4l4-4M4 20h16',
  copy: 'M9 9h11v11H9V9zm-5 6V4h11',
  sparkles: 'M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8L12 3zm7 12l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z',
  target: 'M12 21a9 9 0 100-18 9 9 0 000 18zm0-4a5 5 0 100-10 5 5 0 000 10zm0-4a1 1 0 100-2 1 1 0 000 2z',
  alert: 'M12 9v4m0 4h.01M10.3 3.9L2.4 18a2 2 0 001.7 3h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
  github: 'M9 19c-4 1.5-4-2-6-2.5m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 00-1.3-3.2 4.3 4.3 0 00-.1-3.2s-1-.3-3.4 1.3a11.8 11.8 0 00-6 0C6.8 2.3 5.8 2.6 5.8 2.6a4.3 4.3 0 00-.1 3.2A4.6 4.6 0 004.4 9c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V22',
  menu: 'M4 6h16M4 12h16M4 18h16',
  refresh: 'M4 4v6h6M20 20v-6h-6M5.6 15a7 7 0 0012 2.4L20 14M18.4 9A7 7 0 006.4 6.6L4 10',
}

export type IconName = keyof typeof PATHS

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  )
}
