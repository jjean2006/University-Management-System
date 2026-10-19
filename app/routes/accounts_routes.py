import datetime
from decimal import Decimal
import os
import sys

_venv_site = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "venv", "lib", "python3.12", "site-packages")
)
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    url_for,
)
from jinja2 import TemplateNotFound

from app.auth import ROLE_ACCOUNTS, role_required
from app.db import execute_query, first_row, transaction
from app.routes.common import COMMON_STYLES
from app.validators import (
    INVOICE_NO_RE,
    ValidationError,
    integer,
    iso_date,
    money,
    required_text,
)

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")

ACCOUNTS_DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accounts Dashboard — University Management System</title>
  <link rel="stylesheet" href="/static/css/base.css">
  <style>{COMMON_STYLES}</style>
</head>
<body>
  <header>
    <div>
      <h1>University Financial Accounts & Fee Management</h1>
      <div class="user-meta">Bursar Office | Fee Invoicing, Collections & Defaulter Audits</div>
    </div>
    <div>
      <a href="/logout" class="logout-link">Sign Out</a>
    </div>
  </header>

  {{% with messages = get_flashed_messages(with_categories=true) %}}
    {{% if messages %}}
      {{% for category, message in messages %}}
        <div class="alert alert-{{{{ 'error' if category == 'error' else 'success' }}}}">{{{{ message }}}}</div>
      {{% endfor %}}
    {{% endif %}}
  {{% endwith %}}

  <div class="card">
    <h2>Revenue Summary KPIs</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Status</th><th>Invoice Count</th><th>Total Billed (₹)</th><th>Collected Revenue (₹)</th><th>Outstanding Balance (₹)</th></tr></thead>
        <tbody>
          {{% for row in summary %}}
          <tr>
            <td>
              <span class="badge {{{{ 'badge-paid' if row.payment_status == 'PAID' else ('badge-partial' if row.payment_status == 'PARTIAL' else 'badge-overdue') }}}}">
                {{{{ row.payment_status }}}}
              </span>
            </td>
            <td class="mono">{{{{ row.total_invoices if row.total_invoices is defined else (row.invoice_count if row.invoice_count is defined else '-') }}}}</td>
            <td class="mono">₹{{{{ row.total_billed_amount }}}}</td>
            <td class="mono">₹{{{{ row.total_collected_amount }}}}</td>
            <td class="mono">₹{{{{ row.outstanding_balance }}}}</td>
          </tr>
          {{% else %}}
          <tr><td colspan="5">No revenue summary records found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Fee Defaulters Directory</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Invoice No</th><th>Reg No</th><th>Student Name</th><th>Total Amount</th><th>Paid Amount</th><th>Balance Due</th><th>Due Date</th><th>Status</th></tr></thead>
        <tbody>
          {{% for d in defaulters %}}
          <tr>
            <td class="mono">{{{{ d.invoice_no }}}}</td>
            <td class="mono">{{{{ d.reg_no }}}}</td>
            <td>{{{{ d.student_name }}}}</td>
            <td class="mono">₹{{{{ d.total_amount }}}}</td>
            <td class="mono">₹{{{{ d.paid_amount }}}}</td>
            <td class="mono">₹{{{{ d.balance_due }}}}</td>
            <td class="mono">{{{{ d.due_date }}}}</td>
            <td><span class="badge badge-warning">{{{{ d.payment_status }}}}</span></td>
          </tr>
          {{% else %}}
          <tr><td colspan="8">No outstanding fee defaulters found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Complete Invoicing Ledger</h2>
    <div class="table-responsive">
      <table>
        <thead><tr><th>Payment ID</th><th>Invoice No</th><th>Student ID</th><th>Total (₹)</th><th>Paid (₹)</th><th>Due Date</th><th>Status</th></tr></thead>
        <tbody>
          {{% for l in ledger %}}
          <tr>
            <td class="mono">{{{{ l.payment_id }}}}</td>
            <td class="mono">{{{{ l.invoice_no }}}}</td>
            <td class="mono">{{{{ l.student_id }}}}</td>
            <td class="mono">₹{{{{ l.total_amount }}}}</td>
            <td class="mono">₹{{{{ l.paid_amount }}}}</td>
            <td class="mono">{{{{ l.due_date }}}}</td>
            <td>
              <span class="badge {{{{ 'badge-paid' if l.payment_status == 'PAID' else ('badge-partial' if l.payment_status == 'PARTIAL' else 'badge-overdue') }}}}">
                {{{{ l.payment_status }}}}
              </span>
            </td>
          </tr>
          {{% else %}}
          <tr><td colspan="7">No payment records found.</td></tr>
          {{% endfor %}}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Record Fee Payment Update</h2>
    <form method="POST" action="/accounts/record-payment">
      <div style="display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap;">
        <div>
          <label style="display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-bottom: 4px; color: #334155;">Invoice Number:</label>
          <input type="text" name="invoice_no" placeholder="e.g. INV-2026-003" class="form-control" style="min-width: 220px;" required>
        </div>
        <div>
          <label style="display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; margin-bottom: 4px; color: #334155;">Payment Amount (₹):</label>
          <input type="number" step="0.01" name="amount_paid" placeholder="Enter amount" class="form-control" style="min-width: 180px;" required>
        </div>
        <div>
          <button type="submit" class="btn btn-primary">Record Payment</button>
        </div>
      </div>
    </form>
  </div>
