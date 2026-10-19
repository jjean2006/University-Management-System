/**
 * University Management System (UMS)
 * payments.js — Accounts Payment Recording Modal & Form Validation
 * Zero dependencies, pure vanilla JavaScript.
 */

(function () {
  'use strict';

  function initPaymentModal() {
    var modal = document.getElementById('paymentModal');
    if (!modal) return;

    var openButtons = document.querySelectorAll('[data-record-payment]');
    var closeButtons = modal.querySelectorAll('[data-close-modal]');
    var invoiceInput = document.getElementById('modalInvoiceNo');
    var amountInput = document.getElementById('modalAmountPaid');
    var balanceDisplay = document.getElementById('modalBalanceDue');
    var paymentForm = document.getElementById('recordPaymentForm');

    openButtons.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var invoiceNo = btn.getAttribute('data-invoice-no') || '';
        var balanceDue = btn.getAttribute('data-balance-due') || '';

        if (invoiceInput) invoiceInput.value = invoiceNo;
        if (amountInput) amountInput.value = balanceDue ? parseFloat(balanceDue).toFixed(2) : '';
        if (balanceDisplay) balanceDisplay.textContent = balanceDue ? '₹' + parseFloat(balanceDue).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '-';

        modal.classList.add('active');
        if (amountInput) amountInput.focus();
      });
    });

    closeButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        modal.classList.remove('active');
      });
    });

    // Close on overlay backdrop click
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });

    // Client-side validation before submission
    if (paymentForm) {
      paymentForm.addEventListener('submit', function (e) {
        var val = parseFloat(amountInput.value);
        if (isNaN(val) || val <= 0) {
          e.preventDefault();
          alert('Please enter a valid positive payment amount.');
          amountInput.focus();
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPaymentModal();
  });
})();
