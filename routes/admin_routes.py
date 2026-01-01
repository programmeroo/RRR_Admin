"""Admin dashboard and management routes - API-only version"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, abort, Response
from services import database_access as api
from services.my_logger import log
import os
import csv
import io
from datetime import datetime

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
        log(f'Admin access denied: Invalid IP address {client_ip}', 'danger')
        abort(403)  # Forbidden

    # Set the API server based on session mode
    current_api_mode = session.get('api_mode', 'local')
    api.set_server(current_api_mode)



@admin_bp.route('/')
def index():
    """Admin dashboard landing page"""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api-logs')
def api_logs():
    log_days_str = request.args.get('log_days', '1')
    log_days = int(log_days_str)
    print(f"log_days: {log_days}")
    api_log_data, _ = api.get_api_log(page=1, per_page=500, since=log_days)

    return render_template('admin/api_log.html',
                         api_log_data=api_log_data,
                         log_days=log_days_str)


@admin_bp.route('/web-logs')
def web_logs():
    log_days_str = request.args.get('log_days', '1')
    log_days = int(log_days_str)
    print(f"log_days: {log_days}")
    web_log_data, _ = api.get_web_log(page=1, per_page=500, since=log_days)

    return render_template('admin/web_log.html',
                         web_log_data=web_log_data,
                         log_days=log_days_str)


@admin_bp.route('/contacts')
def contacts():
    """View and manage contacts"""
    filter_type = request.args.get('filter', 'active')

    # Build API parameters - only include unsubscribed if filtering for unsubscribed
    params = {'page': 1, 'per_page': 50}
    if filter_type == "unsubscribed":
        params['unsubscribed'] = True
    else:
        params['unsubscribed'] = False

    contacts_data, status_code = api.get_contacts(**params)
    print(f"contacts count: {len(contacts_data)}")
    if status_code != 200:
        log(f'Error loading contacts: {contacts_data}', 'danger')
        contacts_data = []

    return render_template('admin/contacts.html',
                         contacts=contacts_data,
                         filter=filter_type)


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
    county = int(request.args.get('county', '99999'))
    print(f"county: {county}")
    prices_data, status_code = api.get_daily_prices()
    daily_prices = []


    if status_code == 200 and isinstance(prices_data, list):
        for price in prices_data:
            date_time_string = price["priced_on"]
            price["county"] = counties[price.get("zipcode")]
            date_time_string = price["priced_on"]
            price["price_date_only"] = date_time_string.split()[0]

            # Selected county
            if county == int(price.get("zipcode")):
                print(f"county == {price.get('zipcode')}")
                daily_prices.append(price)

        # All counties
        if county == 99999:
            daily_prices.extend(prices_data)

        print(f"daily_prices len: {len(daily_prices)}")

    return render_template('admin/daily_prices.html',
                         prices=daily_prices,
                         counties=counties,
                         county=county)


@admin_bp.route('/dscr-prices')
def dscr_prices():
    """View DSCR pricing data for all counties"""
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
    county = int(request.args.get('county', '99999'))
    print(f"DSCR county: {county}")
    prices_data, status_code = api.get_dscr_prices()
    dscr_prices_list = []

    if status_code == 200 and isinstance(prices_data, list):
        for price in prices_data:
            date_time_string = price.get("priced_on", "")
            price["county"] = counties.get(price.get("zipcode"), "Unknown")
            price["price_date_only"] = date_time_string.split()[0] if date_time_string else 'N/A'

            # Selected county
            if county == int(price.get("zipcode")):
                dscr_prices_list.append(price)

        # All counties
        if county == 99999:
            dscr_prices_list.extend(prices_data)

        print(f"dscr_prices len: {len(dscr_prices_list)}")

    return render_template('admin/dscr_prices.html',
                         prices=dscr_prices_list,
                         counties=counties,
                         county=county)


@admin_bp.route('/dashboard')
def dashboard():
    """Main admin dashboard"""
    # Get current API mode from session
    current_api_mode = session.get('api_mode', 'local')
    log(f"current_api_mode: {current_api_mode}")

    # Get listings summary
    listings_summary_raw, _ = api.get_listings_summary()

    # Convert from [{'count': 72, 'status': 'dscr_emailed'}, ...] to {'dscr_emailed': 72, ...}
    listings_summary = {}
    if isinstance(listings_summary_raw, list):
        for item in listings_summary_raw:
            status = item.get('status')
            count = item.get('count')
            if status and count is not None:
                listings_summary[status] = count

    # Get contacts summary
    contacts_summary, _ = api.get_contacts_summary()

    # Extract counts from summary [{'subscribed': 164}, {'unsubscribed': 2}]
    subscribed_count = 0
    unsubscribed_count = 0
    if isinstance(contacts_summary, list):
        for item in contacts_summary:
            if 'subscribed' in item:
                subscribed_count = item['subscribed']
            if 'unsubscribed' in item:
                unsubscribed_count = item['unsubscribed']

    # Get Orange County house rates (zipcode 90620)
    orange_rates, _ = api.get_daily_prices(zipcode=90620, listing_type='house')
    rates = {}
    if isinstance(orange_rates, list):
        # Map loan types to rate values
        loan_type_map = {
            'conventional-20': 'conv_20',
            'conventional-5': 'conv_5',
            'high balance-20': 'high_bal_20',
            'high balance-5': 'high_bal_5',
            'fha': 'fha',
            'va': 'va',
            'jumbo': 'jumbo'
        }

        for rate_obj in orange_rates:
            loan_type = rate_obj.get('loan_type')
            rate_value = rate_obj.get('rate')
            if loan_type in loan_type_map:
                rates[loan_type_map[loan_type]] = rate_value

    # Get flyer printers count
    all_activities, _ = api.get_activities(page=1, per_page=50)

    # Handle pagination format and count unique emails
    flyer_printers_count = 0
    if isinstance(all_activities, list):
        raw_list = all_activities[0] if len(all_activities) == 2 else all_activities
        unique_emails = set()
        for activity in raw_list:
            email = activity.get('email_address') or activity.get('email')
            if email:
                unique_emails.add(email)
        flyer_printers_count = len(unique_emails)

    # Get logs summary
    logs_summary, _ = api.get_api_logs_summary()

    # Extract counts from summary [{'web_logs': 366}, {'api_logs': 544}]
    api_logs_count = 0
    web_logs_count = 0
    if isinstance(logs_summary, list):
        for item in logs_summary:
            if 'api_logs' in item:
                api_logs_count = item['api_logs']
            if 'web_logs' in item:
                web_logs_count = item['web_logs']

    stats = {
        'listings_summary': listings_summary if isinstance(listings_summary, dict) else {},
        'contacts_subscribed': subscribed_count,
        'contacts_unsubscribed': unsubscribed_count,
        'rates': rates,
        'flyer_printers': flyer_printers_count,
        'api_logs': api_logs_count,
        'web_logs': web_logs_count,
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
        log('Invalid API mode', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Store in session and update database_access
    session['api_mode'] = api_mode
    api.set_server(api_mode)

    mode_text = "Local Development" if api_mode == 'local' else "Production"
    log(f'Switched to {mode_text} API', 'success')

    return redirect(url_for('admin.dashboard'))



@admin_bp.route('/user-print-activity')
def user_print_activity():
    """Extract print_flyer activities from api_logs table"""
    result, status_code = api.add_activities(activity_type="print_flyer")

    if status_code == 200:
        log('Successfully extracted print activities from API logs', 'success')
    else:
        log(f'Error extracting activities: {result}', 'danger')

    """View users who printed flyers from the website"""
    # Get all activities and filter for print_flyer actions
    all_activities, status_code = api.get_activities(page=1, per_page=50)
    if status_code != 200:
        log(f'Error loading activities: {all_activities}', 'danger')
        activities = []
    else:
        # Handle pagination: API returns [rows, count] format
        raw_list = []
        if isinstance(all_activities, list):
            if len(all_activities) == 2 and isinstance(all_activities[1], int) and isinstance(all_activities[0], list):
                raw_list = all_activities[0]
            else:
                raw_list = all_activities

        # All activities are already dicts from the API, just use them directly
        # Group by email to get unique contacts with their activity counts
        email_groups = {}
        for activity in raw_list:
            if not isinstance(activity, dict):
                continue

            # Use email_address field (which comes from joined contact table)
            email = activity.get('email_address') or activity.get('email')
            if not email:
                continue

            if email not in email_groups:
                email_groups[email] = {
                    'email_address': email,
                    'first_name': activity.get('first_name', ''),
                    'last_name': activity.get('last_name', ''),
                    'company': activity.get('company', ''),
                    'phone': activity.get('phone', ''),
                    'print_count': 0,
                    'last_activity': activity.get('created', ''),
                }

            email_groups[email]['print_count'] += 1

            # Keep the most recent activity timestamp
            if activity.get('created', '') > email_groups[email]['last_activity']:
                email_groups[email]['last_activity'] = activity['created']

        activities = list(email_groups.values())
        # Sort by last activity (most recent first)
        activities.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

    return render_template('admin/flyer_printers.html',
                         activities=activities)


@admin_bp.route('/visitor-activity')
def visitor_activity():
    all_activities, status_code = api.get_activities(page=1, per_page=50)
    if status_code != 200:
        log(f'Error loading activities: {all_activities}', 'danger')
        activities = []
    else:
        # Handle pagination: API returns [rows, count] format
        raw_list = []
        if isinstance(all_activities, list):
            if len(all_activities) == 2 and isinstance(all_activities[1], int) and isinstance(all_activities[0], list):
                raw_list = all_activities[0]
            else:
                raw_list = all_activities

        # All activities are already dicts from the API, just use them directly
        # Group by email to get unique contacts with their activity counts
        email_groups = {}
        for activity in raw_list:
            if not isinstance(activity, dict):
                continue

            # Use email_address field (which comes from joined contact table)
            email = activity.get('email_address') or activity.get('email')
            if not email:
                continue

            if email not in email_groups:
                email_groups[email] = {
                    'email_address': email,
                    'first_name': activity.get('first_name', ''),
                    'last_name': activity.get('last_name', ''),
                    'company': activity.get('company', ''),
                    'phone': activity.get('phone', ''),
                    'page_count': 0,
                    'last_activity': activity.get('created', ''),
                }

            email_groups[email]['page_count'] += 1

            # Keep the most recent activity timestamp
            if activity.get('created', '') > email_groups[email]['last_activity']:
                email_groups[email]['last_activity'] = activity['created']

        activities = list(email_groups.values())
        # Sort by last activity (most recent first)
        activities.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

    return render_template('admin/user_activity.html',
                         activities=activities)


@admin_bp.route('/export-visitor-activity')
def export_visitor_activity():
    """Export user activity to CSV"""
    # Get all activities and filter for print_flyer actions
    all_activities, status_code = api.get_activities(page=1, per_page=50)

    if status_code != 200:
        log(f'Error loading activities for export: {all_activities}', 'danger')
        return redirect(url_for('admin.visitor_activity'))

    # Handle pagination: API returns [rows, count] format
    raw_list = []
    if isinstance(all_activities, list):
        if len(all_activities) == 2 and isinstance(all_activities[1], int) and isinstance(all_activities[0], list):
            raw_list = all_activities[0]
        else:
            raw_list = all_activities

    # Group by email to get unique contacts with their activity counts
    email_groups = {}
    for activity in raw_list:
        if not isinstance(activity, dict):
            continue

        # Use email_address field (which comes from joined contact table)
        email = activity.get('email_address') or activity.get('email')
        if not email:
            continue

        if email not in email_groups:
            email_groups[email] = {
                'email_address': email,
                'first_name': activity.get('first_name', ''),
                'last_name': activity.get('last_name', ''),
                'company': activity.get('company', ''),
                'phone': activity.get('phone', ''),
                'print_count': 0,
                'last_activity': activity.get('created', ''),
            }

        email_groups[email]['print_count'] += 1

        # Keep the most recent activity timestamp
        if activity.get('created', '') > email_groups[email]['last_activity']:
            email_groups[email]['last_activity'] = activity['created']

    activities = list(email_groups.values())
    # Sort by last activity (most recent first)
    activities.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Print Count', 'Last Activity'])

    # Data
    for a in activities:
        writer.writerow([
            a.get('first_name', ''),
            a.get('last_name', ''),
            a.get('email_address', ''),
            a.get('phone', ''),
            a.get('company', ''),
            a.get('print_count', 0),
            a.get('last_activity', '')
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=flyer_printers.csv"}
    )

@admin_bp.route('/export-print-activity')
def export_print_activity():
    """Export user activity to CSV"""
    # Get all activities and filter for print_flyer actions
    all_activities, status_code = api.get_activities(activity_type="print_flyer")

    if status_code != 200:
        log(f'Error loading activities for export: {all_activities}', 'danger')
        return redirect(url_for('admin.user_print_activity'))

    # Handle pagination: API returns [rows, count] format
    raw_list = []
    if isinstance(all_activities, list):
        if len(all_activities) == 2 and isinstance(all_activities[1], int) and isinstance(all_activities[0], list):
            raw_list = all_activities[0]
        else:
            raw_list = all_activities

    # Group by email to get unique contacts with their activity counts
    email_groups = {}
    for activity in raw_list:
        if not isinstance(activity, dict):
            continue

        # Use email_address field (which comes from joined contact table)
        email = activity.get('email_address') or activity.get('email')
        if not email:
            continue

        if email not in email_groups:
            email_groups[email] = {
                'email_address': email,
                'first_name': activity.get('first_name', ''),
                'last_name': activity.get('last_name', ''),
                'company': activity.get('company', ''),
                'phone': activity.get('phone', ''),
                'print_count': 0,
                'last_activity': activity.get('created', ''),
            }

        email_groups[email]['print_count'] += 1

        # Keep the most recent activity timestamp
        if activity.get('created', '') > email_groups[email]['last_activity']:
            email_groups[email]['last_activity'] = activity['created']

    activities = list(email_groups.values())
    # Sort by last activity (most recent first)
    activities.sort(key=lambda x: x.get('last_activity', ''), reverse=True)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Company', 'Print Count', 'Last Activity'])

    # Data
    for a in activities:
        writer.writerow([
            a.get('first_name', ''),
            a.get('last_name', ''),
            a.get('email_address', ''),
            a.get('phone', ''),
            a.get('company', ''),
            a.get('print_count', 0),
            a.get('last_activity', '')
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=flyer_printers.csv"}
    )



@admin_bp.route('/listings')
def listings():
    """View and manage listings"""
    status_filter = request.args.get('status', 'all')

    # Get listings via listing_page_views
    listings_data, status_code = api.get_listing_page_views(status=status_filter, page=1, per_page=50)

    if status_code != 200:
        log(f'Error loading listings: {listings_data}', 'danger')
        listings_data = []

    return render_template('admin/listings.html',
                         listings=listings_data,
                         status_filter=status_filter)


def _get_flyer_printer_data():
    """Helper to get and filter flyer printer data"""
    all_activities, status_code = api.get_activities(page=1, per_page=50)

    if status_code != 200:
        log(f"API error: {all_activities}", 'danger')
        return []
    
    # 1. Determine list of items (handle pagination variations)
    raw_list = []
    if isinstance(all_activities, list):
        # Check for [rows, count] pattern common in pagination
        if len(all_activities) == 2 and isinstance(all_activities[1], int) and isinstance(all_activities[0], list):
             raw_list = all_activities[0]
        else:
             raw_list = all_activities
    
    # 2. Normalize items to dicts
    normalized_list = []
    for a in raw_list:
        if isinstance(a, dict):
            normalized_list.append(a)
        elif isinstance(a, list) and len(a) >= 12:
             # Schema mapping from user_activity route
             normalized_list.append({
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

    # 3. Filter for print_flyer
    print_activities = []
    for a in normalized_list:
        action = a.get('action')
        if isinstance(action, str) and action.startswith('print_flyer'):
            print_activities.append(a)

    # Sort by created date (most recent first)
    print_activities.sort(key=lambda x: x.get('created', ''), reverse=True)
    return print_activities


@admin_bp.route('/flyer-printers')
def flyer_printers():
    """View contacts who printed flyers from the website"""
    flyer_printers_data = _get_flyer_printer_data()
    return render_template('admin/flyer_printers.html',
                         flyer_printers=flyer_printers_data)


@admin_bp.route('/export-flyer-printers')
def export_flyer_printers():
    """Export flyer printer activities to CSV"""
    activities = _get_flyer_printer_data()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow(['Date', 'First Name', 'Last Name', 'Email', 'Phone', 'Company', 'MLS Number', 'Type', 'Action'])

    # Data
    for a in activities:
        # Determine Activity Type (QM vs DSCR)
        act_type = "Other"
        action = a.get('action', '')
        if 'owner' in action:
            act_type = "QM"
        elif 'dscr' in action:
            act_type = "DSCR"

        writer.writerow([
            a.get('created', ''),
            a.get('first_name', ''),
            a.get('last_name', ''),
            a.get('email', ''),
            a.get('phone', ''),
            a.get('company', ''),
            a.get('mls_number', ''),
            act_type,
            action
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=flyer_printers.csv"}
    )


@admin_bp.route('/unsubscribe-user', methods=['GET', 'POST'])
def unsubscribe_user():
    """Unsubscribe a user from email list"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            log('Email address is required', 'danger')
            return redirect(url_for('admin.unsubscribe_user'))

        # Call API to unsubscribe
        result, status_code = api.unsubscribe_contact(email)

        if status_code == 200:
            log(f'Successfully unsubscribed {email}', 'success')
            return redirect(url_for('admin.contacts'))
        else:
            log(f'Error unsubscribing {email}: {result}', 'danger')
            return redirect(url_for('admin.unsubscribe_user'))

    return render_template('admin/unsubscribe_user.html')


