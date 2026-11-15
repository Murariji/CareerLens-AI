/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Public URL of the FastAPI backend, e.g. https://careerlens-api.onrender.com */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
