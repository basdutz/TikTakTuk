import uuid

import psycopg2
import os
import json

from dotenv import load_dotenv
load_dotenv()
print("DB URL:", os.getenv("DATABASE_URL"))

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse

from .models import UserAccount, Customer, Organizer

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    return conn

def set_schema(conn):
    with conn.cursor() as cur:
        cur.execute('SET search_path TO "TIKTAKTUK", public;')

def extract_pg_error(e):
    """Ambil pesan bersih dari psycopg2.Error (dari RAISE EXCEPTION trigger)."""
    raw = getattr(e, 'pgerror', None) or str(e)
    first_line = raw.strip().split('\n')[0]
    # Hilangkan prefix "ERROR:  " dari PostgreSQL
    return first_line.replace('ERROR:  ', '').replace('ERROR: ', '').strip()

#  ROLE / SESSION HELPERS
DB_ROLE_TO_APP = {
    'administrator': 'admin',
    'organizer':     'organizer',
    'customer':      'customer',
}

def _current_role(request):
    return request.session.get('role')
 
def _resolve_role(request):
    return _current_role(request)

def _ctx(request, **extra):
    role = _current_role(request)
    base = {
        'role':         role,
        'username':     request.session.get('username'),
        'display_name': request.session.get('display_name'),
        'organizer_id': request.session.get('organizer_id'),
        'customer_id':  request.session.get('customer_id'),
        'is_admin':     role == 'admin',
        'is_organizer': role == 'organizer',
        'is_customer':  role == 'customer',
    }
    base.update(extra)
    return base

def _require_manage(request):
    """True jika user boleh CRUD venue/event (admin atau organizer)."""
    return _current_role(request) in ('admin', 'organizer')
 
def _redirect_dashboard(app_role):
    return redirect({
        'admin':     'main:dashboard_admin',
        'organizer': 'main:dashboard_organizer',
        'customer':  'main:dashboard_customer',
    }.get(app_role, 'main:home'))

def _require_role(request, allowed_role):
    role = _current_role(request)
    if not role:
        return redirect('main:home')
    if role != allowed_role:
        return _redirect_dashboard(role)
    return None


def _authenticate(username, password):
    if not username or not password:
        raise ValueError('Username dan password wajib diisi.')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "user_id"::text, "PASSWORD"
                  FROM "USER_ACCOUNT"
                 WHERE LOWER("username") = LOWER(%s)
            """, [username])
            row = cur.fetchone()

            if not row or row[1] != password:
                raise ValueError('Username atau password salah.')

            user_id = row[0]

            cur.execute("""
                SELECT r."role_name"
                  FROM "ACCOUNT_ROLE" ar
                  JOIN "ROLE" r ON r."role_id" = ar."role_id"
                 WHERE ar."user_id" = %s::uuid
              ORDER BY r."role_name"
            """, [user_id])
            db_roles = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    app_roles = [
        DB_ROLE_TO_APP[r] for r in db_roles if r in DB_ROLE_TO_APP
    ]
    if not app_roles:
        raise ValueError('Akun tidak memiliki role aktif.')

    return {'user_id': user_id, 'roles': app_roles}


def _fetch_profile_for_role(user_id, app_role):
    """
    Ambil display_name & profile_id (organizer_id/customer_id) sesuai role.
    Return (profile_id, display_name).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if app_role == 'organizer':
                cur.execute("""
                    SELECT "organizer_id"::text, "organization_name"
                      FROM "ORGANIZER"
                     WHERE "user_id" = %s::uuid
                """, [user_id])
            elif app_role == 'customer':
                cur.execute("""
                    SELECT "customer_id"::text, "full_name"
                      FROM "CUSTOMER"
                     WHERE "user_id" = %s::uuid
                """, [user_id])
            else:  # admin
                cur.execute("""
                    SELECT "user_id"::text, "username"
                      FROM "USER_ACCOUNT"
                     WHERE "user_id" = %s::uuid
                """, [user_id])

            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return (None, None)
    return (row[0], row[1])


def _set_session_for_role(request, user_id, app_role):
    profile_id, display_name = _fetch_profile_for_role(user_id, app_role)

    # Flush dulu supaya tidak ada residu dari role lain
    request.session.flush()

    request.session['user_id']      = user_id
    request.session['role']         = app_role
    request.session['username']     = display_name or ''
    request.session['display_name'] = display_name or ''

    if app_role == 'organizer':
        request.session['organizer_id'] = profile_id
    elif app_role == 'customer':
        request.session['customer_id']  = profile_id

#  PUBLIC / AUTH VIEWS
def home(request):
    return render(request, "main/home.html")

def register(request):
    return render(request, "main/register_role.html")

def register_customer(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone     = request.POST.get("phone_number")
        username  = request.POST.get("username")
        password  = request.POST.get("password")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM "USER_ACCOUNT"
                    WHERE LOWER("username") = LOWER(%s)
                """, [username])
                if cur.fetchone():
                    messages.error(request, "Username sudah dipakai")
                    return redirect("main:register_customer")

                user_id     = uuid.uuid4()
                customer_id = uuid.uuid4()

                cur.execute("""
                    INSERT INTO "USER_ACCOUNT" ("user_id", "username", "PASSWORD")
                    VALUES (%s, %s, %s)
                """, [user_id, username, password])

                cur.execute("""
                    INSERT INTO "CUSTOMER" ("customer_id", "full_name", "phone_number", "user_id")
                    VALUES (%s, %s, %s, %s)
                """, [customer_id, full_name, phone, user_id])

                cur.execute("""
                    INSERT INTO "ACCOUNT_ROLE" ("role_id", "user_id")
                    SELECT "role_id", %s FROM "ROLE" WHERE "role_name" = 'customer'
                """, [user_id])

            conn.commit()
            messages.success(request, "Registrasi customer berhasil")
            return redirect("main:login")

        except Exception as e:
            conn.rollback()
            messages.error(request, str(e))
        finally:
            conn.close()

    return render(request, "main/register_customer.html")

def register_organizer(request):
    if request.method == "POST":
        name = request.POST.get("organization_name")
        email = request.POST.get("contact_email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT 1
                    FROM "USER_ACCOUNT"
                    WHERE LOWER("username") = LOWER(%s)
                """, [username])

                if cur.fetchone():
                    messages.error(request, "Username sudah dipakai")
                    return redirect("main:register_organizer")

                user_id = uuid.uuid4()

                cur.execute("""
                    INSERT INTO "USER_ACCOUNT"
                        ("user_id", "username", "PASSWORD")
                    VALUES (%s, %s, %s)
                """, [user_id, username, password])

                organizer_id = uuid.uuid4()

                cur.execute("""
                    INSERT INTO "ORGANIZER"
                        ("organizer_id", "organization_name", "contact_email", "user_id")
                    VALUES (%s, %s, %s, %s)
                """, [organizer_id, name, email, user_id])

                cur.execute("""
                    INSERT INTO "ACCOUNT_ROLE" ("role_id", "user_id")
                    SELECT "role_id", %s FROM "ROLE" WHERE "role_name" = 'organizer'
                """, [user_id])

            conn.commit()

            messages.success(request, "Registrasi organizer berhasil")
            return redirect("main:login")

        except Exception as e:
            conn.rollback()
            messages.error(request, str(e))

        finally:
            conn.close()

    return render(request, "main/register_organizer.html")

