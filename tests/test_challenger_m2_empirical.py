"""Empirical Challenger Test Suite for Milestone 2: Auth & Security Boundaries.

Adversarially tests:
1. Unauthenticated requests to protected routes -> redirect to /login
2. Cross-role authorization matrix -> 403 Forbidden on role mismatch
3. Invalid passwords, non-existent usernames, SQL injection payloads -> 401 with error feedback, no crashes
4. Session lifecycle: logout termination, session purging, open redirect defense, session tampering
5. Empirical reproduction of identified security vulnerabilities (Open Redirect via backslash, Infinite Redirect Loop)
"""

import pytest


class TestUnauthenticatedProtection:
    """Verifies that all protected endpoints strictly enforce authentication."""

    PROTECTED_ROUTES = [
        "/admin/dashboard",
        "/faculty/dashboard",
        "/student/dashboard",
        "/accounts/dashboard",
        "/warden/dashboard",
    ]

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_unauthenticated_dashboards_redirect_to_login(self, client, route):
        """Unauthenticated GET to protected dashboard routes must return 302 redirecting to /login."""
        res = client.get(route, follow_redirects=False)
        assert res.status_code == 302, f"Expected 302 redirect for {route}, got {res.status_code}"
        location = res.headers.get("Location", "")
        assert "/login" in location, f"Expected Location header pointing to /login for {route}, got {location}"
        assert f"next={route.replace('/', '%2F')}" in location or f"next={route}" in location, (
            f"Expected next parameter containing target route for {route}, got {location}"
        )

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_unauthenticated_dashboards_redirect_destination(self, client, route):
        """Following redirect leads to /login with HTTP 200 and login form."""
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200
        assert "login" in res.request.path.lower()
        body = res.get_data(as_text=True)
        assert 'name="username"' in body
        assert 'name="password"' in body

    def test_unauthenticated_post_faculty_attendance_blocked(self, client):
        """Unauthenticated POST /faculty/attendance must redirect to /login or return 401/403."""
        res = client.post(
            "/faculty/attendance",
            data={"course_id": 1, "attendance_date": "2026-10-19"},
            follow_redirects=False,
        )
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_unauthenticated_post_accounts_record_payment_blocked(self, client):
        """Unauthenticated POST /accounts/record-payment must redirect to /login or return 401/403."""
        res = client.post(
            "/accounts/record-payment",
            data={"invoice_no": "INV-2026-001", "amount_paid": "5000.00"},
            follow_redirects=False,
        )
        assert res.status_code in (302, 401, 403)
        if res.status_code == 302:
            assert "/login" in res.headers.get("Location", "")

    def test_unauthenticated_root_redirects_to_login(self, client):
        """Unauthenticated GET / must redirect to /login."""
        res = client.get("/", follow_redirects=False)
        assert res.status_code == 302
        assert "/login" in res.headers.get("Location", "")


class TestStudentCrossRoleBoundaries:
    """Verifies that student role cannot access any privileged routes or actions."""

    FORBIDDEN_STUDENT_ROUTES = [
        "/admin/dashboard",
        "/faculty/dashboard",
        "/accounts/dashboard",
        "/warden/dashboard",
    ]

    @pytest.mark.parametrize("route", FORBIDDEN_STUDENT_ROUTES)
    def test_student_forbidden_from_other_dashboards(self, student_client, route):
        """Student role accessing non-student dashboards must receive HTTP 403 Forbidden."""
        res = student_client.get(route, follow_redirects=False)
        assert res.status_code == 403, (
            f"Student access to {route} returned status {res.status_code}, expected 403 Forbidden."
        )

    def test_student_forbidden_from_marking_attendance(self, student_client):
        """Student attempting to POST to /faculty/attendance must receive HTTP 403 Forbidden."""
        res = student_client.post(
            "/faculty/attendance",
            data={"course_id": 1, "attendance_date": "2026-10-19"},
            follow_redirects=False,
        )
        assert res.status_code == 403, (
            f"Student POST to /faculty/attendance returned status {res.status_code}, expected 403."
        )

    def test_student_forbidden_from_recording_payment(self, student_client):
        """Student attempting to POST to /accounts/record-payment must receive HTTP 403 Forbidden."""
        res = student_client.post(
            "/accounts/record-payment",
            data={"invoice_no": "INV-2026-001", "amount_paid": "1000"},
            follow_redirects=False,
        )
        assert res.status_code == 403, (
            f"Student POST to /accounts/record-payment returned status {res.status_code}, expected 403."
        )

    def test_student_can_access_student_dashboard(self, student_client):
        """Student role accessing /student/dashboard must succeed with HTTP 200."""
        res = student_client.get("/student/dashboard", follow_redirects=False)
        assert res.status_code == 200
        content = res.get_data(as_text=True)
        assert "Student Academic Portal" in content or "student" in content.lower()


