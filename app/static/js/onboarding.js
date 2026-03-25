/* Onboarding Manager for Contrudesk (vanilla JS + Intro.js)
   - Shows a role-based tour on first login
   - Persists completion/skip in localStorage per user:role:version
   - Re-openable from a "Guía" button
*/
(function(){
  function log(){ /* console.log('[onb]', ...arguments); */ }

  function getUser(){ return (window.CurrentUser && window.CurrentUser.id && window.CurrentUser.role) ? window.CurrentUser : null; }
  function getRole(){ const u = getUser(); return u ? String(u.role).toLowerCase() : null; }
  function getConfig(){ return (window.OnboardingGuideConfig && window.OnboardingGuideConfig.roles) ? window.OnboardingGuideConfig : null; }
  function lsGet(key){ try { return JSON.parse(localStorage.getItem(key)); } catch(e){ return null; } }
  function lsSet(key, val){ try { localStorage.setItem(key, JSON.stringify(val)); } catch(e){} }
  function isVisible(el){ if(!el) return false; const style = window.getComputedStyle(el); if(style.display==='none' || style.visibility==='hidden' || style.opacity==='0') return false; const rect = el.getBoundingClientRect(); return !!(rect.width && rect.height); }

  function buildSteps(roleCfg){
    const steps = [];
    for (const step of (roleCfg.steps || [])){
      if (step.element){
        const el = document.querySelector(step.element);
        if (el && isVisible(el)) steps.push({ element: step.element, intro: step.intro });
      } else if (step.intro){
        steps.push({ intro: step.intro });
      }
    }
    return steps;
  }

  function storageKey(){
    const u = getUser();
    const cfg = getConfig();
    const version = (cfg && cfg.version) ? cfg.version : 1;
    return u ? `onb:${u.id}:${u.role}:${version}` : null;
  }

  function shouldShow(force){
    if (force) return true;
    const key = storageKey();
    if (!key) return false;
    const saved = lsGet(key);
    return !saved || (!saved.completed && !saved.skipped);
  }

  function mark(state){
    const key = storageKey();
    if (!key) return;
    const prev = lsGet(key) || {};
    const payload = Object.assign({}, prev, { [state]: true, at: new Date().toISOString() });
    lsSet(key, payload);
  }

  function start(force){
    const u = getUser();
    const cfg = getConfig();
    if (!u || !cfg || !window.introJs) { return; }
    if (!shouldShow(force)) { return; }

    const roleCfg = cfg.roles[getRole()];
    if (!roleCfg) { return; }

    // Build steps present in DOM
    const steps = buildSteps(roleCfg);
    if (!steps.length) { return; }

    const intro = window.introJs();
    intro.setOptions({
      steps,
      nextLabel: 'Siguiente',
      prevLabel: 'Atrás',
      doneLabel: 'Entendido',
      skipLabel: 'Saltar',
      showStepNumbers: false,
      showBullets: false,
      showProgress: true,
      exitOnOverlayClick: true,
      disableInteraction: false
    });

    intro.oncomplete(function(){ mark('completed'); });
    intro.onexit(function(){ mark('skipped'); });

    // Small delay so layout/nav are fully painted
    setTimeout(function(){ intro.start(); }, 100);
  }

  function setupHelpButtons(){
    const btn = document.getElementById('onbHelpBtn');
    if (btn) btn.addEventListener('click', function(){ start(true); });
    const btnm = document.getElementById('onbHelpBtnMobile');
    if (btnm) btnm.addEventListener('click', function(){ start(true); });
  }

  document.addEventListener('DOMContentLoaded', function(){
    setupHelpButtons();
    // Auto start only when authenticated and first time
    start(false);
  });

  // Expose for console/manual trigger
  window.OnboardingManager = { start };
})();
