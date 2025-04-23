// app.js - Main application initialization

// Display current node port
function showNodeInfo () {
  const port = window.location.port
  document.getElementById('nodePort').textContent = port
}

// Initialize all event listeners
function setupEventListeners () {
  setupTransactionForm()
  setupMiningButton()
  setupPeerForm()
}

// Main initialization function
async function initApp () {
  showNodeInfo()
  setupEventListeners()
  initializeWallet()

  // Initial data loading
  await fetchChain()
  await loadPeers()
  await renderMempool()

  // Start sync interval
  startSyncInterval()
}

// Start the application when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp)
