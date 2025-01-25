import time  # Importing the time module for handling time-related tasks

from PIL import Image, ImageDraw, ImageFont  # Importing PIL modules for image manipulation
import requests  # Importing requests for making HTTP requests
from io import BytesIO  # Importing BytesIO for handling binary data
import os  # Importing os for interacting with the operating system
from bs4 import BeautifulSoup  # Importing BeautifulSoup for parsing HTML content
import cloudscraper  # Importing cloudscraper to bypass anti-bot measures

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
}

# Function to calculate the total V-Bucks from the data
def calculate_total_vbucks(data):
    total = 0
    for item in data:
        total += int(item['vbucks'].split('x')[0].strip())  # Summing up the V-Bucks
    return f"{total}x V-Bucks Today"  # Returning the total as a formatted string

def fetch_with_retry(url, headers=None, timeout=10,has_scraper=None):
    if has_scraper:
        scraper = cloudscraper.create_scraper()
        while True:
            try:
                response = scraper.get(url=url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response
                elif "Just a moment" in response.text:
                    print("Error")
                    print(response.text)
                else:
                    print(f"Received status code {response.status_code}, retrying...")
            except Exception as e:
                print("Error in connection:", e, time.ctime(time.time()))
            time.sleep(2)
    else:
        while True:
            try:
                response = requests.get(url=url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response
                elif "Just a moment" in response.text:
                    print("Error")
                    print(response.text)
                else:
                    print(f"Received status code {response.status_code}, retrying...")
            except Exception as e:
                print("Error in connection:", e, time.ctime(time.time()))
            time.sleep(2)

# Function to create an image of the table
def create_table_image(data):
    # Custom colors for different badges
    colors = {
        'header_bg': (30, 30, 30),
        'T': (128, 0, 128),  # Dark purple
        'C': (205, 133, 63),  # Brownish orange
        'P': (0, 100, 0),  # Dark green
        'S': (160, 160, 160)  # Silver
    }

    # Increasing the image resolution
    scale_factor = 3  # Scaling factor for higher resolution
    table_width = 400 * scale_factor
    header_height = 70 * scale_factor
    row_height = 60 * scale_factor
    padding = 30 * scale_factor

    # Loading custom fonts
    try:
        font_path = os.path.join("fonts", "fortnite.otf")
        title_font = ImageFont.truetype(font_path, 26 * scale_factor)
        text_font = ImageFont.truetype(font_path, 20 * scale_factor)
    except:
        title_font = ImageFont.truetype("arial.ttf", 26 * scale_factor)
        text_font = ImageFont.truetype("arial.ttf", 22 * scale_factor)

    # Calculating the total height of the image
    total_height = header_height + (len(data) * row_height) + padding

    # Creating the image
    img = Image.new('RGB', (table_width, total_height), (44, 47, 51))
    draw = ImageDraw.Draw(img)

    # Drawing the header
    header_text = calculate_total_vbucks(data)
    draw.rectangle([0, 0, table_width, header_height], fill=colors['header_bg'])
    image_path = "vbucks.png"  # Path to the V-Bucks image
    image = Image.open(image_path).convert('RGBA')
    image = image.resize((30 * scale_factor, 30 * scale_factor), resample=Image.LANCZOS)  # Resizing the image

    # Drawing the header text (centered horizontally)
    bbox = draw.textbbox((0, 0), header_text, font=title_font)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((table_width - text_w + 10) // 2, (header_height - 30 * scale_factor) // 2),
        header_text,
        font=title_font,
        fill=(255, 255, 255)
    )
    img.paste(image, ((table_width - text_w - 60 * scale_factor) // 2, (header_height - 35 * scale_factor) // 2), image)

    # Drawing the table rows
    y = header_height + 20 * scale_factor
    for index, item in enumerate(data):
        x = padding

        # Drawing the badge with a shadow
        badge_bg = colors.get(item['badge'], (0, 0, 0))
        draw.rounded_rectangle(
            (x + 12 * scale_factor, y + 12 * scale_factor, x + 42 * scale_factor, y + 42 * scale_factor),
            radius=8 * scale_factor,
            fill=badge_bg,
            outline=(255, 255, 255),
            width=2 * scale_factor
        )

        # Drawing the badge text
        bbox = draw.textbbox((0, 0), item['badge'], font=text_font)
        draw.text(
            (x + 27 * scale_factor - (bbox[2] // 2), y + 19 * scale_factor),
            item['badge'],
            font=text_font,
            fill=(255, 255, 255)
        )

        # Drawing the PWR value
        x += 100 * scale_factor
        draw.text(
            (x, y + 20 * scale_factor),
            f"{item['pwr']}",
            font=text_font,
            fill=(255, 255, 255)
        )

        # Loading and pasting the image from the URL
        if 'image_url' in item:
            response = fetch_with_retry(url=item['image_url'], headers=headers, timeout=10)
            image = Image.open(BytesIO(response.content)).convert('RGBA')
            image = image.resize((20 * scale_factor, 20 * scale_factor), resample=Image.LANCZOS)
            img.paste(image, (x - 30 * scale_factor, y + 19 * scale_factor), image)

        # Drawing the V-Bucks value
        x += 110 * scale_factor
        draw.text(
            (x, y + 20 * scale_factor),
            item['vbucks'],
            font=text_font,
            fill=(255, 255, 255)
        )

        # Drawing a separator line (only if not the last item)
        if index < len(data) - 1:
            draw.line(
                [(padding, y + 55 * scale_factor), (table_width - padding, y + 55 * scale_factor)],
                fill=(180, 180, 180),
                width=3 * scale_factor
            )

        y += row_height
    return img

# Function to extract data from a table row
def extract_data_from_row(row):
    # Extracting the badge
    badge_span = row.find('span', class_='badge')
    if not badge_span:
        return None  # Skip rows without a badge
    badge = badge_span.text.strip()

    # Extracting the image URL
    img_tag = row.find('img')
    if img_tag and 'src' in img_tag.attrs:
        image_url = img_tag['src']
    else:
        # If the image is not found directly, search within <noscript>
        noscript_tag = row.find('noscript')
        if noscript_tag:
            img_tag = noscript_tag.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
            else:
                return None  # Skip rows without an image
        else:
            return None  # Skip rows without an image

    # Extracting the PWR value
    pwr_td = row.find('td', class_='right')
    if not pwr_td:
        return None  # Skip rows without a PWR value
    pwr = pwr_td.text.strip()

    # Extracting the V-Bucks value
    vbucks_td = row.find('td', class_='cell col mythic--border-small')
    if not vbucks_td:
        return None  # Skip rows without a V-Bucks value
    vbucks = vbucks_td.get_text(strip=True)

    # Returning the extracted data
    return {
        "badge": badge,
        "image_url": image_url,
        "pwr": pwr,
        "vbucks": vbucks
    }

# Function to scrape data from the website
def grap_data():
    response = fetch_with_retry("https://v2.fortnitedb.com/", timeout=10, has_scraper=True)

    html_content = response.text

    # Parsing the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Finding the specific table
    table = soup.find('table', class_='summary-honorable summary-wrapper')
    if not table:
        raise ValueError("The required table was not found.")

    # Extracting data from the table
    data = []
    for row in table.find_all('tr'):
        row_data = extract_data_from_row(row)
        if row_data:  # If data is successfully extracted
            data.append(row_data)

    # Saving the created table image
    create_table_image(data).save('Daily Missions.png')

# You can call this Function in your project to make image
grap_data()