class TestFullCrossRoleMatrix:
    """Exhaustive matrix of all 5 roles across all 5 dashboards (25 combinations)."""

    ROLES_CLIENTS = ["admin", "faculty", "student", "accounts", "warden"]
    ROUTES_MAP = {
        "admin": "/admin/dashboard",
        "faculty": "/faculty/dashboard",
        "student": "/student/dashboard",
        "accounts": "/accounts/dashboard",
        "warden": "/warden/dashboard",
    }

    def _get_role_client(self, role, request):
        return request.getfixturevalue(f"{role}_client")

    @pytest.mark.parametrize("accessor_role", ROLES_CLIENTS)
    @pytest.mark.parametrize("target_role", ROLES_CLIENTS)
    def test_cross_role_dashboard_access_matrix(self, accessor_role, target_role, request):
        """Every role should access ONLY its own dashboard (HTTP 200) and get 403 on all others."""
        client = self._get_role_client(accessor_role, request)
        target_route = self.ROUTES_MAP[target_role]
        res = client.get(target_route, follow_redirects=False)

        if accessor_role == target_role:
            assert res.status_code == 200, (
                f"Role {accessor_role} failed to access its own dashboard {target_route} (status: {res.status_code})"
            )
        else:
            assert res.status_code == 403, (
                f"Role {accessor_role} was NOT forbidden from accessing {target_route} (status: {res.status_code})"
            )