def register_admin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM "USER_ACCOUNT"
                    WHERE LOWER("username") = LOWER(%s)
                """, [username])
                if cur.fetchone():
                    messages.error(request, "Username sudah dipakai")
                    return redirect("main:register_admin")

                user_id = uuid.uuid4()

                cur.execute("""
                    INSERT INTO "USER_ACCOUNT" ("user_id", "username", "PASSWORD")
                    VALUES (%s, %s, %s)
                """, [user_id, username, password])

                cur.execute("""
                    INSERT INTO "ACCOUNT_ROLE" ("role_id", "user_id")
                    SELECT "role_id", %s FROM "ROLE" WHERE "role_name" = 'administrator'
                """, [user_id])

            conn.commit()
            messages.success(request, "Registrasi admin berhasil")
            return redirect("main:login")

        except Exception as e:
            conn.rollback()
            messages.error(request, str(e))
        finally:
            conn.close()

    return render(request, "main/register_admin.html")

# Login and Logout
@require_http_methods(['GET', 'POST'])
def login(request):
    # Sudah login? langsung ke dashboard
    if request.session.get('role'):
        return _redirect_dashboard(request.session['role'])

    if request.method == 'GET':
        return render(request, 'main/login.html')

    # POST
    username   = (request.POST.get('username') or '').strip()
    password   = request.POST.get('password') or ''
    chosen_role = request.POST.get('role')  # diisi pada step kedua (multi-role)

    if not username or not password:
        return render(request, 'main/login.html', {
            'error': True,
            'message': 'Username dan password wajib diisi.',
            'username': username,
        })

    try:
        auth = _authenticate(username, password)
    except ValueError as e:
        return render(request, 'main/login.html', {
            'error': True,
            'message': str(e),
        })

    roles    = auth['roles']
    user_id  = auth['user_id']

    # Single role -> langsung login
    if len(roles) == 1:
        _set_session_for_role(request, user_id, roles[0])
        return _redirect_dashboard(roles[0])

    # Multi-role
    if chosen_role and chosen_role in roles:
        _set_session_for_role(request, user_id, chosen_role)
        return _redirect_dashboard(chosen_role)

    # Belum pilih -> tampilkan role picker
    return render(request, 'main/login.html', {
        'multi_role': True,
        'roles': roles,
        'username': username,
        'password': password, 
        'display_name': username,
    })


def logout(request):
    request.session.flush()
    return redirect('main:home')

#  DASHBOARDS
def dashboard(request):
    role = request.session.get('role')
    if not role:
        return redirect('main:home')
    return _redirect_dashboard(role)


def dashboard_admin(request):
    guard = _require_role(request, 'admin')
    if guard:
        return guard

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM "USER_ACCOUNT"')
            total_users = cur.fetchone()[0]

            cur.execute('SELECT COUNT(*) FROM "EVENT"')
            total_events = cur.fetchone()[0]

            cur.execute("""
                SELECT COALESCE(SUM("total_amount"), 0)
                FROM "ORDER" WHERE "payment_status" = 'Completed'
            """)
            total_revenue = int(cur.fetchone()[0])

            cur.execute('SELECT COUNT(*) FROM "PROMOTION"')
            total_promos = cur.fetchone()[0]

            cur.execute('SELECT COUNT(*) FROM "VENUE"')
            total_venues = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM "VENUE" WHERE "seat_type" = 'Reserved Seating'
            """)
            reserved_venues = cur.fetchone()[0]

            cur.execute("""
                SELECT MAX("capacity") FROM "VENUE"
            """)
            max_capacity = cur.fetchone()[0] or 0

            cur.execute("""
                SELECT COUNT(*) FROM "PROMOTION"
                WHERE "discount_type" = 'PERCENTAGE'
            """)
            promo_persen = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM "PROMOTION"
                WHERE "discount_type" = 'NOMINAL'
            """)
            promo_nominal = cur.fetchone()[0]

            cur.execute('SELECT COUNT(*) FROM "ORDER_PROMOTION"')
            total_promo_usage = cur.fetchone()[0]
    finally:
        conn.close()

    def fmt_rupiah(val):
        if val >= 1_000_000:
            return f"Rp {val/1_000_000:.1f}M"
        return f"Rp {val:,}"

    return render(request, "main/dashboard_admin.html", _ctx(
        request,
        total_users=total_users,
        total_events=total_events,
        total_revenue=fmt_rupiah(total_revenue),
        total_promos=total_promos,
        total_venues=total_venues,
        reserved_venues=reserved_venues,
        max_capacity=f"{max_capacity:,}",
        promo_persen=promo_persen,
        promo_nominal=promo_nominal,
        total_promo_usage=total_promo_usage,
    ))


def dashboard_organizer(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return guard

    organizer_id = request.session.get('organizer_id')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Acara aktif (event di masa depan)
            cur.execute("""
                SELECT COUNT(*)
                FROM "EVENT"
                WHERE "organizer_id" = %s::uuid
                  AND "event_datetime" > NOW()
            """, [organizer_id])
            total_acara_aktif = cur.fetchone()[0]

            # Total tiket terjual (order Completed)
            cur.execute("""
                SELECT COUNT(t.ticket_id)
                FROM "TICKET" t
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                JOIN "ORDER" o ON o.order_id = t.torder_id
                WHERE e.organizer_id = %s::uuid
                  AND o.payment_status = 'Completed'
            """, [organizer_id])
            total_tiket_terjual = cur.fetchone()[0]

            # Revenue (order Completed)
            cur.execute("""
                SELECT COALESCE(SUM(o.total_amount), 0)
                FROM "ORDER" o
                JOIN "TICKET" t ON t.torder_id = o.order_id
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                WHERE e.organizer_id = %s::uuid
                  AND o.payment_status = 'Completed'
            """, [organizer_id])
            total_revenue = int(cur.fetchone()[0])

            # Venue mitra (distinct venue dari event organizer)
            cur.execute("""
                SELECT COUNT(DISTINCT e.venue_id)
                FROM "EVENT" e
                WHERE e.organizer_id = %s::uuid
            """, [organizer_id])
            total_venue_mitra = cur.fetchone()[0]

            # Performa acara: event mendatang + % terjual
            cur.execute("""
                SELECT
                    e.event_id::text,
                    e.event_title,
                    e.event_datetime,
                    v.venue_name,
                    v.city,
                    COALESCE(SUM(tc.quota), 0) AS total_quota,
                    COUNT(t.ticket_id) FILTER (
                        WHERE o.payment_status = 'Completed'
                    ) AS terjual
                FROM "EVENT" e
                JOIN "VENUE" v ON v.venue_id = e.venue_id
                LEFT JOIN "TICKET_CATEGORY" tc ON tc.tevent_id = e.event_id
                LEFT JOIN "TICKET" t ON t.tcategory_id = tc.category_id
                LEFT JOIN "ORDER" o ON o.order_id = t.torder_id
                WHERE e.organizer_id = %s::uuid
                  AND e.event_datetime > NOW()
                GROUP BY e.event_id, e.event_title, e.event_datetime, v.venue_name, v.city
                ORDER BY e.event_datetime ASC
                LIMIT 5
            """, [organizer_id])
            rows = cur.fetchall()
            performa_acara = []
            for r in rows:
                total_q = int(r[5]) if r[5] else 0
                terjual = int(r[6]) if r[6] else 0
                pct = round(terjual / total_q * 100) if total_q > 0 else 0
                performa_acara.append({
                    'event_id':       r[0],
                    'event_title':    r[1],
                    'event_datetime': r[2],
                    'venue_name':     r[3],
                    'city':           r[4],
                    'pct_terjual':    pct,
                    'terjual':        terjual,
                    'total_quota':    total_q,
                })
    finally:
        conn.close()

    def fmt_rupiah(val):
        if val >= 1_000_000:
            return f"Rp {val/1_000_000:.1f}M"
        return f"Rp {val:,}"

    return render(request, "main/dashboard_organizer.html", _ctx(
        request,
        total_acara_aktif=total_acara_aktif,
        total_tiket_terjual=total_tiket_terjual,
        total_revenue=fmt_rupiah(total_revenue),
        total_venue_mitra=total_venue_mitra,
        performa_acara=performa_acara,
    ))


def dashboard_customer(request):
    guard = _require_role(request, 'customer')
    if guard:
        return guard

    customer_id = request.session.get('customer_id')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Tiket aktif (order Completed atau Pending)
            cur.execute("""
                SELECT COUNT(t.ticket_id)
                FROM "TICKET" t
                JOIN "ORDER" o ON o.order_id = t.torder_id
                WHERE o.customer_id = %s::uuid
                  AND o.payment_status IN ('Completed', 'Pending')
            """, [customer_id])
            total_tiket_aktif = cur.fetchone()[0]

            # Total acara diikuti (distinct event dari tiket yang completed)
            cur.execute("""
                SELECT COUNT(DISTINCT tc.tevent_id)
                FROM "TICKET" t
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "ORDER" o ON o.order_id = t.torder_id
                WHERE o.customer_id = %s::uuid
                  AND o.payment_status = 'Completed'
            """, [customer_id])
            total_acara = cur.fetchone()[0]

            # Promo tersedia (promo yang belum habis use_limit)
            cur.execute("""
                SELECT COUNT(*)
                FROM "PROMOTION" p
                WHERE p.use_limit > (
                    SELECT COUNT(*) FROM "ORDER_PROMOTION" op WHERE op.promotion_id = p.promotion_id
                )
                AND p.end_date >= CURRENT_DATE
            """)
            total_promo = cur.fetchone()[0]

            # Total belanja (completed)
            cur.execute("""
                SELECT COALESCE(SUM(o.total_amount), 0)
                FROM "ORDER" o
                WHERE o.customer_id = %s::uuid
                  AND o.payment_status = 'Completed'
            """, [customer_id])
            total_belanja = int(cur.fetchone()[0])

            # Tiket mendatang (event di masa depan, max 5)
            cur.execute("""
                SELECT
                    e.event_title,
                    tc.category_name,
                    e.event_datetime,
                    v.venue_name,
                    v.city,
                    t.ticket_id::text
                FROM "TICKET" t
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                JOIN "VENUE" v ON v.venue_id = e.venue_id
                JOIN "ORDER" o ON o.order_id = t.torder_id
                WHERE o.customer_id = %s::uuid
                  AND o.payment_status IN ('Completed', 'Pending')
                  AND e.event_datetime > NOW()
                ORDER BY e.event_datetime ASC
                LIMIT 5
            """, [customer_id])
            rows = cur.fetchall()
            tiket_mendatang = [
                {
                    'event_title':   r[0],
                    'category_name': r[1],
                    'event_datetime': r[2],
                    'venue_name':    r[3],
                    'city':          r[4],
                    'ticket_id':     r[5],
                }
                for r in rows
            ]
    finally:
        conn.close()

    def fmt_rupiah(val):
        if val >= 1_000_000:
            return f"Rp {val/1_000_000:.1f}M"
        return f"Rp {val:,}"

    return render(request, "main/dashboard_customer.html", _ctx(
        request,
        total_tiket_aktif=total_tiket_aktif,
        total_acara=total_acara,
        total_promo=total_promo,
        total_belanja=fmt_rupiah(total_belanja),
        tiket_mendatang=tiket_mendatang,
    ))

def profile_organizer(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return guard

    organizer_id = request.session.get('organizer_id')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o."organizer_id"::text, o."organization_name", o."contact_email",
                       u."username", u."user_id"::text
                FROM "ORGANIZER" o
                JOIN "USER_ACCOUNT" u ON u."user_id" = o."user_id"
                WHERE o."organizer_id" = %s::uuid
            """, [organizer_id])
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return redirect('main:logout')

    return render(request, "main/profile_organizer.html", _ctx(
        request,
        profile_organizer_id=row[0],
        profile_orgname=row[1],
        profile_email=row[2] or '',
        profile_username=row[3],
        profile_userid=row[4],
    ))


