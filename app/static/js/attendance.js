/**
 * University Management System (UMS)
 * attendance.js — Faculty Attendance Marker & Live Percentage Preview
 * Zero dependencies, pure vanilla JavaScript.
 */

(function () {
  'use strict';

  function updateAttendancePreview() {
    var radios = document.querySelectorAll('input[type="radio"][name^="status_"]:not(:disabled)');
    var totalStudents = document.querySelectorAll('#attendanceTable tbody tr[data-course-ids]:not([hidden])').length;
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

  function isEnrolled(el, courseId) {
    return (el.getAttribute('data-course-ids') || '').split(',').indexOf(courseId) !== -1;
  }

  // Batch sheet: show only students enrolled in the selected course; hidden rows are
  // disabled so their radios are not submitted.
  function filterBatchSheet() {
    var courseSelect = document.getElementById('courseSelect');
    if (!courseSelect) return;
    document.querySelectorAll('#attendanceTable tbody tr[data-course-ids]').forEach(function (row) {
      var show = isEnrolled(row, courseSelect.value);
      row.hidden = !show;
      row.querySelectorAll('input').forEach(function (input) { input.disabled = !show; });
    });
    updateAttendancePreview();
  }

  // Individual entry: offer only students enrolled in the selected course.
  function filterIndividualStudents() {
    var courseSelect = document.getElementById('indCourseSelect');
    var studentSelect = document.getElementById('indStudentSelect');
    if (!courseSelect || !studentSelect) return;
    var firstVisible = null;
    Array.prototype.forEach.call(studentSelect.options, function (opt) {
      var show = isEnrolled(opt, courseSelect.value);
      opt.hidden = !show;
      opt.disabled = !show;
      if (show && !firstVisible) firstVisible = opt;
    });
    if (studentSelect.selectedOptions.length === 0 || studentSelect.selectedOptions[0].disabled) {
      studentSelect.value = firstVisible ? firstVisible.value : '';
    }
  }

  function initAttendanceActions() {
    var batchCourse = document.getElementById('courseSelect');
    var indCourse = document.getElementById('indCourseSelect');
    if (batchCourse) batchCourse.addEventListener('change', filterBatchSheet);
    if (indCourse) indCourse.addEventListener('change', filterIndividualStudents);
    filterIndividualStudents();

    var selectAllPresentBtn = document.getElementById('btnMarkAllPresent');
    var selectAllAbsentBtn = document.getElementById('btnMarkAllAbsent');

    if (selectAllPresentBtn) {
      selectAllPresentBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var presentRadios = document.querySelectorAll('#attendanceTable input[type="radio"][value="Present"]:not(:disabled)');
        presentRadios.forEach(function (r) {
          r.checked = true;
        });
        updateAttendancePreview();
      });
    }

    if (selectAllAbsentBtn) {
      selectAllAbsentBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var absentRadios = document.querySelectorAll('#attendanceTable input[type="radio"][value="Absent"]:not(:disabled)');
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

    // Run initial filtering and calculation
    filterBatchSheet();
    updateAttendancePreview();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initAttendanceActions();
  });
})();
