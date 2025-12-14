"""
Background Workflow Runner for RRR_Admin
Runs multi-step workflows like the TKinter app
"""

from services import database_access as api
from services import process_listings, scrape_homes, scrape_pricing, dscr_pricing
from services.my_logger import log
from datetime import datetime
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

EXPORT_ROOT = Path("C:/LOCAL_PROJECTS/RateReadyRealtor/archive")


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
        count = scrape_homes.scrape()
        update_status("do_scrape", f"Scraped {count} files")
        return True
    except Exception as e:
        update_status("do_scrape", f"Error: {str(e)}", error=True)
        return False


def do_process_pages():
    """Process HTML listings"""
    update_status("do_process_pages", "Processing listing HTML files...")
    try:
        result = process_listings.process_files()
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
    """Archive tables to CSV"""
    update_status("do_archive", "Archiving tables...")
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        export_dir = EXPORT_ROOT / f"archive_{ts}"
        export_dir.mkdir(parents=True, exist_ok=True)
        tables = ["emails", "colisters", "quotes", "listings", "daily_prices"]

        for table in tables:
            archive_response, status_code = api.archive_table(table=table)
            count = archive_response.get("count", "unknown")
            update_status("do_archive", f"Archived {table}: {count} rows")

            get_response, status_code = api.get_archive(table=table)
            if status_code == 200 and get_response:
                df = pd.DataFrame(get_response) if isinstance(get_response, list) else pd.DataFrame([get_response])
                if not df.empty:
                    file_path = export_dir / f"{table}_{ts}.csv"
                    df.to_csv(file_path, index=False)

        update_status("do_archive", f"Archive completed: {export_dir}")
        return True
    except Exception as e:
        update_status("do_archive", f"Error: {str(e)}", error=True)
        return False


def do_clean_up():
    """Delete archived records from database"""
    update_status("do_clean_up", "Cleaning up archived records...")
    try:
        current_date = datetime.now()
        api.purge_api_log(before=current_date.strftime("%Y-%m-%d"))

        for table in ["daily_prices", "listings", "quotes"]:
            response, status_code = api.delete_archive(table)
            update_status("do_clean_up", f"Deleted {table} archive")

        update_status("do_clean_up", "Cleanup completed")
        return True
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


# Predefined workflows (like in TKinter app)
WORKFLOW_QM = [
    do_pricing,
    do_scrape,
    do_process_pages,
    do_quote,
    do_email,
    do_archive,
    do_clean_up
]

WORKFLOW_QUOTE_EMAIL = [
    do_quote,
    do_email
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