@require_POST
def profile_organizer_update(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    organizer_id = request.session.get('organizer_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    org_name = (data.get('organization_name') or '').strip()
    email    = (data.get('contact_email') or '').strip()

    if not org_name:
        return JsonResponse({'success': False, 'error': 'Nama organizer wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "ORGANIZER"
                SET "organization_name" = %s, "contact_email" = %s
                WHERE "organizer_id" = %s::uuid
            """, [org_name, email or None, organizer_id])
        conn.commit()

        request.session['display_name'] = org_name
        request.session['username']     = org_name

        return JsonResponse({'success': True, 'organization_name': org_name, 'contact_email': email})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def profile_organizer_password(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    organizer_id = request.session.get('organizer_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    old_pw  = data.get('old_password', '')
    new_pw  = data.get('new_password', '')
    conf_pw = data.get('confirm_password', '')

    if not old_pw:
        return JsonResponse({'success': False, 'error': 'Password lama wajib diisi.'})
    if not new_pw or len(new_pw) < 8:
        return JsonResponse({'success': False, 'error': 'Password baru minimal 8 karakter.'})
    if new_pw != conf_pw:
        return JsonResponse({'success': False, 'error': 'Konfirmasi password tidak cocok.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u."user_id"::text, u."PASSWORD"
                FROM "USER_ACCOUNT" u
                JOIN "ORGANIZER" o ON o."user_id" = u."user_id"
                WHERE o."organizer_id" = %s::uuid
            """, [organizer_id])
            row = cur.fetchone()
            if not row or row[1] != old_pw:
                return JsonResponse({'success': False, 'error': 'Password lama salah.'})

            cur.execute("""
                UPDATE "USER_ACCOUNT" SET "PASSWORD" = %s
                WHERE "user_id" = %s::uuid
            """, [new_pw, row[0]])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()

def profile_customer(request):
    guard = _require_role(request, 'customer')
    if guard:
        return guard

    customer_id = request.session.get('customer_id')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c."customer_id"::text, c."full_name", c."phone_number",
                       u."username", u."user_id"::text
                FROM "CUSTOMER" c
                JOIN "USER_ACCOUNT" u ON u."user_id" = c."user_id"
                WHERE c."customer_id" = %s::uuid
            """, [customer_id])
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return redirect('main:logout')

    return render(request, "main/profile_customer.html", _ctx(
        request,
        profile_customer_id=row[0],
        profile_fullname=row[1],
        profile_phone=row[2] or '',
        profile_username=row[3],
        profile_userid=row[4],
    ))


@require_POST
def profile_customer_update(request):
    guard = _require_role(request, 'customer')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    customer_id = request.session.get('customer_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    full_name    = (data.get('full_name') or '').strip()
    phone_number = (data.get('phone_number') or '').strip()

    if not full_name:
        return JsonResponse({'success': False, 'error': 'Nama lengkap wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "CUSTOMER"
                SET "full_name" = %s, "phone_number" = %s
                WHERE "customer_id" = %s::uuid
            """, [full_name, phone_number or None, customer_id])
        conn.commit()

        request.session['display_name'] = full_name
        request.session['username']     = full_name

        return JsonResponse({'success': True, 'full_name': full_name, 'phone_number': phone_number})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def profile_customer_password(request):
    guard = _require_role(request, 'customer')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    customer_id = request.session.get('customer_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    old_pw  = data.get('old_password', '')
    new_pw  = data.get('new_password', '')
    conf_pw = data.get('confirm_password', '')

    if not old_pw:
        return JsonResponse({'success': False, 'error': 'Password lama wajib diisi.'})
    if not new_pw or len(new_pw) < 8:
        return JsonResponse({'success': False, 'error': 'Password baru minimal 8 karakter.'})
    if new_pw != conf_pw:
        return JsonResponse({'success': False, 'error': 'Konfirmasi password tidak cocok.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Ambil user_id via customer_id
            cur.execute("""
                SELECT u."user_id"::text, u."PASSWORD"
                FROM "USER_ACCOUNT" u
                JOIN "CUSTOMER" c ON c."user_id" = u."user_id"
                WHERE c."customer_id" = %s::uuid
            """, [customer_id])
            row = cur.fetchone()
            if not row or row[1] != old_pw:
                return JsonResponse({'success': False, 'error': 'Password lama salah.'})

            cur.execute("""
                UPDATE "USER_ACCOUNT" SET "PASSWORD" = %s
                WHERE "user_id" = %s::uuid
            """, [new_pw, row[0]])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()

def profile_admin(request):
    guard = _require_role(request, 'admin')
    if guard:
        return guard

    user_id = request.session.get('user_id')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "user_id"::text, "username"
                FROM "USER_ACCOUNT"
                WHERE "user_id" = %s::uuid
            """, [user_id])
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return redirect('main:logout')

    return render(request, "main/profile_admin.html", _ctx(
        request,
        profile_userid=row[0],
        profile_username=row[1],
    ))


@require_POST
def profile_admin_update(request):
    guard = _require_role(request, 'admin')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    user_id = request.session.get('user_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    new_username = (data.get('username') or '').strip()
    if not new_username:
        return JsonResponse({'success': False, 'error': 'Username wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Cek duplikat username
            cur.execute("""
                SELECT COUNT(*) FROM "USER_ACCOUNT"
                WHERE LOWER("username") = LOWER(%s)
                  AND "user_id" != %s::uuid
            """, [new_username, user_id])
            if cur.fetchone()[0] > 0:
                return JsonResponse({'success': False, 'error': 'Username sudah digunakan.'})

            cur.execute("""
                UPDATE "USER_ACCOUNT" SET "username" = %s
                WHERE "user_id" = %s::uuid
            """, [new_username, user_id])
        conn.commit()

        # Update session
        request.session['username'] = new_username
        request.session['display_name'] = new_username

        return JsonResponse({'success': True, 'username': new_username})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def profile_admin_password(request):
    guard = _require_role(request, 'admin')
    if guard:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    user_id = request.session.get('user_id')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    old_pw  = data.get('old_password', '')
    new_pw  = data.get('new_password', '')
    conf_pw = data.get('confirm_password', '')

    if not old_pw:
        return JsonResponse({'success': False, 'error': 'Password lama wajib diisi.'})
    if not new_pw or len(new_pw) < 8:
        return JsonResponse({'success': False, 'error': 'Password baru minimal 8 karakter.'})
    if new_pw != conf_pw:
        return JsonResponse({'success': False, 'error': 'Konfirmasi password tidak cocok.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "PASSWORD" FROM "USER_ACCOUNT"
                WHERE "user_id" = %s::uuid
            """, [user_id])
            row = cur.fetchone()
            if not row or row[0] != old_pw:
                return JsonResponse({'success': False, 'error': 'Password lama salah.'})

            cur.execute("""
                UPDATE "USER_ACCOUNT" SET "PASSWORD" = %s
                WHERE "user_id" = %s::uuid
            """, [new_pw, user_id])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()

def artist_list(request):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "artist_id"::text, "name", COALESCE("genre", '')
                FROM "ARTIST"
                ORDER BY "name" ASC
            """)
            rows = cur.fetchall()
        artists = [{'id': r[0], 'name': r[1], 'genre': r[2]} for r in rows]
    finally:
        conn.close()
    return render(request, "main/artist/artist_list.html", _ctx(request, artists_json=json.dumps(artists)))

# Venue Views
def fetch_all_venues():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "venue_id"::text, "venue_name", "capacity",
                       "address", "city", "seat_type"
                  FROM "VENUE"
              ORDER BY "venue_name" ASC
            """)
            rows = cur.fetchall()
        return [
            {
                'venue_id':   r[0],
                'venue_name': r[1],
                'capacity':   r[2],
                'address':    r[3],
                'city':       r[4],
                'seat_type':  r[5],
            }
            for r in rows
        ]
    finally:
        conn.close()

def venue_list(request):
    venues = fetch_all_venues()
    return render(request, "main/venue/venue_list.html", _ctx(
        request,
        venues=venues,
        venues_json=json.dumps(venues),
    ))


@require_POST
def venue_create(request):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    venue_name = (data.get('venue_name') or '').strip()
    address = (data.get('address') or '').strip()
    city = (data.get('city') or '').strip()
    seat_type = (data.get('seat_type') or '').strip()
    try:
        capacity = int(data.get('capacity') or 0)
    except (TypeError, ValueError):
        capacity = 0

    # Validasi sederhana sebelum sampai ke DB (bukan validasi business logic)
    if not (venue_name and address and city and seat_type and capacity > 0):
        return JsonResponse({
            'success': False,
            'error':   'Seluruh field wajib diisi dan kapasitas harus > 0.',
        })
 
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "VENUE"
                    ("venue_name", "capacity", "address", "city", "seat_type")
                VALUES (%s, %s, %s, %s, %s)
                RETURNING "venue_id"::text
            """, [venue_name, capacity, address, city, seat_type])
            new_id = cur.fetchone()[0]
        conn.commit()
        return JsonResponse({'success': True, 'venue_id': new_id})
    except psycopg2.Error as e:
        conn.rollback()
        # Pesan dari trg_check_duplicate_venue
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def venue_edit(request, venue_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    venue_name = (data.get('venue_name') or '').strip()
    address    = (data.get('address') or '').strip()
    city       = (data.get('city') or '').strip()
    seat_type  = (data.get('seat_type') or '').strip()
    try:
        capacity = int(data.get('capacity') or 0)
    except (TypeError, ValueError):
        capacity = 0
 
    if not (venue_name and address and city and seat_type and capacity > 0):
        return JsonResponse({
            'success': False,
            'error':   'Seluruh field wajib diisi dan kapasitas harus > 0.',
        })
 
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "VENUE"
                   SET "venue_name" = %s,
                       "capacity"   = %s,
                       "address"    = %s,
                       "city"       = %s,
                       "seat_type"  = %s
                 WHERE "venue_id"   = %s::uuid
            """, [venue_name, capacity, address, city, seat_type, str(venue_id)])
 
            if cur.rowcount == 0:
                conn.rollback()
                return JsonResponse({
                    'success': False,
                    'error':   'Venue tidak ditemukan.',
                })
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def venue_delete(request, venue_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "VENUE" WHERE "venue_id" = %s', [str(venue_id)])
            if cur.rowcount == 0:
                conn.rollback()
                return JsonResponse({'success': False, 'error': 'Venue tidak ditemukan.'})
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        # Pesan dari trigger prevent_venue_deletion
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


# Event Views
#  DATA LOADERS 
def _fetch_venues_brief():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "venue_id"::text, "venue_name", "city", "capacity"
                  FROM "VENUE"
              ORDER BY "venue_name" ASC
            """)
            return [
                {'venue_id': r[0], 'venue_name': r[1],
                 'city': r[2], 'capacity': r[3]}
                for r in cur.fetchall()
            ]
    finally:
        conn.close()
 
 
def _fetch_organizers_brief():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "organizer_id"::text, "organization_name"
                  FROM "ORGANIZER"
              ORDER BY "organization_name" ASC
            """)
            return [
                {'organizer_id': r[0], 'organization_name': r[1]}
                for r in cur.fetchall()
            ]
    finally:
        conn.close()
 
 
def _fetch_artists_brief():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "artist_id"::text, "name", COALESCE("genre", '')
                  FROM "ARTIST"
              ORDER BY "name" ASC
            """)
            return [
                {'artist_id': r[0], 'name': r[1], 'genre': r[2]}
                for r in cur.fetchall()
            ]
    finally:
        conn.close()
 
 
def _fetch_events_for_listing(organizer_filter=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            base_sql = """
                SELECT
                    e."event_id"::text,
                    e."event_title",
                    e."event_datetime",
                    v."venue_id"::text,
                    v."venue_name",
                    v."city",
                    v."seat_type",
                    o."organizer_id"::text,
                    o."organization_name"
                  FROM "EVENT" e
                  JOIN "VENUE"     v ON v."venue_id"     = e."venue_id"
                  JOIN "ORGANIZER" o ON o."organizer_id" = e."organizer_id"
            """
            params = []
            if organizer_filter:
                base_sql += ' WHERE o."organizer_id" = %s::uuid '
                params.append(str(organizer_filter))
            base_sql += ' ORDER BY e."event_datetime" ASC'
 
            cur.execute(base_sql, params)
            event_rows = cur.fetchall()
 
            events = []
            for r in event_rows:
                events.append({
                    'event_id':       r[0],
                    'event_title':    r[1],
                    'event_datetime': r[2].strftime('%Y-%m-%d %H:%M:%S') if r[2] else '',
                    'venue_id':       r[3],
                    'venue_name':     r[4],
                    'city':           r[5],
                    'seat_type':      r[6],
                    'organizer_id':   r[7],
                    'organization_name': r[8],
                    'artists':        [],
                    'categories':     [],
                    'min_price':      None,
                })
 
            if not events:
                return []
 
            event_ids = [e['event_id'] for e in events]
            ev_idx    = {e['event_id']: e for e in events}
 
            # Artists
            cur.execute("""
                SELECT ea."event_id"::text, a."artist_id"::text, a."name"
                  FROM "EVENT_ARTIST" ea
                  JOIN "ARTIST" a ON a."artist_id" = ea."artist_id"
                 WHERE ea."event_id"::text = ANY(%s)
              ORDER BY a."name"
            """, [event_ids])
            for ev_id, a_id, a_name in cur.fetchall():
                if ev_id in ev_idx:
                    ev_idx[ev_id]['artists'].append({'id': a_id, 'name': a_name})
 
            # Categories
            cur.execute("""
                SELECT "tevent_id"::text, "category_id"::text,
                       "category_name", "price", "quota"
                  FROM "TICKET_CATEGORY"
                 WHERE "tevent_id"::text = ANY(%s)
              ORDER BY "price"
            """, [event_ids])
            for ev_id, c_id, c_name, c_price, c_quota in cur.fetchall():
                if ev_id in ev_idx:
                    price_f = float(c_price or 0)
                    ev_idx[ev_id]['categories'].append({
                        'id':    c_id,
                        'name':  c_name,
                        'price': price_f,
                        'quota': c_quota,
                    })
                    cur_min = ev_idx[ev_id]['min_price']
                    if cur_min is None or price_f < cur_min:
                        ev_idx[ev_id]['min_price'] = price_f
 
        return events
    finally:
        conn.close()
 
 
def _fetch_event_for_form(event_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT "event_id"::text, "event_title", "event_datetime",
                       "venue_id"::text, "organizer_id"::text
                  FROM "EVENT"
                 WHERE "event_id" = %s::uuid
            """, [str(event_id)])
            row = cur.fetchone()
            if not row:
                return None
 
            ev = {
                'event_id':       row[0],
                'event_title':    row[1],
                'event_datetime': row[2],
                'venue_id':       row[3],
                'organizer_id':   row[4],
                'artists':        [],
                'categories':     [],
            }
 
            cur.execute("""
                SELECT a."artist_id"::text, a."name"
                  FROM "EVENT_ARTIST" ea
                  JOIN "ARTIST" a ON a."artist_id" = ea."artist_id"
                 WHERE ea."event_id" = %s::uuid
              ORDER BY a."name"
            """, [str(event_id)])
            ev['artists'] = [{'id': r[0], 'name': r[1]} for r in cur.fetchall()]
 
            cur.execute("""
                SELECT "category_id"::text, "category_name", "quota", "price"
                  FROM "TICKET_CATEGORY"
                 WHERE "tevent_id" = %s::uuid
              ORDER BY "price"
            """, [str(event_id)])
            ev['categories'] = [
                {'id': r[0], 'name': r[1], 'quota': r[2], 'price': float(r[3] or 0)}
                for r in cur.fetchall()
            ]
 
        return ev
    finally:
        conn.close()


def event_list(request):
    role = _current_role(request)
 
    # Bila belum login, kembalikan ke home
    if not role:
        return redirect('main:home')
 
    organizer_filter = None
    if role == 'organizer':
        organizer_filter = request.session.get('organizer_id')
 
    events = _fetch_events_for_listing(organizer_filter=organizer_filter)
 
    return render(request, 'main/event/event_list.html', _ctx(
        request,
        events_json=json.dumps(events),
    ))

def event_create(request):
    if not _require_manage(request):
        return redirect('main:event_list')
 
    if request.method == 'POST':
        return _event_save(request, event_id=None)
 
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=False,
        event_id='',
        venues_json=json.dumps(_fetch_venues_brief()),
        organizers_json=json.dumps(_fetch_organizers_brief()),
        artists_json=json.dumps(_fetch_artists_brief()),
        event_prefill_json='null',
    ))

