"""
Background Workflow Runner for RRR_Admin
Runs multi-step workflows like the TKinter app
"""

from services import database_access as api
from services import process_listings, scrape_homes, scrape_pricing, dscr_pricing
from services.my_logger import log
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import time
import threading

# Global workflow status
workflow_status = {
    'running': False,
    'current_task': None,
    'progress': [],
    'errors': [],
    'started_at': None,
    'completed_at': None
}

EXPORT_ROOT = Path("C:/LOCAL_PROJECTS/RateReadyRealtor/RRR_LOGS/archive")


def update_status(task_name, message, error=False):
    """Update workflow status"""
    global workflow_status
    entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'task': task_name,
        'message': message
    }

    if error:
        workflow_status['errors'].append(entry)
    else:
        workflow_status['progress'].append(entry)

    workflow_status['current_task'] = task_name
    log(f"{task_name}: {message}")


def get_workflow_status():
    """Get current workflow status"""
    return workflow_status.copy()


def do_pricing():
    """Scrape mortgage pricing from LoanFactory"""
    update_status("do_pricing", "Starting pricing scrape...")
    try:
        result = scrape_pricing.do_all_pricing()
        update_status("do_pricing", f"Pricing complete: {result}")
        return True
    except Exception as e:
        update_status("do_pricing", f"Error: {str(e)}", error=True)
        return False


def do_scrape():
    """Copy HTML files from Downloads"""
    update_status("do_scrape", "Scraping HTML files from Downloads...")
    try:
        count = scrape_homes.do_scrape_listings()
        update_status("do_scrape", f"Scraped {count} files")
        return True
    except Exception as e:
        update_status("do_scrape", f"Error: {str(e)}", error=True)
        return False


def do_process_pages():
    """Process HTML listings"""
    update_status("do_process_pages", "Processing listing HTML files...")
    try:
        result = process_listings.process_pages()
        update_status("do_process_pages", f"Processed listings: {result}")
        return True
    except Exception as e:
        update_status("do_process_pages", f"Error: {str(e)}", error=True)
        return False


def do_quote(listing_status='new'):
    """Generate conventional/FHA/VA quotes"""
    update_status("do_quote", f"Generating quotes for {listing_status} listings...")
    try:
        result, status_code = api.add_quotes(listing_status=listing_status)
        count = result.get('count', 0) if isinstance(result, dict) else 0
        update_status("do_quote", f"Generated {count} quotes")
        return status_code in [200, 201]
    except Exception as e:
        update_status("do_quote", f"Error: {str(e)}", error=True)
        return False


def do_dscr_quote(listing_status='new'):
    """Generate DSCR quotes"""
    update_status("do_dscr_quote", f"Generating DSCR quotes for {listing_status} listings...")
    try:
        result, status_code = api.add_dscr_quotes(listing_status=listing_status)
        count = result.get('count', 0) if isinstance(result, dict) else 0
        update_status("do_dscr_quote", f"Generated {count} DSCR quotes")
        return status_code in [200, 201]
    except Exception as e:
        update_status("do_dscr_quote", f"Error: {str(e)}", error=True)
        return False


def do_email(debug=False):
    """Send conventional quote emails in batches"""
    update_status("do_email", f"Sending emails (debug={debug})...")
    try:
        total_sent = send_email_batches(debug=debug, dscr=False, batch_size=25)
        update_status("do_email", f"Sent {total_sent} emails")
        return total_sent > 0
    except Exception as e:
        update_status("do_email", f"Error: {str(e)}", error=True)
        return False


def do_dscr_email(debug=False):
    """Send DSCR quote emails in batches"""
    update_status("do_dscr_email", f"Sending DSCR emails (debug={debug})...")
    try:
        total_sent = send_email_batches(debug=debug, dscr=True, batch_size=25)
        update_status("do_dscr_email", f"Sent {total_sent} DSCR emails")
        return total_sent > 0
    except Exception as e:
        update_status("do_dscr_email", f"Error: {str(e)}", error=True)
        return False


def do_dscr_pricing():
    """Add DSCR pricing"""
    update_status("do_dscr_pricing", "Adding DSCR pricing...")
    try:
        count, status = dscr_pricing.dscr_pricing()
        update_status("do_dscr_pricing", f"Added {count} DSCR prices")
        return status
    except Exception as e:
        update_status("do_dscr_pricing", f"Error: {str(e)}", error=True)
        return False


