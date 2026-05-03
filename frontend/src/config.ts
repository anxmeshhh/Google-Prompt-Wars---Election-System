// Smart API URL routing:
// - localhost:5173 (dev) → localhost:5000 (Flask dev server)
// - GCE VM (34.41.130.216) → '' (Nginx same-origin proxy)
// - Firebase Hosting (HTTPS) → GCE backend via sslip.io
const GCE_API = 'https://34-41-130-216.sslip.io'

export const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (!import.meta.env.PROD) return 'http://localhost:5000'
  const host = window.location.hostname
  if (host === 'electaverse.web.app' || host === 'electaverse.firebaseapp.com') return GCE_API
  if (host.endsWith('.sslip.io')) return ''  // Same-origin on VM
  if (host.endsWith('.trycloudflare.com')) return ''  // Already on tunnel
  return ''  // GCE same-origin
}

export const API = getApiUrl()