def event_edit(request, event_id):
    if not _require_manage(request):
        return redirect('main:event_list')
 
    ev = _fetch_event_for_form(event_id)
    if not ev:
        messages.error(request, 'Event tidak ditemukan.')
        return redirect('main:event_list')
 
    role = _current_role(request)
    if role == 'organizer':
        my_org = request.session.get('organizer_id')
        if my_org != ev['organizer_id']:
            messages.error(
                request,
                'Anda hanya dapat mengedit event milik Anda sendiri.'
            )
            return redirect('main:event_list')
 
    if request.method == 'POST':
        return _event_save(request, event_id=str(event_id))
 
    # Bentuk prefill yang ramah-JS
    prefill = {
        'event_id':       ev['event_id'],
        'event_title':    ev['event_title'],
        'event_date':     ev['event_datetime'].strftime('%Y-%m-%d'),
        'event_time':     ev['event_datetime'].strftime('%H:%M'),
        'venue_id':       ev['venue_id'],
        'organizer_id':   ev['organizer_id'],
        'artists':        ev['artists'],
        'categories':     ev['categories'],
    }
 
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=True,
        event_id=str(event_id),
        venues_json=json.dumps(_fetch_venues_brief()),
        organizers_json=json.dumps(_fetch_organizers_brief()),
        artists_json=json.dumps(_fetch_artists_brief()),
        event_prefill_json=json.dumps(prefill),
    ))

