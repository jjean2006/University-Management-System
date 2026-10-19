/**
 * University Management System (UMS)
 * attendance.js — Faculty Attendance Marker & Live Percentage Preview
 * Zero dependencies, pure vanilla JavaScript.
 */

(function () {
  'use strict';

  function updateAttendancePreview() {
    var radios = document.querySelectorAll('input[type="radio"][name^="status_"]');
    if (!radios.length) return;

    var totalStudents = document.querySelectorAll('#attendanceTable tbody tr').length;
    var presentCount = 0;
    var absentCount = 0;

    radios.forEach(function (radio) {
      if (radio.checked) {
        if (radio.value === 'Present') {
          presentCount++;
        } else if (radio.value === 'Absent') {
          absentCount++;
        }
      }
    });

    var evaluatedCount = presentCount + absentCount;
    var pct = evaluatedCount > 0 ? ((presentCount / evaluatedCount) * 100).toFixed(1) : '0.0';

    var countBadge = document.getElementById('attendanceLiveCount');
    var pctBadge = document.getElementById('attendanceLivePct');

    if (countBadge) {
      countBadge.textContent = presentCount + ' / ' + totalStudents + ' Present';
    }
    if (pctBadge) {
      pctBadge.textContent = pct + '%';
      if (parseFloat(pct) < 75.0) {
        pctBadge.className = 'badge badge-danger';
      } else {
        pctBadge.className = 'badge badge-success';
      }
    }
  }

  function initAttendanceActions() {
    var selectAllPresentBtn = document.getElementById('btnMarkAllPresent');
    var selectAllAbsentBtn = document.getElementById('btnMarkAllAbsent');

    if (selectAllPresentBtn) {
      selectAllPresentBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
        presentRadios.forEach(function (r) {
          r.checked = true;
        });
        updateAttendancePreview();
      });
    }

    if (selectAllAbsentBtn) {
      selectAllAbsentBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var absentRadios = document.querySelectorAll('input[type="radio"][value="Absent"]');
        absentRadios.forEach(function (r) {
          r.checked = true;
        });
        updateAttendancePreview();
      });
    }

    // Attach change listener to all status radio buttons
    var radios = document.querySelectorAll('input[type="radio"][name^="status_"]');
    radios.forEach(function (radio) {
      radio.addEventListener('change', updateAttendancePreview);
    });

    // Run initial calculation
    updateAttendancePreview();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initAttendanceActions();
  });
})();
