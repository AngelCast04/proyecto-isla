// Vercel: mismo origen (vacío). /api/query lo reescribe vercel.json hacia Render (sin CORS en el navegador).
// Local y Render también usan base vacía.
window.__API_BASE__ = '';
