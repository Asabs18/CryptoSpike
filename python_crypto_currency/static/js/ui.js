// ui.js - UI helper functions

// 📋 Copy to clipboard
function copyText (id) {
  const el = document.getElementById(id)
  navigator.clipboard.writeText(el.textContent.trim())
}

// 🔔 Show auto-disappearing alert
function showAlert (message, type = 'success', duration = 4000) {
  const alertBox = document.getElementById('globalAlert')
  alertBox.textContent = message
  alertBox.className = `alert alert-${type} text-center position-fixed w-100 top-0 start-0 rounded-0`
  alertBox.classList.remove('d-none')
  setTimeout(() => alertBox.classList.add('d-none'), duration)
}

// ⏳ Toggle loading spinner on a button
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
