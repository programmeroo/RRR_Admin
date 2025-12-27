def old_do_archive():
    """
    Archive tables to CSV with pagination support for large tables.

    SAFETY: This function marks records as archived BUT cleanup must be run separately.
    Always verify CSV files exist and are complete before running cleanup!

    Archive Order (per user requirements):
    1. Get all contacts (no archiving, just export all)
    2. Get all emails (no archiving, just export all)
    3. Get archived quotes and dscr_quotes (already archived)
    4. Archive expired listings (marks them as archived)
    5. Get email_reports and colisters (filtered by archived listings)
    """


    # update_status("do_archive", "Archiving tables...")
    # try:
    #     ts = datetime.now().strftime("%Y%m%d_%H%M")
    #     export_dir = EXPORT_ROOT / f"archive_{ts}"
    #     export_dir.mkdir(parents=True, exist_ok=True)

    #     archive_summary = []  # Track what was archived
    #     per_page = 1000  # Fetch 1000 records per page

    #     def fetch_and_save(table, mark_as_archived=False):
    #         """Helper function to fetch and save a table"""
    #         update_status("do_archive", f"Processing {table}...")

    #         # Mark records as archived if requested
    #         if mark_as_archived:
    #             archive_response, status_code = api.archive_table(table=table)
    #             if status_code != 200:
    #                 update_status("do_archive", f"❌ Error marking {table} as archived: HTTP {status_code}", error=True)
    #                 archive_summary.append(f"❌ {table}: Failed to mark (HTTP {status_code})")
    #                 return False
    #             marked_count = archive_response.get("count", 0)
    #             update_status("do_archive", f"Marked {table}: {marked_count} rows")

    #         # Fetch records with pagination
    #         all_records = []
    #         page = 1
    #         fetch_failed = False

    #         while True:
    #             update_status("do_archive", f"Fetching {table} page {page}...")
    #             get_response, status_code = api.get_archive(table=table, page=page, per_page=per_page)

    #             if status_code != 200:
    #                 update_status("do_archive", f"❌ Error fetching {table} page {page}: HTTP {status_code}", error=True)
    #                 fetch_failed = True
    #                 break

    #             # Parse paginated response
    #             if isinstance(get_response, dict) and "records" in get_response:
    #                 records = get_response.get("records", [])
    #                 total_pages = get_response.get("total_pages", 1)
    #                 current_page = get_response.get("current_page", page)
    #                 total_records = get_response.get("total_records", 0)

    #                 if records:
    #                     all_records.extend(records)
    #                     update_status("do_archive", f"Fetched {table} page {current_page}/{total_pages} ({len(all_records)}/{total_records} records)")

    #                 if current_page >= total_pages:
    #                     break
    #                 page += 1
    #             elif isinstance(get_response, list):
    #                 # Non-paginated response
    #                 all_records.extend(get_response)
    #                 update_status("do_archive", f"Fetched {table}: {len(get_response)} records (non-paginated)")
    #                 break
    #             else:
    #                 update_status("do_archive", f"❌ Unexpected response format for {table}", error=True)
    #                 fetch_failed = True
    #                 break

    #         # CRITICAL SAFETY CHECK
    #         if fetch_failed:
    #             archive_summary.append(f"❌ {table}: FETCH FAILED - NOT backed up!")
    #             update_status("do_archive", f"⚠️  WARNING: {table} export failed!", error=True)
    #             return False

    #         if not all_records:
    #             archive_summary.append(f"⏭️  {table}: No records to archive")
    #             update_status("do_archive", f"No {table} records to archive")
    #             return True

    #         # Write to CSV
    #         try:
    #             df = pd.DataFrame(all_records)
    #             file_path = export_dir / f"{table}_{ts}.csv"
    #             df.to_csv(file_path, index=False)

    #             if file_path.exists() and file_path.stat().st_size > 0:
    #                 update_status("do_archive", f"✅ Saved {table}: {len(all_records)} records to {file_path.name}")
    #                 archive_summary.append(f"✅ {table}: {len(all_records)} records saved to CSV")
    #                 return True
    #             else:
    #                 archive_summary.append(f"❌ {table}: CSV SAVE FAILED - NOT backed up!")
    #                 update_status("do_archive", f"❌ ERROR: {table} CSV file not created!", error=True)
    #                 return False
    #         except Exception as csv_error:
    #             archive_summary.append(f"❌ {table}: CSV ERROR - {str(csv_error)}")
    #             update_status("do_archive", f"❌ ERROR saving {table} CSV: {str(csv_error)}", error=True)
    #             return False

    #     # STEP 1: Get all contacts (no archiving needed)
    #     fetch_and_save("contacts", mark_as_archived=False)

    #     # STEP 2: Get all emails (no archiving needed)
    #     fetch_and_save("emails", mark_as_archived=False)

    #     # STEP 3: Get archived quotes and dscr_quotes
    #     fetch_and_save("quotes", mark_as_archived=True)
    #     fetch_and_save("dscr_quotes", mark_as_archived=True)

    #     # STEP 4: Archive expired listings
    #     fetch_and_save("listings", mark_as_archived=True)

    #     # STEP 5: Get email_reports and colisters (filtered by archived listings)
    #     fetch_and_save("email_reports", mark_as_archived=False)
    #     fetch_and_save("colisters", mark_as_archived=False)

    #     # Print summary
    #     update_status("do_archive", "📋 Archive Summary:")
    #     for summary_line in archive_summary:
    #         update_status("do_archive", f"  {summary_line}")

    #     update_status("do_archive", f"")
    #     update_status("do_archive", f"✅ Archive process completed: {export_dir}")
    #     update_status("do_archive", f"⚠️  IMPORTANT: Verify CSV files before running CLEANUP!")
    #     update_status("do_archive", f"⚠️  Check {export_dir} for all expected files")

    #     return True
    # except Exception as e:
    #     update_status("do_archive", f"❌ CRITICAL Error: {str(e)}", error=True)
    #     return False
