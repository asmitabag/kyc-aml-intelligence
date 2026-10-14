export default function CameraView({ camera, mirrored = false, guide = null, children }) {
  return (
    <div className="relative aspect-video overflow-hidden rounded-xl bg-slate-900">
      <video
        ref={camera.videoRef}
        playsInline
        muted
        className={`h-full w-full object-cover ${mirrored ? '-scale-x-100' : ''}`}
      />
      {guide}
      {children}
      {!camera.ready && (
        <div className="absolute inset-0 grid place-items-center px-6 text-center text-sm text-slate-300">
          {camera.error || 'Starting camera…'}
        </div>
      )}
    </div>
  );
}
