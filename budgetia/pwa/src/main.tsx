import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

import { registerSW } from 'virtual:pwa-register'

// Register Service Worker
registerSW({
  onNeedRefresh() {
    // Show a toast or banner to refresh
    if (confirm("Nova versão disponível. Recarregar?")) {
        window.location.reload();
    }
  },
  onOfflineReady() {
    console.log("BudgetIA está pronto para uso offline!");
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
