export function Logo() {
  return (
    <span className="inline-flex items-center gap-2 font-bold">
      <svg viewBox="0 0 64 64" className="size-7" aria-hidden="true">
        <defs>
          <linearGradient id="logo-g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7c3aed" />
            <stop offset="1" stopColor="#c026d3" />
          </linearGradient>
        </defs>
        <rect width="64" height="64" rx="15" fill="url(#logo-g)" />
        <path d="M32 33 15 17M32 33 49 17M32 33v19" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" fill="none" opacity=".9" />
        <g fill="#fff">
          <circle cx="32" cy="33" r="8" />
          <circle cx="15" cy="17" r="5" />
          <circle cx="49" cy="17" r="5" />
          <circle cx="32" cy="52" r="5" />
        </g>
      </svg>
      <span dir="ltr">Agentic AI</span>
    </span>
  );
}