</body>
</html>
"""


@accounts_bp.route("/dashboard", methods=["GET"])
@role_required(ROLE_ACCOUNTS)
def accounts_dashboard():
    """Accounts Dashboard: displays fee summary KPIs, defaulters list, invoicing ledger, and student list for adding dues."""
    summary, defaulters, ledger, students = [], [], [], []
    try:
        summary = execute_query("SELECT * FROM v_accounts_fee_summary;") or []
    except Exception:
        pass
    try:
        defaulters = execute_query("SELECT * FROM v_accounts_defaulters_list;") or []
    except Exception:
        pass
    try:
        ledger = execute_query("SELECT f.*, s.reg_no, s.first_name, s.last_name FROM FEE_PAYMENT f LEFT JOIN STUDENT s ON f.student_id = s.student_id ORDER BY f.payment_id DESC;") or []
    except Exception:
        pass
    try:
        students = execute_query("SELECT student_id, reg_no, first_name, last_name FROM STUDENT ORDER BY reg_no;") or []
    except Exception:
        pass

    try:
        return render_template(
            "accounts/dashboard.html",
            summary=summary,
            defaulters=defaulters,
            ledger=ledger,
            students=students,
        ), 200
    except TemplateNotFound:
        return render_template_string(
            ACCOUNTS_DASHBOARD_HTML,
            summary=summary,
            defaulters=defaulters,
            ledger=ledger,
            students=students,
        ), 200


def _payment_status(total_amount, paid_amount, due_date):
    """Derives an invoice's status from its amounts and due date."""
    if paid_amount >= total_amount:
        return "PAID"
    if due_date < datetime.date.today():
        return "OVERDUE"
    return "PARTIAL" if paid_amount > 0 else "PENDING"


@accounts_bp.route("/add-dues", methods=["POST"])
@role_required(ROLE_ACCOUNTS)
def accounts_add_dues():
    """Create a new fee payment / due record in FEE_PAYMENT."""
    try:
        student_id = integer(request.form.get("student_id"), "Student", min_value=1)
        invoice_no = required_text(
            (request.form.get("invoice_no") or "").upper(), "Invoice number", 20, INVOICE_NO_RE,
            "letters, digits and hyphens, e.g. INV-2026-005",
        )
        total_amount = money(request.form.get("total_amount"), "Total amount", min_value=Decimal("1.00"))
        paid_amount = money(request.form.get("paid_amount") or "0", "Initial amount paid")
        if paid_amount > total_amount:
            raise ValidationError("Initial amount paid cannot be more than the total amount.")
        due_date = iso_date(request.form.get("due_date"), "Due date", not_before=datetime.date.today())

        student = execute_query("SELECT reg_no FROM STUDENT WHERE student_id = %s;", (student_id,), fetch_one=True)
        if not student:
            raise ValidationError(f"Student #{student_id} does not exist.")
        if execute_query("SELECT 1 AS ok FROM FEE_PAYMENT WHERE invoice_no = %s;", (invoice_no,), fetch_one=True):
            raise ValidationError(f"Invoice number {invoice_no} already exists.")
    except ValidationError as e:
        flash(str(e), "danger")
        return redirect(url_for("accounts.accounts_dashboard"))

    payment_status = _payment_status(total_amount, paid_amount, due_date)
    payment_date = datetime.date.today().isoformat() if paid_amount > 0 else None

    try:
        execute_query(
            "INSERT INTO FEE_PAYMENT (student_id, invoice_no, total_amount, paid_amount, due_date, payment_status, payment_date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (student_id, invoice_no, total_amount, paid_amount, due_date.isoformat(), payment_status, payment_date),
            commit=True,
        )
        flash(f"Invoice {invoice_no} issued successfully for ₹{total_amount:,.2f} (Status: {payment_status}).", "success")
    except Exception as e:
        flash(f"Failed to issue invoice {invoice_no}: {str(e)}", "danger")

    return redirect(url_for("accounts.accounts_dashboard"))


