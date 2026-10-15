import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@mantine/core/styles.css'
import '@fontsource/commissioner/latin-400.css'
import '@fontsource/commissioner/latin-500.css'
import '@fontsource/commissioner/latin-600.css'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
