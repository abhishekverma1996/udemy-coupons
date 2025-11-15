import os
import requests
import json
from time import sleep

# Load URLs from environment variables
BASE_LIST_URL = os.getenv("BASE_LIST_URL")
BASE_DETAIL_URL = os.getenv("BASE_DETAIL_URL")

OUTPUT_FILE = "website/coupons.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_page(page_number):
    url = BASE_LIST_URL.format(page_number)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_course_details(slug):
    url = BASE_DETAIL_URL.format(slug)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def main():
    all_courses = []
    
    # Step 1: Get total pages
    first_page = fetch_page(1)
    total_pages = first_page.get("totalPages", 1)
    
    print(f"Total pages to fetch: {total_pages}")
    
    # Step 2: Loop through each page
    for page in range(1, total_pages + 1):
        print(f"Fetching page {page}...")
        page_data = fetch_page(page)
        courses = page_data.get("courses", [])
        
        for course in courses:
            slug = course.get("slug")
            if not slug:
                continue
            
            try:
                details = fetch_course_details(slug)
                
                # Build final course object
                course_info = {
                    "id": details.get("id"),
                    "name": details.get("name"),
                    "description": details.get("description"),
                    "content": details.get("content"),
                    "shoer_description": details.get("shoer_description"),
                    "price": details.get("price"),
                    "sale_price": details.get("sale_price"),
                    "sale_start": details.get("sale_start"),
                    "sale_end": details.get("sale_end"),
                    "lectures": details.get("lectures"),
                    "views": details.get("views"),
                    "rating": details.get("rating"),
                    "image": details.get("image"),
                    "url": details.get("url"),
                    "store": details.get("store"),
                    "type": details.get("type"),
                    "slug": details.get("slug"),
                    "category": details.get("category"),
                    "tags": details.get("tags"),
                    "subcategory": details.get("subcategory"),
                    "language": details.get("language"),
                    "courseid": details.get("courseid")
                }
                
                all_courses.append(course_info)
                sleep(0.5)

            except Exception as e:
                print(f"Failed to fetch details for {slug}: {e}")

    # Step 3: Save JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(all_courses)} courses to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
