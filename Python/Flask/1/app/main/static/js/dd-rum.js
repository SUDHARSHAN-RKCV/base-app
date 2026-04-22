(function () {
  if (!window.DD_RUM) {
    console.warn('Datadog RUM SDK not loaded');
    return;
  }

  /* ========================
     RUM INITIALIZATION
     ======================== */
  window.DD_RUM.onReady(function () {

    window.DD_RUM.init({
      applicationId: 'app-id', /*from datadog*/
      clientToken: 'token', /*from datadog*/
      site: 'datadoghq.eu',
      service: 'app name',
      env: 'PROD',
      version: '1.0.0',
      sessionSampleRate: 100,
      trackUserInteractions: true,
      trackResources: true,
      trackLongTasks: true,
      defaultPrivacyLevel: 'mask-user-input',
    });

    /* ========================
       USER CONTEXT
       Set via window.APP_USER exposed in base.html
       ======================== */
    if (window.APP_USER && window.APP_USER.id) {
      window.DD_RUM.setUser({
        id: window.APP_USER.id, 
      });
    }

    /* ========================
       IDLE SESSION HANDLING
       ======================== */
    let idleTimer;
    const IDLE_TIMEOUT = 5 * 60 * 1000; // 5 min

    function endIdleSession() {
      console.log('Datadog RUM: idle timeout, stopping session');

      window.DD_RUM.clearUser();
      window.DD_RUM.stopSession();
    }

    function resetIdleTimer() {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(endIdleSession, IDLE_TIMEOUT);
    }

    ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(function (eventName) {
      document.addEventListener(eventName, resetIdleTimer, { passive: true });
    });

    /* ========================
       VISIBILITY TRACKING
       ======================== */
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') {
        window.DD_RUM.addAction('tab_hidden', { path: location.pathname });
      }
    });

    resetIdleTimer();

  });

})();