def _payment_error(message, status_code):
    if request.is_json:
        return jsonify({"status": "error", "message": message}), status_code
    flash(message, "danger")
    return redirect(url_for("accounts.accounts_dashboard"))


@accounts_bp.route("/record-payment", methods=["POST"])
@role_required(ROLE_ACCOUNTS)
def accounts_record_payment():
    """Genuine fee transaction endpoint: updates paid_amount, payment_status, and payment_date in FEE_PAYMENT."""
    data = request.get_json(silent=True) if request.is_json else {}

    invoice_no = (request.form.get("invoice_no") or data.get("invoice_no") or "").strip()
    raw_amount = request.form.get("amount_paid") or data.get("amount_paid")

    if not invoice_no:
        return _payment_error("Invoice number is required to record a payment.", 400)

    try:
        amount = money(raw_amount, "Payment amount", min_value=Decimal("0.01"))
    except ValidationError as e:
        return _payment_error(str(e), 400)

    try:
        with transaction() as cur:
            cur.execute(
                "SELECT total_amount, paid_amount, due_date, payment_status FROM FEE_PAYMENT WHERE invoice_no = %s FOR UPDATE;",
                (invoice_no,),
            )
            inv = first_row(cur)
            if not inv:
                return _payment_error(f"Invoice '{invoice_no}' not found in the fee payment ledger.", 404)

            total_amount = Decimal(str(inv.get("total_amount")))
            curr_paid = Decimal(str(inv.get("paid_amount")))
            balance = total_amount - curr_paid
            if balance <= 0:
                return _payment_error(f"Invoice {invoice_no} is already fully paid.", 400)
            if amount > balance:
                return _payment_error(
                    f"Payment of ₹{amount:,.2f} exceeds the outstanding balance of ₹{balance:,.2f} on {invoice_no}.", 400
                )

            due_date = inv.get("due_date")
            if not isinstance(due_date, datetime.date):
                due_date = datetime.date.fromisoformat(str(due_date))
            new_paid = curr_paid + amount
            new_status = _payment_status(total_amount, new_paid, due_date)

            cur.execute(
                "UPDATE FEE_PAYMENT SET paid_amount = %s, payment_status = %s, payment_date = CURDATE() "
                "WHERE invoice_no = %s;",
                (new_paid, new_status, invoice_no),
            )
    except Exception as e:
        return _payment_error(f"Database transaction failed: {str(e)}", 500)

    if request.is_json:
        return jsonify({
            "status": "success",
            "message": "Payment recorded successfully",
            "invoice_no": invoice_no,
            "paid_amount": float(new_paid),
            "total_amount": float(total_amount),
            "payment_status": new_status,
        }), 200

    if request.form.get("redirect") == "false":
        return "Payment recorded successfully", 200

    flash(
        f"Payment of ₹{amount:,.2f} recorded for invoice {invoice_no}. Status updated to {new_status}.",
        "success",
    )
    return redirect(url_for("accounts.accounts_dashboard"))


@accounts_bp.route("/invoices/delete", methods=["POST"])
@role_required(ROLE_ACCOUNTS)
def accounts_delete_invoice():
    """Cancel (delete) an invoice that has not received any payment yet."""
    invoice_no = (request.form.get("invoice_no") or "").strip()
    if not invoice_no:
        flash("Invoice number is required.", "danger")
        return redirect(url_for("accounts.accounts_dashboard"))

    try:
        deleted = execute_query(
            "DELETE FROM FEE_PAYMENT WHERE invoice_no = %s AND paid_amount = 0;",
            (invoice_no,),
            commit=True,
        )
        if deleted:
            flash(f"Invoice {invoice_no} has been cancelled and removed from the ledger.", "success")
        elif execute_query("SELECT 1 AS ok FROM FEE_PAYMENT WHERE invoice_no = %s;", (invoice_no,), fetch_one=True):
            flash(f"Invoice {invoice_no} already has payments recorded and cannot be cancelled.", "warning")
        else:
            flash(f"Invoice '{invoice_no}' not found.", "danger")
    except Exception as e:
        flash(f"Failed to cancel invoice {invoice_no}: {str(e)}", "danger")

    return redirect(url_for("accounts.accounts_dashboard"))
