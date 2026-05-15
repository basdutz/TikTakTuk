import uuid

import psycopg2
import os
import json

from dotenv import load_dotenv
load_dotenv()

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

#  DATABASE HELPER
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        return psycopg2.connect(db_url)

    # Fallback ke individual env vars
    host = os.getenv("PGHOST","localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE", "tiktaktuk")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD",)

    if not all([host, dbname, user, password]):
        raise RuntimeError(
            "DATABASE_URL tidak ditemukan dan env vars PG* belum lengkap. "
            "Pastikan file .env ada di root project dan berisi DATABASE_URL. "
            "Periksa: file .env exists? load_dotenv() jalan? path .env benar?"
        )

    return psycopg2.connect(
        host=host, port=port, dbname=dbname,
        user=user, password=password,
    )


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


#  AUTH HELPERS (untuk Login)
def _authenticate(username, password):
    """
    Validasi kredensial via query langsung ke USER_ACCOUNT,
    return dict {user_id, roles: [...]}.
    Raise ValueError dengan pesan generik kalau gagal.
    sehingga tidak terjadi user-enumeration.
    """
    if not username or not password:
        raise ValueError('Username dan password wajib diisi.')

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Cek username + password (case-insensitive untuk username)
            cur.execute("""
                SELECT "user_id"::text, "PASSWORD"
                  FROM "USER_ACCOUNT"
                 WHERE LOWER("username") = LOWER(%s)
            """, [username])
            row = cur.fetchone()

            # Pesan sama untuk username/password salah -> hindari user enumeration
            if not row or row[1] != password:
                raise ValueError('Username atau password salah.')

            user_id = row[0]

            # 2. Ambil semua role
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
        phone_number = request.POST.get("phone_number")
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                CALL register_customer(%s, %s, %s, %s)
            """, (
                full_name,
                phone_number,
                username,
                password
            ))

            conn.commit()
            cur.close()
            conn.close()
            
            messages.success(request, "Akun berhasil dibuat!")

            return redirect("main:login")

        except psycopg2.Error as e:
                    messages.error(request, extract_pg_error(e))
                    return render(request, "main/register_customer.html")
        except Exception as e:
            messages.error(request, str(e))
            return render(request, "main/register_customer.html")
        
    return render(request, "main/register_customer.html")

def register_organizer(request):
    return render(request, "main/register_organizer.html")

def register_admin(request):
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
    return render(request, "main/dashboard_admin.html", _ctx(request))


def dashboard_organizer(request):
    guard = _require_role(request, 'organizer')
    if guard:
        return guard
    return render(request, "main/dashboard_organizer.html", _ctx(request))


def dashboard_customer(request):
    guard = _require_role(request, 'customer')
    if guard:
        return guard
    return render(request, "main/dashboard_customer.html", _ctx(request))

def profile_organizer(request):
    return render(request, "main/profile_organizer.html", _ctx(request))

def profile_customer(request):
    return render(request, "main/profile_customer.html", _ctx(request))

def profile_admin(request):
    return render(request, "main/profile_admin.html", _ctx(request))

def artist_list(request):
    return render(request, "main/artist/artist_list.html", _ctx(request))

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
def event_list(request):
    return render(request, "main/event/event_list.html", _ctx(request))

def event_create(request):
    if not _require_manage(request):
        return redirect('main:event_list')
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=False,
    ))

def event_edit(request, event_id):
    if not _require_manage(request):
        return redirect('main:event_list')
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=True,
        event_id=event_id,
    ))

def ticket_category_list(request):
    return render(request, 'main/ticket_category/category_list.html', _ctx(request))

def my_tickets(request):
    return render(request, "main/ticket/my_tickets.html", {'role': 'customer', 'username': 'customer'})

def manajemen_tiket_admin(request):
    return render(request, "main/ticket/manajemen_tiket.html", {'role': 'admin', 'username': 'admin'})

def manajemen_tiket_organizer(request):
    return render(request, "main/ticket/manajemen_tiket.html", {'role': 'organizer', 'username': 'organizer'})

def seat_admin(request):
    return render(request, 'main/seat/seat.html', {'role': 'admin', 'username': 'admin'})

def seat_organizer(request):
    return render(request, 'main/seat/seat.html', {'role': 'organizer', 'username': 'organizer'})

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
        lunas = sum(1 for o in orders if o['payment_status'].lower() == 'Completed')
        pending = sum(1 for o in orders if o['payment_status'].lower() == 'Pending')
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
        messages.error(request, str(e))
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