class TestCredentialRejectionsAndFeedback:
    """Adversarial stress-testing of credential evaluation, negative paths, and error feedback."""

    @pytest.mark.parametrize("username,password", [
        ("admin", "wrong_admin_pw"),
        ("faculty", "wrong_faculty_pw"),
        ("EMP1001", "wrong_emp_pw"),
        ("student", "wrong_student_pw"),
        ("25BAI0077", "wrong_reg_pw"),
        ("accounts", "wrong_acc_pw"),
        ("warden", "wrong_warden_pw"),
    ])
    def test_invalid_passwords_rejected_with_401(self, client, username, password):
        """Valid usernames with incorrect passwords must be rejected with 401 and an error alert."""
        res = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
        assert res.status_code == 401, f"Expected 401 for invalid password on {username}, got {res.status_code}"
        body = res.get_data(as_text=True)
        assert "Invalid credentials" in body or "alert" in body.lower()

    @pytest.mark.parametrize("fake_user", [
        "nonexistent_user",
        "fake_admin",
        "hacker_123",
        "STUDENT9999",
        "EMP9999",
        "root",
    ])
    def test_nonexistent_usernames_rejected_with_401(self, client, fake_user):
        """Non-existent usernames must be rejected with 401 without server crash."""
        res = client.post("/login", data={"username": fake_user, "password": "any_password"}, follow_redirects=False)
        assert res.status_code == 401, f"Expected 401 for nonexistent user {fake_user}, got {res.status_code}"
        body = res.get_data(as_text=True)
        assert "Invalid credentials" in body or "error" in body.lower()

    @pytest.mark.parametrize("u,p", [
        ("", ""),
        ("admin", ""),
        ("", "admin123"),
        ("   ", "   "),
        ("\t\n", "\r\n"),
    ])
    def test_empty_and_whitespace_credentials_rejected(self, client, u, p):
        """Empty or whitespace credentials must be rejected with 401 and not establish a session."""
        res = client.post("/login", data={"username": u, "password": p}, follow_redirects=False)
        assert res.status_code == 401

    @pytest.mark.parametrize("sqli_payload", [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin' --",
        "admin' /*",
        "' UNION SELECT 1, 'admin', 'admin', 'admin', 'admin' --",
        "\" OR \"\"=\"",
        "\\'; DROP TABLE STUDENT; --",
    ])
    def test_sql_injection_payloads_safely_rejected(self, client, sqli_payload):
        """SQL injection payloads in username and password must be rejected with 401 without executing."""
        res = client.post("/login", data={"username": sqli_payload, "password": "password"}, follow_redirects=False)
        assert res.status_code == 401

        res_p = client.post("/login", data={"username": "admin", "password": sqli_payload}, follow_redirects=False)
        assert res_p.status_code == 401

    def test_oversized_credential_payloads_rejected_cleanly(self, client):
        """Excessively large credential payloads (buffer overflow / DoS probe) must not crash server."""
        oversized_str = "A" * 10000
        res = client.post("/login", data={"username": oversized_str, "password": oversized_str}, follow_redirects=False)
        assert res.status_code in (400, 401, 413)

    def test_json_payload_authentication_invalid_type_rejected(self, client):
        """Non-string data types in JSON auth request must be handled cleanly without 500 error."""
        res = client.post(
            "/login",
            json={"username": 12345, "password": True},
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code == 401

    def test_case_insensitive_usernames(self, client):
        """Demo usernames should authenticate irrespective of input case (e.g. ADMIN or admin)."""
        res = client.post("/login", data={"username": "ADMIN", "password": "admin123"}, follow_redirects=False)
        assert res.status_code == 302
        assert res.headers.get("Location") == "/admin/dashboard"

        res_fac = client.post("/login", data={"username": "emp1001", "password": "password"}, follow_redirects=False)
        assert res_fac.status_code == 302
        assert res_fac.headers.get("Location") == "/faculty/dashboard"


class TestSessionLifecycleAndLogout:
    """Verifies session setup, termination, expiration, tampering, and redirection security."""

    def test_get_logout_terminates_session(self, admin_client):
        """GET /logout must purge session and redirect to /login."""
        # Confirm authenticated
        res_pre = admin_client.get("/admin/dashboard", follow_redirects=False)
        assert res_pre.status_code == 200

        # Perform logout
        res_logout = admin_client.get("/logout", follow_redirects=False)
        assert res_logout.status_code == 302
        assert "/login" in res_logout.headers.get("Location", "")

        # Post-logout: accessing protected route must redirect to /login
        res_post = admin_client.get("/admin/dashboard", follow_redirects=False)
        assert res_post.status_code == 302
        assert "/login" in res_post.headers.get("Location", "")

    def test_post_logout_terminates_session(self, faculty_client):
        """POST /logout must also purge session and redirect to /login."""
        res_pre = faculty_client.get("/faculty/dashboard", follow_redirects=False)
        assert res_pre.status_code == 200

        res_logout = faculty_client.post("/logout", follow_redirects=False)
        assert res_logout.status_code == 302
        assert "/login" in res_logout.headers.get("Location", "")

        res_post = faculty_client.get("/faculty/dashboard", follow_redirects=False)
        assert res_post.status_code == 302
        assert "/login" in res_post.headers.get("Location", "")

    def test_standard_external_redirects_prevented(self, client):
        """Verify scheme-prefixed and double-slash external next URLs are rejected."""
        blocked_urls = [
            "https://evil-phishing.com",
            "http://attacker.com/steal-cookie",
            "//attacker.com",
            "javascript:alert(1)",
        ]
        for bad_url in blocked_urls:
            res = client.post(
                "/login",
                data={"username": "admin", "password": "admin123", "next": bad_url},
                follow_redirects=False,
            )
            assert res.status_code == 302
            location = res.headers.get("Location", "")
            assert not location.startswith("http://")
            assert not location.startswith("https://")
            assert not location.startswith("//")
            assert location == "/admin/dashboard"

    def test_legitimate_internal_next_redirect_succeeds(self, client):
        """Legitimate internal URL in next parameter should redirect to that route upon login."""
        res = client.post(
            "/login",
            data={"username": "admin", "password": "admin123", "next": "/admin/dashboard?view=full"},
            follow_redirects=False,
        )
        assert res.status_code == 302
        assert res.headers.get("Location") == "/admin/dashboard?view=full"

    def test_tampered_or_unknown_role_session_denied(self, client):
        """A session with an unknown or manipulated role must be denied access with HTTP 403."""
        with client.session_transaction() as sess:
            sess["user_id"] = 999
            sess["username"] = "rogue_user"
            sess["role"] = "superadmin"  # Non-existent role
            sess["logged_in"] = True

        for route in [
            "/admin/dashboard",
            "/faculty/dashboard",
            "/student/dashboard",
            "/accounts/dashboard",
            "/warden/dashboard",
        ]:
            res = client.get(route, follow_redirects=False)
            assert res.status_code == 403, (
                f"Rogue role 'superadmin' gained access to {route} with status {res.status_code}"
            )

    def test_logged_in_flag_with_empty_role_denied(self, client):
        """A session with logged_in=True but empty role must be denied with HTTP 403."""
        with client.session_transaction() as sess:
            sess["user_id"] = 999
            sess["username"] = "empty_role_user"
            sess["role"] = ""
            sess["logged_in"] = True

        res = client.get("/admin/dashboard", follow_redirects=False)
        assert res.status_code == 403

    def test_session_role_switching(self, client):
        """Logging in as Admin, then re-logging in as Student changes identity and restricts access."""
        # Step 1: Login as admin
        res1 = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
        assert res1.status_code == 302
        assert client.get("/admin/dashboard", follow_redirects=False).status_code == 200

        # Step 2: Login as student
        res2 = client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=False)
        assert res2.status_code == 302
        assert client.get("/student/dashboard", follow_redirects=False).status_code == 200

        # Step 3: Admin dashboard is now 403 Forbidden
        assert client.get("/admin/dashboard", follow_redirects=False).status_code == 403


class TestVulnerabilityRegressions:
    """Regression tests for authentication vulnerabilities found earlier and since fixed."""

    def test_vuln1_open_redirect_backslash_bypass_blocked(self, client):
        """Open redirect via backslash (/\\attacker.com) must fall back to the role dashboard."""
        payload = "/\\attacker.com"
        res = client.post(
            "/login",
            data={"username": "admin", "password": "admin123", "next": payload},
            follow_redirects=False,
        )
        assert res.status_code == 302
        assert res.headers.get("Location", "") == "/admin/dashboard"

    def test_vuln2_corrupted_role_session_no_redirect_loop(self, client):
        """A session with logged_in=True but no role must be cleared and show the login page (no 302 loop)."""
        with client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["user_id"] = 100
            sess["username"] = "corrupted_session_user"
            sess["role"] = None

        res = client.get("/login", follow_redirects=True)
        assert res.status_code == 200
        assert b"Sign In" in res.data or b"sign in" in res.data.lower()