@admin_bp.route('/user-activity-detail')
def user_activity_detail():
    """View activity for a specific user or MLS number"""
    email = request.args.get('email', '').strip()
    mls_number = request.args.get('mls_number', '').strip()

    activities = []

    if email or mls_number:
        # Build query parameters
        params = {'page': 1, 'per_page': 500}
        if email:
            params['email'] = email
        if mls_number:
            params['mls_number'] = mls_number

        activities_data, status_code = api.get_activities(**params)

        if status_code == 200 and isinstance(activities_data, list):
            # Handle pagination format
            if len(activities_data) == 2 and isinstance(activities_data[1], int):
                activities = activities_data[0]
            else:
                activities = activities_data

    return render_template('admin/user_activity_detail.html',
                         activities=activities,
                         email=email,
                         mls_number=mls_number)


@admin_bp.route('/suspicious-activity')
def suspicious_activity():
    """Monitor potential hacker activity"""
    # Get API logs for suspicious patterns
    api_logs, _ = api.get_api_log(page=1, per_page=1000, since=1)
    web_logs, _ = api.get_web_log(page=1, per_page=1000, since=1)

    # Analyze for suspicious patterns
    ip_counts = {}
    suspicious_activities = []

    # Process API logs
    if isinstance(api_logs, list):
        for log_entry in api_logs:
            ip = log_entry.get('ip_address', 'Unknown')
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

            # Flag suspicious patterns
            endpoint = log_entry.get('endpoint', '')
            status_code = log_entry.get('status_code', 200)

            # Failed auth attempts, unusual endpoints
            if status_code in [401, 403, 404] or 'admin' in endpoint or 'api_key' in endpoint:
                suspicious_activities.append({
                    'ip_address': ip,
                    'activity_type': 'API Access',
                    'action': f"{log_entry.get('method', 'GET')} {endpoint}",
                    'created': log_entry.get('created', ''),
                    'email': None,
                    'email_address': None
                })

    # Process web logs
    if isinstance(web_logs, list):
        for log_entry in web_logs:
            ip = log_entry.get('ip_address', 'Unknown')
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

    # Identify high-frequency IPs (potential DDoS or scraping)
    high_frequency_ips = [
        {'ip_address': ip, 'count': count, 'last_seen': 'Recent'}
        for ip, count in ip_counts.items()
        if count > 50
    ]
    high_frequency_ips.sort(key=lambda x: x['count'], reverse=True)

    # Sort suspicious activities by most recent
    suspicious_activities.sort(key=lambda x: x.get('created', ''), reverse=True)

    stats = {
        'high_frequency_ips': len(high_frequency_ips),
        'failed_attempts': len([a for a in suspicious_activities if '401' in str(a) or '403' in str(a)]),
        'unique_ips': len(ip_counts)
    }

    return render_template('admin/suspicious_activity.html',
                         stats=stats,
                         high_frequency_ips=high_frequency_ips,
                         suspicious_activities=suspicious_activities)



