
import type { ReactNode } from 'react'

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex bg-paper">
      {/* Left — form */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 py-10">
        <div className="w-full max-w-md">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-full border-2 border-rust flex items-center justify-center">
              <span className="font-display font-bold text-lg text-rust">C</span>
            </div>
            <span className="font-display font-bold text-lg text-ink tracking-tight">Campus Board</span>
          </div>
          {children}
        </div>
      </div>

      {/* Right — noticeboard visual, hidden on small screens */}
      <div className="hidden lg:flex flex-1 bg-ink relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-noise" />
        {/* Scattered "pinned notes" */}
        <div className="relative w-full max-w-sm">
          <div className="pin-card rounded-2xl shadow-pin-hover p-5 rotate-[-3deg] -translate-x-6">
            <p className="stamp-label text-rust mb-1">Robotics Society</p>
            <p className="font-display font-semibold text-ink text-sm">Workshop: Intro to ROS2</p>
            <p className="text-xs text-ink/40 mt-1 font-mono">Sat · 11:00 AM · Lab 4</p>
          </div>
          <div className="pin-card rounded-2xl shadow-pin-hover p-5 rotate-[2deg] translate-x-10 -mt-6 ml-auto w-[85%]">
            <p className="stamp-label text-pine mb-1">Open to join</p>
            <p className="font-display font-semibold text-ink text-sm">Photography Club</p>
            <p className="text-xs text-ink/40 mt-1 font-mono">128 members</p>
          </div>
          <div className="pin-card rounded-2xl shadow-pin-hover p-5 rotate-[-1.5deg] mt-6 w-[80%]">
            <p className="stamp-label text-gold mb-1">Certificate ready</p>
            <p className="font-display font-semibold text-ink text-sm">Hackathon Finalist</p>
            <p className="text-xs text-ink/40 mt-1 font-mono">Verify with code · #A8F2…</p>
          </div>
        </div>

        <div className="absolute bottom-8 left-12 right-12 text-paper/40 text-sm">
          One board for every club, event, and announcement on campus.
        </div>
      </div>
    </div>
  )
}
