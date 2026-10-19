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

  function initLedgerFilters() {
    var table = document.getElementById('tblLedger');
    var searchInput = document.getElementById('ledgerSearchInput');
    var statusSelect = document.getElementById('filterLedgerStatus');
    var studentSelect = document.getElementById('filterLedgerStudent');
    var counter = document.querySelector('[data-row-count="tblLedger"]');
    if (!table || !statusSelect || !studentSelect) return;

    function applyFilter() {
      var query = searchInput ? searchInput.value.trim().toLowerCase() : '';
      var status = statusSelect.value.trim().toUpperCase();
      var studentId = studentSelect.value.trim();
      var tbody = table.querySelector('tbody');
      if (!tbody) return;

      var rows = tbody.querySelectorAll('tr');
      var visible = 0;

      rows.forEach(function (row) {
        if (row.querySelector('td[colspan]')) return;
        var text = row.textContent.toLowerCase();
        var rowStatus = (row.getAttribute('data-status') || '').toUpperCase();
        var rowStudentId = (row.getAttribute('data-student-id') || '').trim();

        var matchesQuery = query === '' || text.indexOf(query) !== -1;
        var matchesStatus = status === '' || rowStatus === status;
        var matchesStudent = studentId === '' || rowStudentId === studentId;

        if (matchesQuery && matchesStatus && matchesStudent) {
          row.style.display = '';
          visible++;
        } else {
          row.style.display = 'none';
        }
      });

      if (counter) {
        counter.textContent = visible + ' record' + (visible === 1 ? '' : 's');
      }
    }

    if (searchInput) searchInput.addEventListener('input', applyFilter);
    statusSelect.addEventListener('change', applyFilter);
    studentSelect.addEventListener('change', applyFilter);
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPaymentModal();
    initLedgerFilters();
  });
})();
