/**
 * University Management System (UMS)
 * main.js — Shell Utilities, Flash Dismissal, and Navigation Highlighting
 * Zero npm dependencies, pure vanilla JavaScript.
 */

(function () {
  'use strict';

  // Flash Message Handling (Auto-dismiss after 5s or close button click)
  function initFlashMessages() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
      // Close button handler
      var closeBtn = alert.querySelector('.alert-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function () {
          alert.style.opacity = '0';
          setTimeout(function () {
            if (alert.parentNode) {
              alert.parentNode.removeChild(alert);
            }
          }, 150);
        });
      }

      // Auto-dismiss timeout (5 seconds)
      setTimeout(function () {
        if (alert && alert.parentNode) {
          alert.style.opacity = '0';
          setTimeout(function () {
            if (alert.parentNode) {
              alert.parentNode.removeChild(alert);
            }
          }, 150);
        }
      }, 5000);
    });
  }

  // Navigation Active Link Highlighting
  function initNavHighlights() {
    var path = window.location.pathname;
    var navLinks = document.querySelectorAll('.nav-tab, .subnav-bar a');
    navLinks.forEach(function (link) {
      var href = link.getAttribute('href');
      if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
        link.classList.add('active');
      }
    });
  }

  // Initialize on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () {
    initFlashMessages();
    initNavHighlights();
  });
})();
