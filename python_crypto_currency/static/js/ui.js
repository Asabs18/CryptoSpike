/**
 * ui.js - UI helper functions for the blockchain wallet interface.
 *
 * Provides utilities for:
 * - Clipboard copying
 * - Alert banners
 * - Loading spinner toggles
 * - Sync status feedback
 */

/**
 * 📋 Copy the text content of an element to the clipboard.
 *
 * @param {string} id - The ID of the element whose text will be copied.
 */
function copyText (id) {
  const el = document.getElementById(id)
  navigator.clipboard.writeText(el.textContent.trim())
}

/**
 * 🔔 Show an auto-disappearing alert message at the top of the screen.
 *
 * @param {string} message - The message to display.
 * @param {string} [type='success'] - The Bootstrap alert type (e.g., 'success', 'danger').
 * @param {number} [duration=4000] - Duration in milliseconds before the alert disappears.
 */
function showAlert (message, type = 'success', duration = 4000) {
  const alertBox = document.getElementById('globalAlert')
  alertBox.textContent = message
  alertBox.className = `alert alert-${type} text-center position-fixed w-100 top-0 start-0 rounded-0`
  alertBox.classList.remove('d-none')
  setTimeout(() => alertBox.classList.add('d-none'), duration)
}

/**
 * ⏳ Toggle a loading spinner and disable/enable the button.
 *
 * @param {HTMLElement} button - The button element to toggle loading state on.
 * @param {boolean} isLoading - Whether to show the loading state.
 */
function setLoading (button, isLoading) {
  if (isLoading) {
    button.disabled = true
    button.dataset.originalText = button.innerHTML
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> ${button.textContent.trim()}`
  } else {
    button.disabled = false
    if (button.dataset.originalText) {
      button.innerHTML = button.dataset.originalText
    }
  }
}

/**
 * 🔄 Toggle the syncing indicator based on peer availability.
 *
 * @param {boolean} isSyncing - Whether syncing is currently happening.
 */
async function setSyncing (isSyncing) {
  const spinner = document.getElementById('syncSpinner')
  if (!spinner) return

  try {
    const res = await fetch('/peers')
    const { peers } = await res.json()
    const hasPeers = peers && peers.length > 0
    spinner.classList.toggle('d-none', !isSyncing || !hasPeers)
  } catch {
    spinner.classList.add('d-none')
  }
}