def _event_save(request, event_id=None):
    is_edit = event_id is not None
    role    = _current_role(request)
 
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
 
    title        = (data.get('event_title') or '').strip()
    date_str     = (data.get('event_date') or '').strip()
    time_str     = (data.get('event_time') or '').strip()
    venue_id     = (data.get('venue_id') or '').strip()
    organizer_id = (data.get('organizer_id') or '').strip()
    artist_ids   = data.get('artists') or []
    categories   = data.get('categories') or []
 
    # Validasi field wajib
    if not (title and date_str and time_str and venue_id and organizer_id):
        return JsonResponse({
            'success': False,
            'error':   'Judul, tanggal, waktu, venue, dan organizer wajib diisi.'
        })
 
    # Sesuai spec: setiap event WAJIB punya minimal 1 artist.
    if not isinstance(artist_ids, list) or len(artist_ids) == 0:
        return JsonResponse({
            'success': False,
            'error':   'Event harus memiliki minimal satu artist.'
        })
 
    # Filter kategori yang valid (nama tidak kosong, quota>0, price>=0).
    clean_categories = []
    for c in categories:
        cname = (c.get('category_name') or '').strip()
        try:
            quota = int(c.get('quota') or 0)
            price = float(c.get('price') or 0)
        except (TypeError, ValueError):
            quota, price = 0, 0
        if cname and quota > 0 and price >= 0:
            clean_categories.append({'name': cname, 'quota': quota, 'price': price})
 
    if not clean_categories:
        return JsonResponse({
            'success': False,
            'error':   'Event harus memiliki minimal satu kategori tiket.'
        })
 
    event_datetime = f"{date_str} {time_str}:00"
 
    # Filtered-by-Id untuk Organizer 
    if role == 'organizer':
        my_org = request.session.get('organizer_id')
        if not my_org:
            return JsonResponse({
                'success': False,
                'error':   'Sesi organizer tidak valid, silakan login ulang.'
            }, status=403)
        organizer_id = my_org
 
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1) Capacity check: total quota <= venue capacity 
            cur.execute('SELECT "capacity" FROM "VENUE" WHERE "venue_id" = %s::uuid',
                        [venue_id])
            row = cur.fetchone()
            if not row:
                conn.rollback()
                return JsonResponse({'success': False, 'error': 'Venue tidak ditemukan.'})
            venue_capacity = int(row[0])
            total_quota    = sum(c['quota'] for c in clean_categories)
            if total_quota > venue_capacity:
                conn.rollback()
                return JsonResponse({
                    'success': False,
                    'error':   (f'Total kuota kategori tiket ({total_quota}) '
                                f'melebihi kapasitas venue ({venue_capacity}).')
                })
 
            # 2) INSERT / UPDATE EVENT 
            if is_edit:
                # Untuk organizer, double-check ownership langsung di DB:
                if role == 'organizer':
                    cur.execute("""
                        SELECT "organizer_id"::text
                          FROM "EVENT"
                         WHERE "event_id" = %s::uuid
                    """, [event_id])
                    e_row = cur.fetchone()
                    if not e_row or e_row[0] != request.session.get('organizer_id'):
                        conn.rollback()
                        return JsonResponse({
                            'success': False,
                            'error':   'Anda tidak berhak mengedit event ini.'
                        }, status=403)
 
                cur.execute("""
                    UPDATE "EVENT"
                       SET "event_title"    = %s,
                           "event_datetime" = %s,
                           "venue_id"       = %s::uuid,
                           "organizer_id"   = %s::uuid
                     WHERE "event_id" = %s::uuid
                """, [title, event_datetime, venue_id, organizer_id, event_id])
                if cur.rowcount == 0:
                    conn.rollback()
                    return JsonResponse({
                        'success': False,
                        'error':   'Event tidak ditemukan.'
                    })
                final_event_id = event_id
            else:
                cur.execute("""
                    INSERT INTO "EVENT"
                        ("event_title", "event_datetime", "venue_id", "organizer_id")
                    VALUES (%s, %s, %s::uuid, %s::uuid)
                    RETURNING "event_id"::text
                """, [title, event_datetime, venue_id, organizer_id])
                final_event_id = cur.fetchone()[0]
 
            # 3) Sinkronisasi EVENT_ARTIST

            if is_edit:
                cur.execute('DELETE FROM "EVENT_ARTIST" WHERE "event_id" = %s::uuid',
                            [final_event_id])
 
            for a_id in artist_ids:
                cur.execute("""
                    INSERT INTO "EVENT_ARTIST" ("event_id", "artist_id")
                    VALUES (%s::uuid, %s::uuid)
                """, [final_event_id, a_id])
 
            # 4) Sinkronisasi TICKET_CATEGORY 

            if is_edit:
                cur.execute("""
                    DELETE FROM "TICKET_CATEGORY"
                     WHERE "tevent_id" = %s::uuid
                       AND "category_id" NOT IN (
                           SELECT DISTINCT "tcategory_id" FROM "TICKET"
                       )
                """, [final_event_id])
 
            for c in clean_categories:
                cur.execute("""
                    INSERT INTO "TICKET_CATEGORY"
                        ("category_name", "quota", "price", "tevent_id")
                    VALUES (%s, %s, %s, %s::uuid)
                """, [c['name'], c['quota'], c['price'], final_event_id])
 
        conn.commit()
        return JsonResponse({'success': True, 'event_id': final_event_id})
 
    except psycopg2.Error as e:
        conn.rollback()
        # Pesan dari trigger validate_event_artist atau constraint DB lain.
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()

def ticket_category_list(request):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SET search_path TO "TIKTAKTUK", public;')  # ← TAMBAH INI
            
            cur.execute("""
                SELECT 
                    tc."category_id"::text,
                    tc."category_name",
                    tc."quota",
                    tc."price",
                    tc."tevent_id"::text,
                    e."event_title"
                FROM "TICKET_CATEGORY" tc
                JOIN "EVENT" e ON e."event_id" = tc."tevent_id"
                ORDER BY e."event_title", tc."category_name"
            """)
            rows = cur.fetchall()
            categories = [
                {
                    'id': r[0],
                    'name': r[1],
                    'quota': int(r[2]),
                    'price': float(r[3]),
                    'event_id': r[4],
                    'event_title': r[5]
                }
                for r in rows
            ]

            cur.execute("""
                SELECT "event_id"::text, "event_title"
                FROM "EVENT"
                ORDER BY "event_title"
            """)
            events = [{'id': r[0], 'title': r[1]} for r in cur.fetchall()]

    finally:
        conn.close()

    return render(request, 'main/ticket_category/category_list.html', _ctx(
        request,
        categories_json=json.dumps(categories),
        events_json=json.dumps(events),
    ))