def do_archive():
    archive_response, status_code = api.archive_listings()
    if status_code != 200:
        update_status("do_archive", f"❌ Error archive_listings: HTTP {status_code}", error=True)
        update_status("do_archive", f"❌ Archive_listings: Failed to mark (HTTP {status_code})")
        return False
    marked_count = archive_response.get("count", 0)
    update_status("do_archive", f"Archive listings: {marked_count} rows")
    return True


def do_clean_up():
    """Delete archived records from database"""
    update_status("do_clean_up", "Cleaning up archived records...")
    success = True

    try:
        # Purge API logs (optional - may not be implemented on server)
        before_date = datetime.now() - timedelta(days=30)
        try:
            api_purge_response, status_code = api.purge_api_log(log="api_log", before=before_date.strftime("%Y-%m-%d"))
            if status_code == 200:
                update_status("do_clean_up", f"Purged API Logs: {api_purge_response}")
            else:
                update_status("do_clean_up", f"API log purge not available (HTTP {status_code}) - skipping")
        except Exception as e:
            update_status("do_clean_up", f"API log purge not available - skipping")

        # Delete archived records for each table
        try:
            deleted_count, status_code = api.delete_archives()
            if status_code == 200:
                update_status("do_clean_up", f"Purged archived records: {deleted_count}")
            elif status_code == 404:
                update_status("do_clean_up", "Archive deletion not available on server - skipping")
            else:
                update_status("do_clean_up", f"Warning: Archive deletion returned HTTP {status_code}")
                success = False
        except Exception as e:
            update_status("do_clean_up", f"Archive deletion not available - skipping")

        return success

    except Exception as e:
        update_status("do_clean_up", f"Error: {str(e)}", error=True)
        return False


def send_email_batches(debug=False, dscr=False, batch_size=25):
    """Send emails in batches with delays"""
    total_sent = 0
    batch_num = 1

    while True:
        update_status("send_emails", f"Processing batch #{batch_num}...")

        response, status_code = api.add_emails(debug=debug, dscr=dscr, max_send_count=batch_size)

        if status_code == 201:
            sent = response.get("emails_sent", 0)
            total_sent += sent
            update_status("send_emails", f"Batch #{batch_num}: {sent} emails sent (total: {total_sent})")

            if sent == 0:
                break

            batch_num += 1
            time.sleep(2)  # Delay between batches
        else:
            break

    return total_sent


def run_workflow(workflow, **kwargs):
    """
    Run a workflow in the background
    workflow: list of task functions to run sequentially
    kwargs: parameters like listing_status, debug
    """
    global workflow_status

    def _run():
        global workflow_status
        workflow_status = {
            'running': True,
            'current_task': None,
            'progress': [],
            'errors': [],
            'started_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed_at': None
        }

        update_status("workflow", f"Starting workflow with {len(workflow)} tasks")

        for task_func in workflow:
            task_name = task_func.__name__
            try:
                # Call task with appropriate parameters
                if task_name in ['do_quote', 'do_dscr_quote']:
                    result = task_func(kwargs.get('listing_status', 'new'))
                elif task_name in ['do_email', 'do_dscr_email']:
                    result = task_func(kwargs.get('debug', False))
                else:
                    result = task_func()

                if not result:
                    update_status(task_name, "Task returned False - continuing anyway", error=True)

            except Exception as e:
                update_status(task_name, f"Exception: {str(e)}", error=True)

        workflow_status['running'] = False
        workflow_status['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        workflow_status['current_task'] = None
        update_status("workflow", "Workflow completed")

    # Run in background thread
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return True


# Predefined workflows

# Main Workflow: Data Pipeline (Insert & Process Listings, Maintain Database)
WORKFLOW_MAIN = [
    do_scrape,
    do_process_pages,
    do_archive,
    do_clean_up
]

# Weekly Reports Workflow: Handled by API endpoint /api/report/run
# See workflow_routes.py run_reports() which calls api.run_reports()
# Supports: week parameter (1-4 or empty for all), debug mode

# Legacy workflows (for backwards compatibility)
WORKFLOW_QM = [
    do_scrape,
    do_process_pages,
    do_quote,
    do_email,
    do_archive,
    do_clean_up
]

WORKFLOW_QUOTE_EMAIL = [
    do_quote,
    do_email,
]

WORKFLOW_DSCR = [
    do_dscr_pricing,
    do_dscr_quote,
    do_dscr_email
]

WORKFLOW_PROCESS_ONLY = [
    do_scrape,
    do_process_pages
]
