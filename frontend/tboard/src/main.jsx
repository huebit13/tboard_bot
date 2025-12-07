// frontend/tboard/src/main.jsx
import { Buffer } from 'buffer';
window.Buffer = Buffer;
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { TonConnectProvider } from './TonConnectProvider.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <TonConnectProvider>
      <App />
    </TonConnectProvider>
  </StrictMode>,
)