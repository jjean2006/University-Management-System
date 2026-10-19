"""Shared UI aesthetics, constants, and helpers for role blueprint views."""

# Institutional Neutral CSS Styles adhering to Review 2 and Anti-AI Checklist
COMMON_STYLES = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: #F8F9FA;
    color: #0F172A;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    padding: 24px 32px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    margin-bottom: 24px;
    border-bottom: 1px solid #E2E8F0;
  }
  h1 { font-size: 22px; font-weight: 600; color: #0F172A; }
  h2 { font-size: 16px; font-weight: 600; color: #1E293B; margin-top: 24px; margin-bottom: 12px; }
  .user-meta { font-size: 13px; color: #64748B; margin-top: 4px; }
  .logout-link {
    font-size: 13px;
    color: #991B1B;
    text-decoration: none;
    margin-left: 12px;
    padding: 5px 10px;
    border: 1px solid #FECACA;
    border-radius: 4px;
    background: #FEF2F2;
    transition: background-color 140ms ease-in-out;
  }
  .logout-link:hover { background: #FEE2E2; }
  .card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
  .table-responsive { overflow-x: auto; margin-top: 8px; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    color: #334155;
  }
  th {
    background-color: #F1F5F9;
    color: #0F172A;
    font-weight: 600;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid #CBD5E1;
  }
  td {
    padding: 10px 12px;
    border-bottom: 1px solid #E2E8F0;
  }
  tr:hover { background-color: #F8FAFC; }
  .mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 12.5px; }
  .badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .badge-paid, .badge-success { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
  .badge-partial, .badge-warning { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
  .badge-overdue, .badge-danger { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
  .badge-info { background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
  .btn {
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid transparent;
    transition: background-color 140ms ease-in-out;
  }
  .btn-primary { background: #1E293B; color: #FFFFFF; border-color: #1E293B; }
  .btn-primary:hover { background: #0F172A; }
  .form-control {
    padding: 6px 10px;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    font-size: 13px;
    outline: none;
    transition: border-color 140ms ease-in-out;
  }
  .form-control:focus {
    border-color: #1E293B;
  }
  .alert {
    padding: 10px 14px;
    border-radius: 4px;
    font-size: 13px;
    margin-bottom: 16px;
  }
  .alert-success { background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }
  .alert-error { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }
"""
