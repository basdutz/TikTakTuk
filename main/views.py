import psycopg2
import os
import json

from dotenv import load_dotenv
load_dotenv()

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        return psycopg2.connect(db_url)

    # Fallback ke individual env vars
    host = os.getenv("localhost")
    port = os.getenv("5432")
    dbname = os.getenv("tiktaktuk")
    user = os.getenv("postgres")
    password = os.getenv("zahra3012")

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

DB_ROLE_TO_APP = {
    'administrator': 'admin',
    'organizer':     'organizer',
    'customer':      'customer',
}


def _authenticate(username, password):
    """
    Validasi kredensial via query langsung ke USER_ACCOUNT,
    return dict {user_id, roles: [...]}.
    Raise ValueError dengan pesan generik kalau gagal.
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


def _redirect_dashboard(app_role):
    return redirect({
        'admin':     'main:dashboard_admin',
        'organizer': 'main:dashboard_organizer',
        'customer':  'main:dashboard_customer',
    }.get(app_role, 'main:home'))


def _require_role(request, allowed_role):
    """Belum login -> home. Role salah -> dashboard role-nya sendiri."""
    if not request.session.get('role'):
        return redirect('main:home')
    if request.session.get('role') != allowed_role:
        return _redirect_dashboard(request.session.get('role'))
    return None

def _resolve_role(request):
    return request.GET.get('role') or request.session.get('role')
 

def _ctx(request, **extra):
    role = _resolve_role(request)
    base = {
        'role': role,
        'username': request.session.get('username'),
        'organizer_id': request.session.get('organizer_id'),
        'customer_id':  request.session.get('customer_id'),
        'is_admin':     role == 'admin',
        'is_organizer': role == 'organizer',
        'is_customer':  role == 'customer',
    }
    base.update(extra)
    return base
 
 
def _require_manage(request):
    return request.session.get('role') in ('admin', 'organizer')

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
            conn = psycopg2.connect(
                os.getenv("DATABASE_URL")
            )

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

            messages.success(request, "Akun berhasil dibuat!")

            cur.close()
            conn.close()

            return redirect("main:login")

        except Exception as e:
            messages.error(request, str(e))
            return render(request, "main/register_customer.html")
        
    return render(request, "main/register_customer.html")

def register_organizer(request):
    return render(request, "main/register_organizer.html")

def register_admin(request):
    return render(request, "main/register_admin.html")

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


def profile(request):
    role = request.GET.get('role')

    if role == 'organizer':
        return redirect('main:profile_organizer')
    elif role == 'customer':
        return redirect('main:profile_customer')
    elif role == 'admin':
        return redirect('main:profile_admin')
    else:
        return redirect('main:home')
    
def profile_organizer(request):
    return render(request, "main/profile_organizer.html", {'role': 'organizer', 'username': 'organizer'})

def profile_customer(request):
    return render(request, "main/profile_customer.html", {'role': 'customer', 'username': 'customer'})

def profile_admin(request):
    return render(request, "main/profile_admin.html", {'role': 'admin', 'username': 'admin'})

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

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT create_venue(%s, %s, %s, %s, %s)::text
            """, [
                data.get('venue_name', '').strip(),
                int(data.get('capacity') or 0),
                data.get('address', '').strip(),
                data.get('city', '').strip(),
                data.get('seat_type', '').strip(),
            ])
            new_id = cur.fetchone()[0]
        conn.commit()
        return JsonResponse({'success': True, 'venue_id': new_id})
    except psycopg2.Error as e:
        conn.rollback()
        # Pesan WAJIB datang dari trigger/SP (lihat extract_pg_error)
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

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT update_venue(%s::uuid, %s, %s, %s, %s, %s)
            """, [
                str(venue_id),
                data.get('venue_name', '').strip(),
                int(data.get('capacity') or 0),
                data.get('address', '').strip(),
                data.get('city', '').strip(),
                data.get('seat_type', '').strip(),
            ])
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
def order_list_admin(request):
    return render(request, 'main/order/order_list.html', {'role': 'admin', 'username': 'admin'})

def order_list_organizer(request):
    return render(request, 'main/order/order_list.html', {'role': 'organizer', 'username': 'organizer'})

def order_list_customer(request):
    return render(request, 'main/order/order_list.html', {'role': 'customer', 'username': 'customer'})

def order_checkout(request, event_id):
    return render(request, 'main/order/order_checkout.html', {
        'role': 'customer',
        'username': 'customer',
        'event_id': event_id,
    })

# Promotion Views
def promotion_list_admin(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'admin', 'username': 'admin'})

def promotion_list_organizer(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'organizer', 'username': 'organizer'})

def promotion_list_customer(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'customer', 'username': 'customer'})

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