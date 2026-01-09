import os
import json
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
from services.database_access import add_contact, add_listing_dict, add_colister, set_server, get_listing
from services.scrape_homes import count_filtered_pages
from datetime import datetime
from services.my_logger import log


PAGES_FOLDER = r"C:/LOCAL_PROJECTS/RRR_LOGS/pages"
PROCESSED_FOLDER = r"C:/LOCAL_PROJECTS/RRR_LOGS/processed"
FAILED_FOLDER = r"C:/LOCAL_PROJECTS/RRR_LOGS/failed"
LOGS_FOLDER = r"C:/LOCAL_PROJECTS/RRR_LOGS/logs"


def extract_details_url_from_offers(json_data):
    if isinstance(json_data, dict) and "@graph" in json_data:
        for item in json_data["@graph"]:
            if isinstance(item, dict):
                types = item.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if "Product" in types or "RealEstateListing" in types:
                    offers = item.get("offers", {})
                    if isinstance(offers, dict) and "url" in offers:
                        return offers["url"]
    return None


def get_agents(html_content, property_data):
    agent_list = property_data.get("offers", {}).get("offeredBy", [])
    if isinstance(agent_list, dict):
        agent_list = [agent_list]

    agents = []
    for agent in agent_list:
        name = str(agent.get("name", "N/A"))
        agents.append({
            "first_name": name.split(" ")[0],
            "last_name": name.split(" ")[-1],
            "company": agent.get("memberOf", {}).get("name", "N/A"),
            "phone": agent.get("telephone", "N/A"),
            "email_address": agent.get("email", "N/A"),
            "license": ""
        })

    soup = BeautifulSoup(html_content, "html.parser")
    license_tags = soup.find_all('span', class_='agent-information-license-number')
    for i, tag in enumerate(license_tags):
        if i < len(agents):
            agents[i]["license"] = tag.text.replace("License #", "").strip()

    log(f"🆔 Found {len(license_tags)} license tags, {len(agents)} agents.")
    return agents


def get_files_in_folder(folder_path):
    return [f.name for f in Path(folder_path).iterdir() if f.is_file()]


def get_json_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    json_script = soup.find("script", type="application/ld+json")
    return json.loads(json_script.string)


def get_details(html_content):
    listing = {}
    soup = BeautifulSoup(html_content, "html.parser")

    try:
        json_data = get_json_data(html_content)
        details_url = extract_details_url_from_offers(json_data)

        if not details_url:
            canonical = soup.find("link", rel="canonical")
            if canonical and canonical.get("href"):
                details_url = canonical["href"]

        property_data = next((item for item in json_data["@graph"] if "RealEstateListing" in item["@type"]), None)
        if not property_data:
            log("⚠️ No property details found in JSON")
            return None

        address_data = property_data.get("mainEntity", {}).get("address", {})
        address = address_data.get("streetAddress", "N/A")
        city = address_data.get("addressLocality", "N/A").replace(' ', '-')
        region = address_data.get("addressRegion", "N/A")
        zipcode = address_data.get("postalCode", "N/A")
        city_state = '-'.join([city, region]).lower()

        price = property_data.get("offers", {}).get("price", "0")
        main_entity = property_data.get("mainEntity", {})
        beds = main_entity.get("numberOfBedrooms", "0")
        baths = main_entity.get("numberOfBathroomsTotal", "0")
        sqft = main_entity.get("floorSize", {}).get("value", "0")
        entity_type = main_entity.get("@type", "N/A")
        listing_type = "house" if entity_type == "SingleFamilyResidence" else "condo"

        mls_number = "N/A"
        try:
            mls_tag = soup.find('p', class_="mls-number")
            spans = mls_tag.find_all('span')
            if len(spans) > 1:
                mls_number = spans[1].text.strip()
                log(f"mls-number found: {mls_number}")
        except Exception:
            log("⚠️ MLS Number not found")

        listing = {
            "mls_number": mls_number,
            "city_state": city_state,
            "listing_type": listing_type,
            "details_url": details_url,
            "property_address": address,
            "zipcode": zipcode,
            "price": price,
            "beds": beds,
            "baths": baths,
            "sq_ft": sqft
        }

    except Exception as e:
        log(f"❌ Failed to extract detail_data: {e}")
        return None

    agents = get_agents(html_content, property_data)
    return listing, agents


def move_to_failed(file_name):
    os.makedirs(FAILED_FOLDER, exist_ok=True)
    src = os.path.join(PAGES_FOLDER, file_name)
    dst = os.path.join(FAILED_FOLDER, file_name)
    shutil.move(src, dst)
    log(f"❌ Moved to failed: {file_name}")


def move_to_processed(file_name):
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    src = os.path.join(PAGES_FOLDER, file_name)
    dst = os.path.join(PROCESSED_FOLDER, file_name)
    shutil.move(src, dst)
    log(f"📂 Moved to processed: {file_name}")


def new_listing(listing, agents):
    log(f"new_listing: {listing["mls_number"]}")
    
    found_listing, status_code = get_listing(listing["mls_number"])
    if status_code == 200:
        log(f"Listing exists: {listing["mls_number"]}")
        return False
    
    lister, status_code = add_contact(agents[0])
    log("add_contact lister")
    if status_code != 201:
        return False

    listing["lister_id"] = lister.get("id")
    new_listing, status_code = add_listing_dict(listing)
    if status_code != 201:
        return False

    if len(agents) > 1:
        colister, status_code = add_contact(agents[1])
        log("add_contact colister")
        if status_code == 201:
            new_colister, status_code = add_colister(
                mls_number=listing["mls_number"],
                colister_id=colister["id"]
            )
            log("add_colister")
            return status_code == 201
        return False

    return True


def process_page(file_name):
    try:
        file_path = Path(PAGES_FOLDER) / file_name
        with open(file_path, encoding="utf-8") as f:
            html_data = f.read()
            result = get_details(html_data)

            if not result:
                log(f"❌ Skipping file {file_name} due to missing details.")
                return False

            listing, agents = result
            if new_listing(listing, agents):
                log(f"✅ process_page: {file_name} success")
                return True

    except FileNotFoundError:
        log(f"❌ File not found: {file_name}")
    except Exception as e:
        log(f"❌ Unexpected error processing {file_name}: {e}")

    return False


def process_pages():
    page_count = count_filtered_pages(PAGES_FOLDER)
    page_list = get_files_in_folder(PAGES_FOLDER)

    log(f"📄 Total pages to process: {page_count}")

    for file_name in page_list:
        success = process_page(file_name)
        if not success:
            move_to_failed(file_name)


if __name__ == "__main__":
    set_server("local")
    process_pages()
