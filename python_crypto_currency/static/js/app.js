/**
 * app.js - Main application initialization
 *
 * This script initializes the UI and blockchain functions on page load.
 * It sets up event listeners, loads initial data, starts syncing,
 * and displays local node information.
 */

/**
 * 🖥️ Display the current node's port number in the UI.
 */
function showNodeInfo () {
  const port = window.location.port
  document.getElementById('nodePort').textContent = port
}

/**
 * 🎛️ Set up all UI-related event listeners.
 * Includes form submission, button clicks, and peer management.
 */
function setupEventListeners () {
  setupTransactionForm()
  setupMiningButton()
  setupPeerForm()
}

/**
 * 🚀 Main application initializer.
 * Loads data, initializes wallet, displays UI, and starts periodic sync.
 */
async function initApp () {
  showNodeInfo()
  setupEventListeners()
  initializeWallet()

  // Load initial state
  await fetchChain()
  await loadPeers()
  await renderMempool()

  // Start periodic sync
  startSyncInterval()
}

/**
 * ⏱️ Run the app once the DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', initApp)