@require_POST
def artist_create(request):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    name  = (data.get('name') or '').strip()
    genre = (data.get('genre') or '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Nama artis wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "ARTIST" ("name", "genre")
                VALUES (%s, %s) RETURNING "artist_id"::text
            """, [name, genre or None])
            new_id = cur.fetchone()[0]
        conn.commit()
        return JsonResponse({'success': True, 'id': new_id, 'name': name, 'genre': genre})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def artist_edit(request, artist_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    name  = (data.get('name') or '').strip()
    genre = (data.get('genre') or '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Nama artis wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "ARTIST" SET "name" = %s, "genre" = %s
                WHERE "artist_id" = %s::uuid
            """, [name, genre or None, str(artist_id)])
        conn.commit()
        return JsonResponse({'success': True, 'name': name, 'genre': genre})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def artist_delete(request, artist_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "ARTIST" WHERE "artist_id" = %s::uuid', [str(artist_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def ticket_category_create(request):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    name     = (data.get('category_name') or '').strip()
    event_id = (data.get('event_id') or '').strip()
    try:
        quota = int(data.get('quota') or 0)
        price = float(data.get('price') or 0)
    except (TypeError, ValueError):
        quota, price = 0, 0

    if not (name and event_id and quota > 0 and price >= 0):
        return JsonResponse({'success': False, 'error': 'Semua field wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "TICKET_CATEGORY" ("category_name", "quota", "price", "tevent_id")
                VALUES (%s, %s, %s, %s::uuid) RETURNING "category_id"::text
            """, [name, quota, price, event_id])
            new_id = cur.fetchone()[0]
        conn.commit()
        return JsonResponse({'success': True, 'id': new_id})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def ticket_category_edit(request, category_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    name     = (data.get('category_name') or '').strip()
    event_id = (data.get('event_id') or '').strip()
    try:
        quota = int(data.get('quota') or 0)
        price = float(data.get('price') or 0)
    except (TypeError, ValueError):
        quota, price = 0, 0

    if not (name and event_id and quota > 0 and price >= 0):
        return JsonResponse({'success': False, 'error': 'Semua field wajib diisi.'})

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "TICKET_CATEGORY"
                SET "category_name" = %s, "quota" = %s, "price" = %s, "tevent_id" = %s::uuid
                WHERE "category_id" = %s::uuid
            """, [name, quota, price, event_id, str(category_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()


@require_POST
def ticket_category_delete(request, category_id):
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "TICKET_CATEGORY" WHERE "category_id" = %s::uuid', [str(category_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        return JsonResponse({'success': False, 'error': extract_pg_error(e)})
    finally:
        conn.close()

def my_tickets(request):
    guard = _require_role(request, 'customer')
    if guard:
        return guard

    customer_id = request.session.get('customer_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.ticket_id::text,
                    t.ticket_code,
                    e.event_title,
                    tc.category_name,
                    e.event_datetime,
                    v.venue_name,
                    v.city,
                    tc.price,
                    o.order_id::text,
                    c.full_name,
                    CASE WHEN hr.seat_id IS NOT NULL THEN
                        s.section || ' - Baris ' || s.row_number || ' No.' || s.seat_number
                    ELSE '—' END AS seat_info
                FROM "TICKET" t
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                JOIN "VENUE" v ON v.venue_id = e.venue_id
                JOIN "ORDER" o ON o.order_id = t.torder_id
                JOIN "CUSTOMER" c ON c.customer_id = o.customer_id
                LEFT JOIN "HAS_RELATIONSHIP" hr ON hr.ticket_id = t.ticket_id
                LEFT JOIN "SEAT" s ON s.seat_id = hr.seat_id
                WHERE o.customer_id = %s::uuid
                ORDER BY e.event_datetime DESC
            """, [customer_id])
            rows = cur.fetchall()
            tikets = [
                {
                    'ticket_id':     r[0],
                    'ticket_code':   r[1],
                    'event_title':   r[2],
                    'category_name': r[3],
                    'event_datetime': r[4].strftime('%d %b %Y, %H:%M') if r[4] else '—',
                    'venue_name':    r[5],
                    'city':          r[6],
                    'price':         f"Rp {int(r[7]):,}".replace(',', '.') if r[7] else '—',
                    'order_id':      r[8],
                    'pelanggan':     r[9],
                    'seat_info':     r[10],
                }
                for r in rows
            ]
    finally:
        conn.close()

    return render(request, "main/ticket/my_tickets.html", _ctx(
        request,
        tikets=tikets,
        tikets_json=json.dumps(tikets),
    ))


def manajemen_tiket_admin(request):
    guard = _require_role(request, 'admin')
    if guard:
        return guard
    return _manajemen_tiket(request)


def manajemen_tiket_organizer(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return guard
    return _manajemen_tiket(request)


def _manajemen_tiket(request):
    role = _current_role(request)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Semua tiket (admin lihat semua, organizer lihat semua juga per spec FE)
            cur.execute("""
                SELECT
                    t.ticket_id::text,
                    t.ticket_code,
                    e.event_title,
                    tc.category_name,
                    e.event_datetime,
                    v.venue_name,
                    v.city,
                    tc.price,
                    o.order_id::text,
                    c.full_name,
                    CASE WHEN hr.seat_id IS NOT NULL THEN
                        s.section || ' - Baris ' || s.row_number || ' No.' || s.seat_number
                    ELSE '—' END AS seat_info
                FROM "TICKET" t
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                JOIN "VENUE" v ON v.venue_id = e.venue_id
                JOIN "ORDER" o ON o.order_id = t.torder_id
                JOIN "CUSTOMER" c ON c.customer_id = o.customer_id
                LEFT JOIN "HAS_RELATIONSHIP" hr ON hr.ticket_id = t.ticket_id
                LEFT JOIN "SEAT" s ON s.seat_id = hr.seat_id
                ORDER BY e.event_datetime DESC
            """)
            rows = cur.fetchall()
            tikets = [
                {
                    'ticket_id':     r[0],
                    'ticket_code':   r[1],
                    'event_title':   r[2],
                    'category_name': r[3],
                    'event_datetime': r[4].strftime('%d %b %Y, %H:%M') if r[4] else '—',
                    'venue_name':    r[5],
                    'city':          r[6],
                    'price':         f"Rp {int(r[7]):,}".replace(',', '.') if r[7] else '—',
                    'order_id':      r[8],
                    'pelanggan':     r[9],
                    'seat_info':     r[10],
                }
                for r in rows
            ]

            # Data untuk modal tambah tiket: semua order
            cur.execute("""
                SELECT
                    o.order_id::text,
                    c.full_name,
                    e.event_title,
                    e.event_id::text,
                    v.seat_type
                FROM "ORDER" o
                JOIN "CUSTOMER" c ON c.customer_id = o.customer_id
                JOIN "TICKET" t ON t.torder_id = o.order_id
                JOIN "TICKET_CATEGORY" tc ON tc.category_id = t.tcategory_id
                JOIN "EVENT" e ON e.event_id = tc.tevent_id
                JOIN "VENUE" v ON v.venue_id = e.venue_id
                GROUP BY o.order_id, c.full_name, e.event_title, e.event_id, v.seat_type
                ORDER BY o.order_id
            """)
            orders_raw = cur.fetchall()
            orders = [
                {
                    'order_id':    r[0],
                    'customer':    r[1],
                    'event_title': r[2],
                    'event_id':    r[3],
                    'seat_type':   r[4],
                }
                for r in orders_raw
            ]

            # Kategori tiket per event
            cur.execute("""
                SELECT
                    tc.category_id::text,
                    tc.category_name,
                    tc.price,
                    tc.quota,
                    tc.tevent_id::text,
                    COUNT(t.ticket_id) AS terjual
                FROM "TICKET_CATEGORY" tc
                LEFT JOIN "TICKET" t ON t.tcategory_id = tc.category_id
                GROUP BY tc.category_id, tc.category_name, tc.price, tc.quota, tc.tevent_id
            """)
            cats_raw = cur.fetchall()
            categories = [
                {
                    'category_id':   r[0],
                    'category_name': r[1],
                    'price':         float(r[2]) if r[2] else 0,
                    'quota':         r[3],
                    'event_id':      r[4],
                    'terjual':       r[5],
                    'full':          r[5] >= r[3],
                }
                for r in cats_raw
            ]

            # Seat tersedia (belum di-assign)
            cur.execute("""
                SELECT
                    s.seat_id::text,
                    s.section,
                    s.row_number,
                    s.seat_number,
                    s.venue_id::text,
                    v.venue_name
                FROM "SEAT" s
                JOIN "VENUE" v ON v.venue_id = s.venue_id
                WHERE s.seat_id NOT IN (
                    SELECT seat_id FROM "HAS_RELATIONSHIP"
                )
                ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
            """)
            seats_raw = cur.fetchall()
            seats_available = [
                {
                    'seat_id':   r[0],
                    'section':   r[1],
                    'row':       r[2],
                    'number':    r[3],
                    'venue_id':  r[4],
                    'venue_name': r[5],
                }
                for r in seats_raw
            ]

    finally:
        conn.close()

    return render(request, "main/ticket/manajemen_tiket.html", _ctx(
        request,
        tikets=tikets,
        tikets_json=json.dumps(tikets),
        orders_json=json.dumps(orders),
        categories_json=json.dumps(categories),
        seats_available_json=json.dumps(seats_available),
    ))


def seat_admin(request):
    guard = _require_role(request, 'admin')
    if guard:
        return guard
    return _seat_view(request)


def seat_organizer(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return guard
    return _seat_view(request)


def _seat_view(request):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    s.seat_id::text,
                    s.section,
                    s.row_number,
                    s.seat_number,
                    v.venue_id::text,
                    v.venue_name,
                    CASE WHEN hr.seat_id IS NOT NULL THEN 'terisi' ELSE 'tersedia' END AS status
                FROM "SEAT" s
                JOIN "VENUE" v ON v.venue_id = s.venue_id
                LEFT JOIN "HAS_RELATIONSHIP" hr ON hr.seat_id = s.seat_id
                ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
            """)
            rows = cur.fetchall()
            seats = [
                {
                    'seat_id':    r[0],
                    'section':    r[1],
                    'row_number': r[2],
                    'seat_number': r[3],
                    'venue_id':   r[4],
                    'venue_name': r[5],
                    'status':     r[6],
                }
                for r in rows
            ]

            cur.execute('SELECT "venue_id"::text, "venue_name" FROM "VENUE" ORDER BY "venue_name"')
            venues = [{'venue_id': r[0], 'venue_name': r[1]} for r in cur.fetchall()]

    finally:
        conn.close()

    return render(request, 'main/seat/seat.html', _ctx(
        request,
        seats=seats,
        seats_json=json.dumps(seats),
        venues=venues,
        venues_json=json.dumps(venues),
    ))

# Order Views
def order_list(request):
    """
    Daftar order — tampilan berbeda per role:
    - Admin   : semua order
    - Organizer : order dari event yang dia kelola
    - Customer  : order miliknya sendiri
    """
    role = _resolve_role(request)
    if not role:
        return redirect('main:home')
 
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Base query per role
        if role == 'admin':
            query = """
                SELECT
                    o.order_id,
                    o.order_date,
                    o.payment_status,
                    o.total_amount,
                    c.full_name AS customer_name,
                    LEFT(c.full_name, 1) AS initial
                FROM "ORDER" o
                JOIN CUSTOMER c ON c.customer_id = o.customer_id
                WHERE 1=1
            """
            params = []
 
        elif role == 'organizer':
            organizer_id = request.session.get('organizer_id')
            query = """
                SELECT DISTINCT
                    o.order_id,
                    o.order_date,
                    o.payment_status,
                    o.total_amount,
                    c.full_name AS customer_name,
                    LEFT(c.full_name, 1) AS initial
                FROM "ORDER" o
                JOIN CUSTOMER c ON c.customer_id = o.customer_id
                JOIN TICKET t ON t.torder_id = o.order_id
                JOIN TICKET_CATEGORY tc ON tc.category_id = t.tcategory_id
                JOIN EVENT e ON e.event_id = tc.tevent_id
                JOIN ORGANIZER org ON org.organizer_id = e.organizer_id
                WHERE org.organizer_id = %s
            """
            params = [organizer_id]
 
        else:  # customer
            customer_id = request.session.get('customer_id')
            query = """
                SELECT
                    o.order_id,
                    o.order_date,
                    o.payment_status,
                    o.total_amount,
                    NULL AS customer_name,
                    NULL AS initial
                FROM "ORDER" o
                JOIN CUSTOMER c ON c.customer_id = o.customer_id
                JOIN USER_ACCOUNT ua ON ua.user_id = c.user_id
                WHERE c.customer_id = %s
            """
            params = [customer_id]
 
        # Filter search
        if search:
            query += " AND CAST(o.order_id AS TEXT) ILIKE %s"
            params.append(f'%{search}%')
 
        # Filter status
        if status_filter:
            query += " AND LOWER(o.payment_status) = LOWER(%s)"
            params.append(status_filter)
 
        query += " ORDER BY o.order_date DESC"
 
        cur.execute(query, params)
        orders = cur.fetchall()
 
        # Hitung statistik
        total = len(orders)
        lunas = sum(1 for o in orders if o['payment_status'].lower() == 'completed')
        pending = sum(1 for o in orders if o['payment_status'].lower() == 'pending')
        total_revenue = sum(o['total_amount'] for o in orders if o['payment_status'].lower() == 'paid')
 
        cur.close()
        conn.close()
 
        ctx = _ctx(request,
            orders=orders,
            total=total,
            lunas=lunas,
            pending=pending,
            total_revenue=total_revenue,
            search=search,
            status_filter=status_filter,
        )
        return render(request, 'main/order/order_list.html', ctx)
 
    except Exception as e:
        messages.error(request, str(e))
        return render(request, 'main/order/order_list.html', _ctx(request, orders=[]))
 
 
def order_update(request, order_id):
    """Update payment_status — hanya Admin"""
    if _resolve_role(request) != 'admin':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:order_list')
 
    if request.method == 'POST':
        new_status = request.POST.get('payment_status')
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE "ORDER"
                SET payment_status = %s
                WHERE order_id = %s
            """, (new_status, order_id))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, f'Status order berhasil diubah menjadi {new_status}.')
        except Exception as e:
            messages.error(request, str(e))
 
    return redirect('main:order_list')
 
 
def order_delete(request, order_id):
    """Delete order — hanya Admin"""
    if _resolve_role(request) != 'admin':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:order_list')
 
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Hapus ORDER_PROMOTION dulu (foreign key)
            cur.execute("DELETE FROM ORDER_PROMOTION WHERE order_id = %s", (order_id,))
            # Hapus TICKET dulu (foreign key)
            cur.execute("DELETE FROM TICKET WHERE torder_id = %s", (order_id,))
            # Hapus ORDER
            cur.execute('DELETE FROM "ORDER" WHERE order_id = %s', (order_id,))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Order berhasil dihapus.')
        except Exception as e:
            messages.error(request, str(e))
 
    return redirect('main:order_list')
 
 
def order_checkout(request, event_id):
    """
    Halaman checkout tiket — hanya Customer.
    GET  : tampilkan halaman dengan info event & kategori tiket
    POST : buat order baru
    """
    role = _resolve_role(request)
    if role != 'customer':
        return redirect('main:home')
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Ambil info event
        cur.execute("""
            SELECT e.event_id, e.event_title, e.event_datetime,
                   v.venue_name, v.city, v.address
            FROM EVENT e
            JOIN VENUE v ON v.venue_id = e.venue_id
            WHERE e.event_id = %s
        """, (event_id,))
        event = cur.fetchone()
 
        if not event:
            messages.error(request, 'Event tidak ditemukan.')
            return redirect('main:event_list')
 
        # Ambil kategori tiket + sisa kuota
        cur.execute("""
            SELECT
                tc.category_id,
                tc.category_name,
                tc.price,
                tc.quota,
                tc.quota - COUNT(t.ticket_id) AS remaining_quota
            FROM TICKET_CATEGORY tc
            LEFT JOIN TICKET t ON t.tcategory_id = tc.category_id
            WHERE tc.tevent_id = %s
            GROUP BY tc.category_id, tc.category_name, tc.price, tc.quota
            ORDER BY tc.price DESC
        """, (event_id,))
        categories = cur.fetchall()
 
        # Ambil daftar kursi venue
        cur.execute("""
            SELECT s.seat_id, s.section, s.row_number, s.seat_number
            FROM SEAT s
            JOIN EVENT e ON e.venue_id = s.venue_id
            WHERE e.event_id = %s
            ORDER BY s.section, s.row_number, s.seat_number
        """, (event_id,))
        seats = cur.fetchall()
 
        # Ambil artis event
        cur.execute("""
            SELECT a.name
            FROM ARTIST a
            JOIN EVENT_ARTIST ea ON ea.artist_id = a.artist_id
            WHERE ea.event_id = %s
        """, (event_id,))
        artists = cur.fetchall()
 
        if request.method == 'POST':
            category_id   = request.POST.get('category_id')
            qty           = int(request.POST.get('qty', 1))
            seat_ids      = request.POST.getlist('seat_ids')  # opsional
            promo_code    = request.POST.get('promo_code', '').strip()
            customer_id   = request.session.get('customer_id')
 
            # Hitung total amount
            cur.execute("SELECT price FROM TICKET_CATEGORY WHERE category_id = %s", (category_id,))
            cat = cur.fetchone()
            if not cat:
                messages.error(request, 'Kategori tiket tidak ditemukan.')
                return redirect('main:order_checkout', event_id=event_id)
 
            total_amount = cat['price'] * qty
            discount = 0
 
            # Cek promo (preview diskon sebelum trigger jalan)
            promotion_id = None
            if promo_code:
                cur.execute("""
                    SELECT promotion_id, promo_code, discount_type, discount_value
                    FROM PROMOTION
                    WHERE UPPER(promo_code) = UPPER(%s)
                """, (promo_code,))
                promo = cur.fetchone()
                if promo:
                    promotion_id = promo['promotion_id']
                    if promo['discount_type'].upper() == 'PERCENTAGE':
                        discount = total_amount * (promo['discount_value'] / 100)
                    else:
                        discount = promo['discount_value']
                    total_amount = max(0, total_amount - discount)
 
            new_order_id = uuid.uuid4()
 
            # INSERT ORDER
            cur.execute("""
                INSERT INTO "ORDER" (order_id, order_date, payment_status, total_amount, customer_id)
                VALUES (%s, NOW(), 'Pending', %s, %s)
            """, (new_order_id, total_amount, customer_id))
 
            # INSERT TICKET per qty
            for _ in range(qty):
                ticket_id   = uuid.uuid4()
                ticket_code = f"TKT-{str(ticket_id)[:8].upper()}"
                cur.execute("""
                    INSERT INTO TICKET (ticket_id, ticket_code, tcategory_id, torder_id)
                    VALUES (%s, %s, %s, %s)
                """, (ticket_id, ticket_code, category_id, new_order_id))
 
            # INSERT HAS_RELATIONSHIP (seat) jika dipilih
            for seat_id in seat_ids:
                cur.execute("""
                    INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id)
                    VALUES (%s, %s)
                """, (seat_id, ticket_id))
 
            # INSERT ORDER_PROMOTION — trigger otomatis validasi di sini
            if promotion_id:
                op_id = uuid.uuid4()
                try:
                    cur.execute("""
                        INSERT INTO ORDER_PROMOTION (order_promotion_id, promotion_id, order_id)
                        VALUES (%s, %s, %s)
                    """, (op_id, promotion_id, new_order_id))
                except Exception as trigger_err:
                    conn.rollback()
                    messages.error(request, str(trigger_err))
                    cur.close()
                    conn.close()
                    return render(request, 'main/order/order_checkout.html', _ctx(
                        request, event=event, categories=categories,
                        seats=seats, artists=artists, event_id=event_id
                    ))
 
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Pemesanan berhasil! Order ID: ' + str(new_order_id)[:8].upper())
            return redirect('main:order_list')
 
        cur.close()
        conn.close()
 
        return render(request, 'main/order/order_checkout.html', _ctx(
            request,
            event=event,
            categories=categories,
            seats=seats,
            artists=artists,
            event_id=event_id,
        ))
 
    except Exception as e:
        messages.error(request, str(e))
        return redirect('main:event_list')
 
 
# Promotion Views
 
def promotion_list(request):
    """
    Daftar promosi — semua role bisa lihat.
    Admin bisa Create, Update, Delete.
    """
    role = _resolve_role(request)
    search = request.GET.get('search', '').strip()
    tipe_filter = request.GET.get('tipe', '').strip()
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        query = """
            SELECT
                p.promotion_id,
                p.promo_code,
                p.discount_type,
                p.discount_value,
                p.start_date,
                p.end_date,
                p.use_limit,
                COUNT(op.order_promotion_id) AS usage_count
            FROM PROMOTION p
            LEFT JOIN ORDER_PROMOTION op ON op.promotion_id = p.promotion_id
            WHERE 1=1
        """
        params = []
 
        if search:
            query += " AND p.promo_code ILIKE %s"
            params.append(f'%{search}%')
 
        if tipe_filter:
            query += " AND UPPER(p.discount_type) = UPPER(%s)"
            params.append(tipe_filter)
 
        query += " GROUP BY p.promotion_id ORDER BY p.start_date DESC"
 
        cur.execute(query, params)
        promotions = cur.fetchall()
 
        # Statistik
        total_promo = len(promotions)
        total_penggunaan = sum(p['usage_count'] for p in promotions)
        tipe_persentase = sum(1 for p in promotions if p['discount_type'].upper() == 'PERCENTAGE')
 
        cur.close()
        conn.close()
 
        ctx = _ctx(request,
            role=role,
            promotions=promotions,
            total_promo=total_promo,
            total_penggunaan=total_penggunaan,
            tipe_persentase=tipe_persentase,
            search=search,
            tipe_filter=tipe_filter,
        )
        return render(request, 'main/promotion/promotion_list.html', ctx)
 
    except Exception as e:
        messages.error(request, str)
        return render(request, 'main/promotion/promotion_list.html', _ctx(request, promotions=[]))
 
 
def promotion_create(request):
    """Buat promo baru — hanya Admin"""
    if _resolve_role(request) != 'admin':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:promotion_list')
 
    if request.method == 'POST':
        promo_code     = request.POST.get('promo_code', '').strip().upper()
        discount_type  = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        start_date     = request.POST.get('start_date')
        end_date       = request.POST.get('end_date')
        use_limit    = request.POST.get('use_limit')
 
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO PROMOTION
                    (promotion_id, promo_code, discount_type, discount_value, start_date, end_date, use_limit)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
            """, (
                uuid.uuid4(), promo_code, discount_type,
                discount_value, start_date, end_date, use_limit
            ))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, f'Promo "{promo_code}" berhasil dibuat.')
        except Exception as e:
            messages.error(request, str(e))
 
    return redirect('main:promotion_list')
 
 
def promotion_update(request, promotion_id):
    """Update promo — hanya Admin"""
    if _resolve_role(request) != 'admin':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:promotion_list')
 
    if request.method == 'POST':
        promo_code     = request.POST.get('promo_code', '').strip().upper()
        discount_type  = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        start_date     = request.POST.get('start_date')
        end_date       = request.POST.get('end_date')
        use_limit    = request.POST.get('use_limit')
 
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE PROMOTION
                SET promo_code = %s,
                    discount_type = %s,
                    discount_value = %s,
                    start_date = %s,
                    end_date = %s,
                    use_limit = %s
                WHERE promotion_id = %s
            """, (
                promo_code, discount_type, discount_value,
                start_date, end_date, use_limit, promotion_id
            ))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, f'Promo "{promo_code}" berhasil diperbarui.')
        except Exception as e:
            messages.error(request, str(e))
 
    return redirect('main:promotion_list')
 
 
def promotion_delete(request, promotion_id):
    """Delete promo — hanya Admin"""
    if _resolve_role(request) != 'admin':
        messages.error(request, 'Akses ditolak.')
        return redirect('main:promotion_list')
 
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Hapus ORDER_PROMOTION dulu (foreign key)
            cur.execute("DELETE FROM ORDER_PROMOTION WHERE promotion_id = %s", (promotion_id,))
            cur.execute("DELETE FROM PROMOTION WHERE promotion_id = %s", (promotion_id,))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Promo berhasil dihapus.')
        except Exception as e:
            messages.error(request, str(e))
 
    return redirect('main:promotion_list')
 
 
def promotion_validate(request):
    """
    AJAX endpoint — validasi kode promo saat customer mengetik di checkout.
    Return JSON: { valid, discount_type, discount_value, message }
    """
    promo_code = request.GET.get('code', '').strip()
    event_id   = request.GET.get('event_id', '').strip()
 
    if not promo_code:
        return JsonResponse({'valid': False, 'message': 'Kode promo kosong.'})
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute("""
            SELECT p.promotion_id, p.promo_code, p.discount_type,
                   p.discount_value, p.start_date, p.end_date, p.use_limit,
                   COUNT(op.order_promotion_id) AS usage_count
            FROM PROMOTION p
            LEFT JOIN ORDER_PROMOTION op ON op.promotion_id = p.promotion_id
            WHERE UPPER(p.promo_code) = UPPER(%s)
            GROUP BY p.promotion_id
        """, (promo_code,))
        promo = cur.fetchone()
 
        if not promo:
            return JsonResponse({'valid': False, 'message': f'Kode promo "{promo_code}" tidak ditemukan.'})
 
        if promo['usage_count'] >= promo['use_limit']:
            return JsonResponse({'valid': False, 'message': f'Promotion "{promo_code}" telah mencapai batas maksimum penggunaan.'})
 
        # Cek tanggal event dalam periode promo
        if event_id:
            cur.execute("SELECT event_datetime FROM EVENT WHERE event_id = %s", (event_id,))
            event = cur.fetchone()
            if event:
                event_date = event['event_datetime'].date()
                if not (promo['start_date'] <= event_date <= promo['end_date']):
                    return JsonResponse({'valid': False, 'message': f'Promotion "{promo_code}" tidak berlaku untuk tanggal event ini.'})
 
        cur.close()
        conn.close()
 
        return JsonResponse({
            'valid': True,
            'discount_type': promo['discount_type'],
            'discount_value': float(promo['discount_value']),
            'message': f'Kode promo valid! Diskon {"{}%".format(promo["discount_value"]) if promo["discount_type"].upper() == "PERCENTAGE" else "Rp {:,.0f}".format(promo["discount_value"])}',
        })
 
    except Exception as e:
        return JsonResponse({'valid': False, 'message': str(e)})
 
# Seat Views
def seat_delete(request, seat_id):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "SEAT" WHERE "seat_id" = %s', [str(seat_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        raw = e.pgerror or str(e)
        msg = raw.strip().split('\n')[0].replace('ERROR:  ', '').replace('ERROR: ', '')
        return JsonResponse({'success': False, 'error': msg})
    finally:
        conn.close()

def seat_create(request):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    import json as _json
    data = _json.loads(request.body)
    venue_id    = data.get('venue_id')
    section     = data.get('section', '').strip()
    row_number  = data.get('row_number', '').strip()
    seat_number = data.get('seat_number', '').strip()
    if not all([venue_id, section, row_number, seat_number]):
        return JsonResponse({'success': False, 'error': 'Semua field wajib diisi.'})
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "SEAT" ("venue_id", "section", "row_number", "seat_number")
                VALUES (%s, %s, %s, %s)
                RETURNING "seat_id"::text
            """, [venue_id, section, row_number, seat_number])
            seat_id = cur.fetchone()[0]
        conn.commit()
        return JsonResponse({'success': True, 'seat_id': seat_id})
    except psycopg2.Error as e:
        conn.rollback()
        raw = e.pgerror or str(e)
        msg = raw.strip().split('\n')[0].replace('ERROR:  ', '').replace('ERROR: ', '')
        return JsonResponse({'success': False, 'error': msg})
    finally:
        conn.close()


def seat_update(request, seat_id):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    import json as _json
    data = _json.loads(request.body)
    venue_id    = data.get('venue_id')
    section     = data.get('section', '').strip()
    row_number  = data.get('row_number', '').strip()
    seat_number = data.get('seat_number', '').strip()
    if not all([venue_id, section, row_number, seat_number]):
        return JsonResponse({'success': False, 'error': 'Semua field wajib diisi.'})
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE "SEAT"
                SET "venue_id" = %s, "section" = %s, "row_number" = %s, "seat_number" = %s
                WHERE "seat_id" = %s
            """, [venue_id, section, row_number, seat_number, str(seat_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        raw = e.pgerror or str(e)
        msg = raw.strip().split('\n')[0].replace('ERROR:  ', '').replace('ERROR: ', '')
        return JsonResponse({'success': False, 'error': msg})
    finally:
        conn.close()

# Ticket Views
def ticket_create(request):
    from django.http import JsonResponse
    import json, random, string
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    if not _require_manage(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    data = json.loads(request.body)
    order_id    = data.get('order_id')
    category_id = data.get('category_id')
    seat_id     = data.get('seat_id')

    ticket_code = 'TKT-' + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO "TICKET" ("ticket_code", "tcategory_id", "torder_id")
                VALUES (%s, %s, %s)
                RETURNING "ticket_id"::text
            """, [ticket_code, category_id, order_id])
            ticket_id = cur.fetchone()[0]

            if seat_id:
                cur.execute("""
                    INSERT INTO "HAS_RELATIONSHIP" ("seat_id", "ticket_id")
                    VALUES (%s, %s)
                """, [seat_id, ticket_id])

        conn.commit()
        return JsonResponse({'success': True, 'ticket_code': ticket_code})
    except psycopg2.Error as e:
        conn.rollback()
        raw = e.pgerror or str(e)
        msg = raw.strip().split('\n')[0].replace('ERROR:  ', '').replace('ERROR: ', '')
        return JsonResponse({'success': False, 'error': msg})
    finally:
        conn.close()

