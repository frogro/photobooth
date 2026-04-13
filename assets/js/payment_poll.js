"use strict";

(function () {
  var pollTimer = null;
  var paymentStartTime = null;
  var lastOverlayEl = null;

  function getPaymentTimeoutMs() {
    try {
      if (typeof window !== 'undefined' &&
          window.config &&
          window.config.payments &&
          window.config.payments.timeout) {
        var seconds = parseInt(window.config.payments.timeout, 10);
        if (!isNaN(seconds) && seconds > 0) {
          return seconds * 1000;
        }
      }
    } catch (e) {
      console.log('Payment timeout config read failed:', e);
    }
    return 60000;
  }

  function getActiveOverlay() {
    var overlay = document.querySelector('.overlay');
    if (!overlay) return null;

    if (
      overlay.classList.contains('overlay-qr') ||
      overlay.classList.contains('overlay-both') ||
      overlay.classList.contains('overlay-coin')
    ) {
      return overlay;
    }

    return null;
  }

  function closePaymentOverlay() {
    var overlay = getActiveOverlay() || document.querySelector('.overlay');

    if (typeof window.photoboothTools !== 'undefined') {
      window.photoboothTools.isPrinting = false;
    }

    if (typeof window.photoboothTools !== 'undefined' &&
        window.photoboothTools.overlay &&
        typeof window.photoboothTools.overlay.close === 'function') {
      window.photoboothTools.overlay.close();
      return;
    }

    if (overlay) {
      overlay.remove();
    }
  }

  function showTimeoutMessageAndClose() {
    var overlay = getActiveOverlay() || document.querySelector('.overlay');
    if (!overlay) {
      closePaymentOverlay();
      return;
    }

    try {
      overlay.innerHTML = '<div style="text-align:center;">⏱️ Zahlung abgebrochen oder abgelaufen</div>';
    } catch (e) {
      console.log('Could not update overlay timeout message:', e);
    }

    setTimeout(function () {
      closePaymentOverlay();
    }, 1200);
  }

  function redirectToStart(message) {
    var overlay = getActiveOverlay() || document.querySelector('.overlay');
    if (!overlay) {
      if (typeof window.photoboothTools !== 'undefined') {
        window.photoboothTools.isPrinting = false;
      }
      setTimeout(function () {
        window.location.href = '/';
      }, 1200);
      return;
    }

    try {
      overlay.innerHTML = '<div style="text-align:center;">' + message + '</div>';
    } catch (e) {
      console.log('Could not update overlay message:', e);
    }

    if (typeof window.photoboothTools !== 'undefined') {
      window.photoboothTools.isPrinting = false;
    }

    setTimeout(function () {
      window.location.href = '/';
    }, 1200);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    paymentStartTime = null;
    lastOverlayEl = null;
  }

  function startPolling(overlayEl) {
    if (pollTimer && lastOverlayEl === overlayEl) {
      return;
    }

    stopPolling();
    paymentStartTime = Date.now();
    lastOverlayEl = overlayEl;

    pollTimer = setInterval(function () {
      var currentOverlay = getActiveOverlay();

      if (!currentOverlay) {
        stopPolling();
        return;
      }

      var timeoutMs = getPaymentTimeoutMs();
      if (paymentStartTime && Date.now() - paymentStartTime >= timeoutMs) {
        console.log('Payment timeout reached after ms:', timeoutMs);
        stopPolling();
        showTimeoutMessageAndClose();
        return;
      }

      $.ajax({
        url: '/api/paymentStatus.php',
        method: 'GET',
        dataType: 'json',
        success: function success(data) {
          console.log('Payment poll:', data);

          if (data.cancelled) {
            stopPolling();

            if (typeof window.photoboothTools !== 'undefined') {
              window.photoboothTools.isPrinting = false;
            }

            window.location.href = '/';
            return;
          }

          if (data.paid && data.printed) {
            stopPolling();

            if (typeof window.photoboothTools !== 'undefined') {
              window.photoboothTools.isPrinting = false;
            }

            var overlay = getActiveOverlay() || document.querySelector('.overlay');
            if (overlay) {
              overlay.innerHTML = '✅ Zahlung erfolgreich – Druck abgeschlossen';
            }
            redirectToStart('✅ Zahlung erfolgreich – Druck abgeschlossen');
          }
        },
        error: function error(xhr, status, err) {
          console.log('Payment poll failed:', status, err);
        }
      });
    }, 2000);
  }

  var observer = new MutationObserver(function () {
    var overlay = getActiveOverlay();

    if (!overlay) {
      if (pollTimer) {
        stopPolling();
      }
      return;
    }

    startPolling(overlay);
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
})();
