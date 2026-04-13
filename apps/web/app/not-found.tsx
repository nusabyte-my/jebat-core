import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center relative overflow-hidden">
      <div className="relative z-10 text-center px-4 sm:px-6 lg:px-8">
        <div className="text-8xl md:text-9xl font-bold mb-4">
          <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">404</span>
        </div>
        <h2 className="text-2xl md:text-3xl font-bold mb-4">Page Not Found</h2>
        <p className="text-neutral-400 mb-8 max-w-md mx-auto">
          The page you're looking for might have been moved, deleted, or never existed.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 py-3 text-sm font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            Go Home
          </Link>
          <Link href="/status" className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
            Check Status
          </Link>
        </div>
      </div>
    </div>
  );
}
