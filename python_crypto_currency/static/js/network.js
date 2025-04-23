/**
 * network.js - Peer management and network synchronization
 *
 * Handles:
 * - Adding peers to the local node
 * - Syncing mempools and blockchains across peers
 * - Displaying current peers in the UI
 * - Periodic syncing loop
 */

/**
 * 🌐 Load the list of connected peers and display them in the UI.
 */
async function loadPeers () {
  const res = await fetch('/peers')
  const json = await res.json()
  const list = document.getElementById('peerList')
  list.innerHTML = ''

  json.peers.forEach(peer => {
    const li = document.createElement('li')
    li.textContent = peer
    list.appendChild(li)
  })
}

/**
 * ➕ Setup the peer connection form to allow users to add new peers.
 */
function setupPeerForm () {
  document.getElementById('peerForm').addEventListener('submit', async e => {
    e.preventDefault()
    const input = document.getElementById('newPeer').value.trim()
    if (!input) {
      showAlert('⚠️ Please enter a peer port or URL.', 'warning')
      return
    }

    const peerUrl = input.startsWith('http')
      ? input
      : `http://localhost:${input}`

    try {
      const res = await fetch('/peers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer: peerUrl })
      })

      const json = await res.json()

      if (!res.ok) {
        showAlert(json.error || '❌ Failed to add peer', 'danger')
      } else {
        showAlert(json.message || '✅ Peer added!', 'success')
        document.getElementById('newPeer').value = ''
        loadPeers()
      }
    } catch (err) {
      showAlert('❌ Failed to reach server', 'danger')
    }
  })
}

/**
 * 🔄 Sync the mempool with all known peers by merging their pending transactions.
 */
async function syncMempool () {
  setSyncing(true)

  const peersRes = await fetch('/peers')
  const { peers } = await peersRes.json()

  for (const peer of peers) {
    try {
      const res = await fetch(`${peer}/mempool`)
      const peerTxs = await res.json()

      await fetch('/mempool/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(peerTxs)
      })
    } catch (err) {
      console.warn('Failed to sync mempool with', peer)
    }
  }

  setSyncing(false)
}

/**
 * 🔁 Periodic synchronization loop.
 * Syncs the chain, mempool, and updates the UI every few seconds.
 */
async function periodicSync () {
  if (!wallet) return // Skip syncing if wallet not loaded

  const peersRes = await fetch('/peers')
  const { peers } = await peersRes.json()
  if (peers.length === 0) return // Skip spinner if no peers

  setSyncing(true)

  try {
    await fetch('/resolve')
    await fetchChain()
    await syncMempool()
    await renderMempool()
    await loadPeers()
  } catch (err) {
    console.warn('Periodic sync error:', err)
  }

  setSyncing(false)
}

/**
 * 🕒 Start the periodic sync interval to run every 5 seconds.
 */
function startSyncInterval () {
  setInterval(periodicSync, 5000)
}