def ticket_update(request, ticket_id):
    from django.http import JsonResponse
    import json as _json
    import psycopg2
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    if _current_role(request) != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    data = _json.loads(request.body)
    seat_id = data.get('seat_id') 
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "HAS_RELATIONSHIP" WHERE "ticket_id" = %s::uuid', [str(ticket_id)])

            if seat_id and seat_id != "" and seat_id != "None":
                cur.execute('DELETE FROM "HAS_RELATIONSHIP" WHERE "seat_id" = %s::uuid', [str(seat_id)])

                cur.execute("""
                    INSERT INTO "HAS_RELATIONSHIP" ("seat_id", "ticket_id")
                    VALUES (%s::uuid, %s::uuid)
                """, [str(seat_id), str(ticket_id)])
                
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database Error: {e}") 
        return JsonResponse({'success': False, 'error': str(e)})
    finally:
        conn.close()

def ticket_delete(request, ticket_id):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if _current_role(request) != 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM "HAS_RELATIONSHIP" WHERE "ticket_id" = %s', [str(ticket_id)])
            cur.execute('DELETE FROM "TICKET" WHERE "ticket_id" = %s', [str(ticket_id)])
        conn.commit()
        return JsonResponse({'success': True})
    except psycopg2.Error as e:
        conn.rollback()
        raw = e.pgerror or str(e)
        msg = raw.strip().split('\n')[0].replace('ERROR:  ', '').replace('ERROR: ', '')
        return JsonResponse({'success': False, 'error': msg})
    finally:
        conn.close()