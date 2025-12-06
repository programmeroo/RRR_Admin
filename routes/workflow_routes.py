"""Admin workflow routes - run workflows in background like TKinter app"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from services import database_access as api
from services import workflow_runner as runner

workflow_bp = Blueprint('workflow', __name__, url_prefix='/admin/workflow')


@workflow_bp.before_request
def check_admin():
    """Ensure all workflow routes require IP whitelist (checked in admin_bp) and set API server"""
    # Set the API server based on session mode
    current_api_mode = session.get('api_mode', 'local')
    api.set_server(current_api_mode)


@workflow_bp.route('/')
def index():
    """Workflow management page"""
    current_api_mode = session.get('api_mode', 'local')

    # Get workflow status/counts via API
    new_listings, _ = api.get_listings(status='new')
    quoted_listings, _ = api.get_listings(status='quoted')
    dscr_quoted_listings, _ = api.get_listings(status='dscr_quoted')

    workflow_stats = {
        'new_listings': len(new_listings) if isinstance(new_listings, list) else 0,
        'listings_quoted': len(quoted_listings) if isinstance(quoted_listings, list) else 0,
        'listings_dscr_quoted': len(dscr_quoted_listings) if isinstance(dscr_quoted_listings, list) else 0,
    }

    # Get current workflow status
    status = runner.get_workflow_status()

    return render_template('admin/workflows.html',
                         current_api_mode=current_api_mode,
                         stats=workflow_stats,
                         workflow_status=status)


@workflow_bp.route('/status')
def status():
    """Get current workflow status (for AJAX polling)"""
    return jsonify(runner.get_workflow_status())


@workflow_bp.route('/run/<workflow_name>', methods=['POST'])
def run_workflow(workflow_name):
    """Run a predefined workflow in the background"""
    # Check if a workflow is already running
    status = runner.get_workflow_status()
    if status['running']:
        flash('A workflow is already running. Please wait for it to complete.', 'warning')
        return redirect(url_for('workflow.index'))

    # Get workflow parameters
    listing_status = request.form.get('listing_status', 'new')
    debug = request.form.get('debug', 'false') == 'true'

    # Select workflow
    workflows = {
        'full': runner.WORKFLOW_FULL,
        'quote_email': runner.WORKFLOW_QUOTE_EMAIL,
        'dscr': runner.WORKFLOW_DSCR,
        'process_only': runner.WORKFLOW_PROCESS_ONLY,
    }

    workflow = workflows.get(workflow_name)
    if not workflow:
        flash(f'Invalid workflow: {workflow_name}', 'danger')
        return redirect(url_for('workflow.index'))

    # Start workflow in background
    runner.run_workflow(workflow, listing_status=listing_status, debug=debug)

    flash(f'✅ Started {workflow_name} workflow in background. Use the status panel to monitor progress.', 'success')
    return redirect(url_for('workflow.index'))


# Individual task routes (for manual execution)

@workflow_bp.route('/scrape-homes', methods=['POST'])
def scrape_homes():
    """Copy HTML files from Downloads to processing folder"""
    try:
        result = runner.do_scrape()
        flash('Scrape homes completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/process-listings', methods=['POST'])
def process_listings():
    """Process listing pages from HTML files"""
    try:
        result = runner.do_process_pages()
        flash('Process listings completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/scrape-pricing', methods=['POST'])
def scrape_pricing():
    """Scrape mortgage pricing from LoanFactory"""
    try:
        result = runner.do_pricing()
        flash('Pricing scrape completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/generate-quotes', methods=['POST'])
def generate_quotes():
    """Generate conventional/FHA/VA quotes via API"""
    listing_status = request.form.get('listing_status', 'new')

    try:
        result = runner.do_quote(listing_status)
        flash('Quote generation completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/generate-dscr-quotes', methods=['POST'])
def generate_dscr_quotes():
    """Generate DSCR (investment) quotes via API"""
    listing_status = request.form.get('listing_status', 'new')

    try:
        result = runner.do_dscr_quote(listing_status)
        flash('DSCR quote generation completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/send-emails', methods=['POST'])
def send_emails():
    """Send conventional quote emails via API"""
    debug = request.form.get('debug', 'false') == 'true'

    try:
        result = runner.do_email(debug)
        flash('Email sending completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/send-dscr-emails', methods=['POST'])
def send_dscr_emails():
    """Send DSCR quote emails via API"""
    debug = request.form.get('debug', 'false') == 'true'

    try:
        result = runner.do_dscr_email(debug)
        flash('DSCR email sending completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/dscr-pricing', methods=['POST'])
def dscr_pricing():
    """Add DSCR pricing"""
    try:
        result = runner.do_dscr_pricing()
        flash('DSCR pricing completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/archive', methods=['POST'])
def archive():
    """Archive tables to CSV"""
    try:
        result = runner.do_archive()
        flash('Archive completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))


@workflow_bp.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up archived records"""
    confirm = request.form.get('confirm', 'false')

    if confirm != 'true':
        flash('Cleanup requires confirmation. Please check the confirmation box.', 'warning')
        return redirect(url_for('workflow.index'))

    try:
        result = runner.do_clean_up()
        flash('Cleanup completed - check status for details', 'success' if result else 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('workflow.index'))
