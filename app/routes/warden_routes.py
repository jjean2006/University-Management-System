import os
import sys

_venv_site = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "venv", "lib", "python3.12", "site-packages")
)
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

from flask import Blueprint, render_template, render_template_string
from jinja2 import TemplateNotFound

from app.auth import ROLE_WARDEN, role_required
from app.db import execute_query
from app.routes.common import COMMON_STYLES

warden_bp = Blueprint("warden", __name__, url_prefix="/warden")

WARDEN_DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hostel Warden Dashboard — University Management System</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>{COMMON_STYLES}</style>
</head>
<body>
  <header>
    <div>
      <h1>Hostel Administration & Resident Directory</h1>
      <div class="user-meta">Chief Hostel Warden | Block Capacities & Bed Occupancy Matrix</div>
    </div>
    <div>
      <a href="/logout" class="logout-link">Sign Out</a>
    </div>
  </header>

  <div class="card">
    <h2>Hostel Block Capacities</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Block ID</th><th>Block Name</th><th>Gender Type</th><th>Total Capacity</th></tr></thead>
        <tbody>
          {{% for b in blocks %}}
          <tr>
            <td class="mono">{{{{ b.block_id }}}}</td>
            <td>{{{{ b.block_name }}}}</td>
            <td class="mono">{{{{ 'Male (Men)' if b.gender_type == 'M' else 'Female (Ladies)' }}}}</td>
            <td class="mono">{{{{ b.total_capacity }}}} Beds</td>
          </tr>
          {{% else %}}
          <tr><td colspan="4">No hostel blocks found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Room Occupancy Matrix</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Block Name</th><th>Room Number</th><th>Floor</th><th>Capacity</th><th>Occupied Beds</th><th>Vacant Beds</th><th>Monthly Rent (₹)</th></tr></thead>
        <tbody>
          {{% for r in rooms %}}
          <tr>
            <td>{{{{ r.block_name }}}}</td>
            <td class="mono">{{{{ r.room_number }}}}</td>
            <td class="mono">{{{{ r.floor_number }}}}</td>
            <td class="mono">{{{{ r.capacity }}}}</td>
            <td class="mono">{{{{ r.occupied_beds }}}}</td>
            <td class="mono">
              <span class="badge {{{{ 'badge-danger' if r.vacant_beds == 0 else 'badge-success' }}}}">
                {{{{ r.vacant_beds }}}}
              </span>
            </td>
            <td class="mono">₹{{{{ r.monthly_rent }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="7">No room occupancy data found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Hostel Resident Roster (Residential Students)</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Reg No</th><th>Resident Name</th><th>Gender</th><th>Block</th><th>Room Number</th><th>Degree Programme</th></tr></thead>
        <tbody>
          {{% for res in residents %}}
          <tr>
            <td class="mono">{{{{ res.reg_no }}}}</td>
            <td>{{{{ res.student_name }}}}</td>
            <td class="mono">{{{{ res.gender }}}}</td>
            <td>{{{{ res.block_name }}}}</td>
            <td class="mono">{{{{ res.room_number }}}}</td>
            <td>{{{{ res.programme_name }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="6">No residential students found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""


@warden_bp.route("/dashboard", methods=["GET"])
@role_required(ROLE_WARDEN)
def warden_dashboard():
    """Warden Dashboard: queries hostel blocks, room occupancy overview, and residential student directory."""
    try:
        blocks = execute_query("SELECT * FROM HOSTEL_BLOCK ORDER BY block_id;") or []
        rooms = execute_query("SELECT * FROM v_warden_occupancy_overview ORDER BY block_name, room_number;") or []
        residents = execute_query("SELECT * FROM v_warden_resident_directory ORDER BY block_name, room_number, reg_no;") or []
    except Exception:
        blocks, rooms, residents = [], [], []

    try:
        return render_template(
            "warden/dashboard.html",
            blocks=blocks,
            rooms=rooms,
            residents=residents,
        ), 200
    except TemplateNotFound:
        return render_template_string(
            WARDEN_DASHBOARD_HTML,
            blocks=blocks,
            rooms=rooms,
            residents=residents,
        ), 200
