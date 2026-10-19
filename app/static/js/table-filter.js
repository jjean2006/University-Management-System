/**
 * University Management System (UMS)
 * table-filter.js — Instant Client-Side Table Search Filter & Column Sorter
 * Zero dependencies, high performance.
 */

(function () {
  'use strict';

  function initTableFilters() {
    var filterInputs = document.querySelectorAll('[data-table-filter]');
    filterInputs.forEach(function (input) {
      var targetId = input.getAttribute('data-table-filter');
      var table = document.getElementById(targetId);
      if (!table) return;

      var counter = document.querySelector('[data-row-count="' + targetId + '"]');

      input.addEventListener('input', function () {
        var query = input.value.trim().toLowerCase();
        var tbody = table.querySelector('tbody');
        if (!tbody) return;

        var rows = tbody.querySelectorAll('tr');
        var visibleCount = 0;

        rows.forEach(function (row) {
          // If empty placeholder row, skip
          if (row.querySelector('td[colspan]')) return;

          var text = row.textContent.toLowerCase();
          if (query === '' || text.indexOf(query) !== -1) {
            row.style.display = '';
            visibleCount++;
          } else {
            row.style.display = 'none';
          }
        });

        if (counter) {
          counter.textContent = visibleCount + ' record' + (visibleCount === 1 ? '' : 's');
        }
      });
    });
  }

  function initTableSorting() {
    var sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(function (th) {
      th.classList.add('sortable');
      var icon = document.createElement('span');
      icon.className = 'sort-icon';
      icon.textContent = ' ⇅';
      th.appendChild(icon);

      th.addEventListener('click', function () {
        var table = th.closest('table');
        if (!table) return;
        var tbody = table.querySelector('tbody');
        if (!tbody) return;

        var colIndex = Array.prototype.indexOf.call(th.parentNode.children, th);
        var isAsc = th.getAttribute('data-sort-order') !== 'asc';
        th.setAttribute('data-sort-order', isAsc ? 'asc' : 'desc');

        // Reset all other headers in same thead
        var siblings = th.parentNode.querySelectorAll('th[data-sortable]');
        siblings.forEach(function (s) {
          if (s !== th) {
            s.removeAttribute('data-sort-order');
            var sIcon = s.querySelector('.sort-icon');
            if (sIcon) sIcon.textContent = ' ⇅';
          }
        });

        icon.textContent = isAsc ? ' ▲' : ' ▼';

        var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
        // Filter out empty rows
        var dataRows = rows.filter(function (r) {
          return !r.querySelector('td[colspan]');
        });

        dataRows.sort(function (a, b) {
          var aCell = a.children[colIndex] ? a.children[colIndex].textContent.trim() : '';
          var bCell = b.children[colIndex] ? b.children[colIndex].textContent.trim() : '';

          // Clean currency symbols and percentages for numeric comparison
          var aNum = parseFloat(aCell.replace(/[₹$%, ]/g, ''));
          var bNum = parseFloat(bCell.replace(/[₹$%, ]/g, ''));

          if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? aNum - bNum : bNum - aNum;
          }

          return isAsc
            ? aCell.localeCompare(bCell, undefined, { numeric: true, sensitivity: 'base' })
            : bCell.localeCompare(aCell, undefined, { numeric: true, sensitivity: 'base' });
        });

        // Re-append sorted rows to tbody
        dataRows.forEach(function (row) {
          tbody.appendChild(row);
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTableFilters();
    initTableSorting();
  });
})();
