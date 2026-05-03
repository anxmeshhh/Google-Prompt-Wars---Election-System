// Smart API URL routing:
// - localhost:5173 (dev) → localhost:5000 (Flask dev server)
// - GCE VM (34.41.130.216) → '' (Nginx same-origin proxy)
// - Firebase Hosting (HTTPS) → Cloudflared tunnel to GCE backend
const GCE_TUNNEL = 'https://half-itself-yard-prison.trycloudflare.com'

export const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (!import.meta.env.PROD) return 'http://localhost:5000'
  const host = window.location.hostname
  if (host === 'electaverse.web.app' || host === 'electaverse.firebaseapp.com') return GCE_TUNNEL
  if (host.endsWith('.trycloudflare.com')) return ''  // Already on tunnel
  return ''  // GCE same-origin
}

export const API = getApiUrl()
