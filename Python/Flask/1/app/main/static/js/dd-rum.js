(function () {
  if (!window.DD_RUM) {
    console.warn('Datadog RUM SDK not loaded');
    return;
  }

  // Fetch config first, then init RUM with user context
  fetch('/api/config')
    .then(function (res) { return res.json(); })
    .then(function (cfg) {

      window.DD_RUM.onReady(function () {
        window.DD_RUM.init({
          applicationId: cfg.rumAppId,
          clientToken:   cfg.rumToken,
          site:                 'datadoghq.eu',
          service:              cfg.appName    || 'Dashboard',
          env:                  cfg.env        || 'PROD',
          version:              cfg.appVersion || '3.0.0',
          sessionSampleRate:    100,
          trackUserInteractions: true,
          trackResources:       true,
          trackLongTasks:       true,
          defaultPrivacyLevel:  'mask-user-input',
        });

        // Set user if authenticated
        if (cfg.userId) {
          window.DD_RUM.setUser({
            id:    cfg.userId,
            email: cfg.userEmail,
            name:  cfg.userRole,
          });
        }

        // Idle session handling
        let idleTimer;
        const IDLE_TIMEOUT = 5 * 60 * 1000;

        function endIdleSession() {
          window.DD_RUM.clearUser();
          window.DD_RUM.stopSession();
        }

        function resetIdleTimer() {
          clearTimeout(idleTimer);
          idleTimer = setTimeout(endIdleSession, IDLE_TIMEOUT);
        }

        ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(function (evt) {
          document.addEventListener(evt, resetIdleTimer, { passive: true });
        });

        document.addEventListener('visibilitychange', function () {
          if (document.visibilityState === 'hidden') {
            window.DD_RUM.addAction('tab_hidden', { path: location.pathname });
          }
        });

        resetIdleTimer();
      }); // end onReady

    })
    .catch(function (err) {
      console.error('Failed to load app config:', err);
    });

})();
