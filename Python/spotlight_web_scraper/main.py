import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random

def create_output_folder():
    """Create the spotlight_images folder if it doesn't exist"""
    folder_name = "./spotlight_images"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created folder: {folder_name}")
    return folder_name

def get_session_with_headers():
    """Create a session with browser-like headers to avoid 403 errors"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def extract_high_res_url(html_content, page_url):
    """Extract the high-resolution image URL from the HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for images in wp-content/uploads directory
    # These are typically the high-res versions
    img_tags = soup.find_all('img')
    
    for img in img_tags:
        src = img.get('src', '')
        if 'wp-content/uploads' in src and src.endswith(('.jpg', '.jpeg', '.png')):
            # Convert relative URLs to absolute URLs
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(page_url, src)
            return src
    
    # Alternative: look for links to images
    links = soup.find_all('a')
    for link in links:
        href = link.get('href', '')
        if 'wp-content/uploads' in href and href.endswith(('.jpg', '.jpeg', '.png')):
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = urljoin(page_url, href)
            return href
    
    return None

def download_image(session, image_url, output_folder):
    """Download an image from the given URL"""
    try:
        # Extract filename from URL
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        
        # If no filename extension, add .jpg
        if not filename.endswith(('.jpg', '.jpeg', '.png')):
            filename += '.jpg'
        
        filepath = os.path.join(output_folder, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            print(f"  File already exists: {filename}")
            return True
        
        # Download the image
        response = session.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  Downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"  Error downloading image: {e}")
        return False

def scrape_spotlight_images(start_page=20, end_page=30):
    """Main function to scrape Windows 10 Spotlight images"""
    print("Starting Windows 10 Spotlight image scraper...")
    
    # Create output folder
    output_folder = create_output_folder()
    
    # Create session with browser headers
    session = get_session_with_headers()
    
    base_url = "https://windows10spotlight.com/images/"
    downloaded_count = 0
    skipped_count = 0
    
    for page_num in range(start_page, end_page + 1):
        page_url = f"{base_url}{page_num}"
        print(f"\nProcessing page {page_num}: {page_url}")
        
        try:
            # Get the page content
            response = session.get(page_url)
            
            # Check for 404 or other errors
            if response.status_code == 404:
                print(f"  Page {page_num} not found (404), skipping...")
                skipped_count += 1
                continue
            
            response.raise_for_status()
            
            # Extract high-resolution image URL
            high_res_url = extract_high_res_url(response.text, page_url)
            high_res_url = clean_image_url(high_res_url)
            if high_res_url:
                print(f"  Found high-res image: {high_res_url}")
                
                # Download the image
                if download_image(session, high_res_url, output_folder):
                    downloaded_count += 1
                else:
                    skipped_count += 1
            else:
                print(f"  No high-res image found on page {page_num}")
                skipped_count += 1
            
            # Add a small delay to be respectful to the server
            #time.sleep(random.uniform(1, 2))
            
        except requests.exceptions.RequestException as e:
            print(f"  Error accessing page {page_num}: {e}")
            skipped_count += 1
            continue
    
    print(f"\n=== Scraping Complete ===")
    print(f"Downloaded: {downloaded_count} images")
    print(f"Skipped: {skipped_count} pages/images")
    print(f"Images saved to: {output_folder}")

def clean_image_url(url):
    """
    Removes the '-WIDTHxHEIGHT' part before the file extension in an image URL.

    Args:
        url (str): The image URL to clean.

    Returns:
        str: The cleaned URL.
    """
    if url is None:
        return None
    return re.sub(r'-\d+x\d+(?=\.\w+$)', '', url)

# Example usage:
url = 'https://windows10spotlight.com/wp-content/uploads/2016/10/244c78a0df569a336ee00eab323cad79-1024x576.jpg'
cleaned_url = clean_image_url(url)
print(cleaned_url)

if __name__ == "__main__":
    # You can modify these parameters as needed
    START_PAGE = 38867
    END_PAGE = 38867
    
    scrape_spotlight_images(START_PAGE, END_PAGE)