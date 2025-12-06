"""Admin dashboard and management routes - API-only version"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, abort
from services import database_access as api
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
def check_admin():
    """Ensure all admin routes require IP whitelist access and set API server"""
    # IP whitelist - only these IPs can access admin routes
    allowed_ips = [
        '127.0.0.1',           # localhost
        '::1',                 # localhost IPv6
        '192.168.1.180',       # Your local development machine
        '192.168.1.181',       # Alternate local IP if DHCP changes
        '192.168.1.226',
        '2603:800c:4d3f:15f::1068',
        # Add your home/office static IP here if you need remote access
    ]

    client_ip = request.remote_addr
    if client_ip not in allowed_ips:
        flash('Admin access denied: Invalid IP address', 'danger')
        abort(403)  # Forbidden

    # Set the API server based on session mode
    current_api_mode = session.get('api_mode', 'local')
    api.set_server(current_api_mode)



@admin_bp.route('/')
def index():
    """Admin dashboard landing page"""
    return redirect(url_for('admin.dashboard'))



@admin_bp.route('/dashboard')
def dashboard():
    """Main admin dashboard"""
    # Get current API mode from session
    current_api_mode = session.get('api_mode', 'local')

    # Get stats via API
    listings_data, _ = api.get_listings(status='active')
    all_quotes, _ = api.get_quotes('')  # Get all quotes
    activities_data, _ = api.get_activities(page=1, per_page=10)
    api_log_data, _ = api.get_api_log()

    stats = {
        'listings': len(listings_data) if isinstance(listings_data, list) else 0,
        'quotes': len(all_quotes) if isinstance(all_quotes, list) else 0,
        'activities': len(activities_data) if isinstance(activities_data, list) else 0,
        'api_logs': len(api_log_data) if isinstance(api_log_data, list) else 0,
        'api_mode': current_api_mode
    }

    return render_template('admin/dashboard.html',
                         current_api_mode=current_api_mode,
                         stats=stats)



@admin_bp.route('/switch-api', methods=['POST'])
def switch_api():
    """Switch between local and remote API"""
    api_mode = request.form.get('api_mode', 'local')

    if api_mode not in ['local', 'remote']:
        flash('Invalid API mode', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Store in session and update database_access
    session['api_mode'] = api_mode
    api.set_server(api_mode)

    mode_text = "Local Development" if api_mode == 'local' else "Production"
    flash(f'✅ Switched to {mode_text} API', 'success')

    return redirect(url_for('admin.dashboard'))



@admin_bp.route('/user-activity')
def user_activity():
    """View users who printed flyers from the website"""
    # Get all activities and filter for print_flyer actions
    all_activities, status_code = api.get_activities(page=1, per_page=1000)
    if status_code != 200:
        flash(f'Error loading activities: {all_activities}', 'danger')
        activities = []
    else:
        # Normalize activities (handle list of lists vs list of dicts)
        normalized_activities = []
        for a in all_activities:
            if isinstance(a, dict):
                normalized_activities.append(a)
            elif isinstance(a, list) and len(a) >= 12:
                # Map list to dict based on schema
                # id, contact_id, email, mls_number, activity_type, feature, action, endpoint, notes, ip_address, user_agent, created
                normalized_activities.append({
                    'id': a[0],
                    'contact_id': a[1],
                    'email': a[2],
                    'mls_number': a[3],
                    'activity_type': a[4],
                    'feature': a[5],
                    'action': a[6],
                    'endpoint': a[7],
                    'notes': a[8],
                    'ip_address': a[9],
                    'user_agent': a[10],
                    'created': a[11]
                })
        
        # Group by email to get unique contacts with their print counts
        email_groups = {}
        for activity in all_activities:
            email = activity['email']
            if not email:
                continue

            if email not in email_groups:
                email_groups[email] = {
                    'email_address': email,
                    'first_name': activity['first_name'],
                    'last_name': activity['last_name'],
                    'company': activity['company'],
                    'phone': '',  # Not available in activities table
                    'print_count': 0,
                    'last_activity': activity['created'],
                }

            email_groups[email]['print_count'] += 1

            # Keep the most recent activity timestamp
            if activity['created'] > email_groups[email]['last_activity']:
                email_groups[email]['last_activity'] = activity['created']

        activities = list(email_groups.values())
        # Sort by last activity (most recent first)
        activities.sort(key=lambda x: x['last_activity'], reverse=True)

    return render_template('admin/user_activity.html',
                         activities=activities)



@admin_bp.route('/contacts')
def contacts():
    """View and manage contacts"""
    # TODO: Need a get_contacts() API endpoint
    flash('Contacts view not yet implemented - need API endpoint', 'info')
    contacts_data = []

    return render_template('admin/contacts.html',
                         contacts=contacts_data)



@admin_bp.route('/listings')
def listings():
    """View and manage listings"""
    status_filter = request.args.get('status', 'all')

    # Get listings via API
    if status_filter == 'all':
        listings_data, status_code = api.get_listings()
    else:
        listings_data, status_code = api.get_listings(status=status_filter)

    if status_code != 200:
        flash(f'Error loading listings: {listings_data}', 'danger')
        listings_data = []

    return render_template('admin/listings.html',
                         listings=listings_data,
                         status_filter=status_filter)



@admin_bp.route('/quotes')
def quotes():
    """View all quotes"""
    # Get all quotes via API (empty mls_number returns all)
    quotes_data, status_code = api.get_quotes('')

    if status_code != 200:
        flash(f'Error loading quotes: {quotes_data}', 'danger')
        quotes_data = []

    return render_template('admin/quotes.html',
                         quotes=quotes_data)



@admin_bp.route('/daily-prices')
def daily_prices():
    """View daily pricing data for all counties"""
    # County zipcode mapping
    counties = {
        90620: "Orange",
        91901: "San Diego",
        91708: "Riverside",
        90001: "Los Angeles",
        91319: "Ventura",
        91701: "San Bernardino",
        96701: "Honolulu",
        96703: "Kauai",
        96708: "Maui",
        96704: "Hawaii"
    }

    # Get prices for each county
    all_prices = []
    for zipcode, county_name in counties.items():
        prices_data, status_code = api.get_daily_prices(zipcode=zipcode)
        if status_code == 200 and isinstance(prices_data, list):
            for price in prices_data:
                price['county'] = county_name
            all_prices.extend(prices_data)

    return render_template('admin/daily_prices.html',
                         prices=all_prices,
                         counties=counties)



@admin_bp.route('/flyer-printers')
def flyer_printers():
    try:
        """View contacts who printed flyers from the website"""
        # Get all activities and filter for print_flyer type
        all_activities, status_code = api.get_activities(page=1, per_page=1000)

        if status_code != 200:
            flash(f'Error loading activities: {all_activities}', 'danger')
            flyer_printers_data = []
        else:
            # The API returns [rows, total_count]
            # Extract the list of activity dictionaries from the first element
            if isinstance(all_activities, list) and len(all_activities) > 0 and isinstance(all_activities[0], list):
                activities_list = all_activities[0]
            else:
                # Fallback: assume it's just a list of dicts if structure doesn't match [rows, total]
                activities_list = all_activities if isinstance(all_activities, list) else []

            # Filter for print_flyer activities
            print_activities = []
            for a in activities_list:
                if not isinstance(a, dict):
                    continue
                
                action = a.get('action')
                if isinstance(action, str) and action.startswith('print_flyer'):
                    print_activities.append(a)

            # Sort by created date (most recent first)
            print_activities.sort(key=lambda x: x.get('created', ''), reverse=True)

        return render_template('admin/flyer_printers.html',
                             flyer_printers=print_activities)
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}", 500



@admin_bp.route('/extract-activities', methods=['POST'])
def extract_activities():
    """Extract print_flyer activities from api_logs table"""
    result, status_code = api.add_activities(activity_type="print_flyer")

    if status_code == 200:
        flash('✅ Successfully extracted print activities from API logs', 'success')
    else:
        flash(f'Error extracting activities: {result}', 'danger')

    return redirect(url_for('admin.flyer_printers'))
