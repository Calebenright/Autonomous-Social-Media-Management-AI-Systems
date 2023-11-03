
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
import textwrap
import json
import openai
import re
from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
from io import BytesIO
import requests
import ast
import tempfile
import xml.etree.ElementTree as ET

from decouple import config
openai.api_key = config('OPENAI_API_KEY')

# ---------------------- Utility Functions --------------------- #

def remove_emojis(text):
    emoji_pattern = re.compile("["
                        u"\U0001F600-\U0001F64F"  # emoticons
                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                        u"\U0001F700-\U0001F77F"  # alchemical symbols
                        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
                        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                        u"\U00002702-\U000027B0"  # Dingbats
                        u"\U000024C2-\U0001F251" 
                        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def hex_to_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

def is_dark_color(r, g, b):
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < 128

def recolor_image(img, color):
    r, g, b, a = img.split()
    grayscale = img.convert("L")
    recolored = Image.merge("RGBA", (Image.composite(Image.new("L", img.size, color[0]), grayscale, a),
                                    Image.composite(Image.new("L", img.size, color[1]), grayscale, a),
                                    Image.composite(Image.new("L", img.size, color[2]), grayscale, a),
                                    a))
    return recolored

def process_images(FOLDER_NUM, primary_color, shuffle_colors, isImage, base_image_url, imgX, imgY, imgWidth, imgHeight, bucket, isBlur, blur_amount, logo_path, isLogo, logoX, logoY, logoWidth, logoHeight,):
    
    #-------- DEPLOYMENT ----------#
    folder_path = f"graphic_design_posts/{FOLDER_NUM}/PNG"

    primary_rgb = hex_to_rgb(primary_color)
    shuffled_colors_list = [hex_to_rgb(shuffle_color) for shuffle_color in shuffle_colors]
    random.shuffle(shuffled_colors_list)
    shuffled_colors = [primary_rgb] + shuffled_colors_list
    blobs = bucket.list_blobs(prefix=folder_path)
    png_files = [blob.name for blob in blobs if blob.name.endswith('.png')]

    if isImage:
        response = requests.get(base_image_url)
        raw_image = Image.open(BytesIO(response.content))
        raw_image = raw_image.convert('RGBA')
        base_image = Image.new('RGBA', (1024, 1024), (255, 255, 255, 0))
        if isBlur:
            raw_image = raw_image.filter(ImageFilter.GaussianBlur(radius=float(blur_amount)))
        if imgWidth > 0 and imgHeight > 0:
            img_aspect = raw_image.width / raw_image.height
            box_aspect = imgWidth / imgHeight
            if img_aspect > box_aspect:
                new_height = imgHeight
                new_width = int(imgHeight * img_aspect)
            else:
                new_width = imgWidth
                new_height = int(imgWidth / img_aspect)
            resized_image = raw_image.resize((new_width, new_height), Image.ANTIALIAS)
            paste_x = imgX + (imgWidth - new_width) // 2
            paste_y = imgY + (imgHeight - new_height) // 2
            base_image.paste(resized_image, (paste_x, paste_y), resized_image)

    else:
        width, height = 1024, 1024
        blank_image = Image.new("RGBA", (width, height), "white")
        img_byte_arr = BytesIO()
        blank_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        base_image = Image.open(img_byte_arr)

    for idx, file_path in enumerate(png_files[0:]):
        blob = bucket.blob(file_path)
        img_data = blob.download_as_bytes()
        img = Image.open(BytesIO(img_data))
        file_name = os.path.basename(file_path)
        if file_name == 'logo.png':
            if isLogo and logo_path:
                recolored_img = recolor_image(img, shuffled_colors[idx])
            else:
                pass
        else:
            recolored_img = recolor_image(img, shuffled_colors[idx])
        base_image = Image.alpha_composite(base_image, recolored_img)

    if isLogo:
        response = requests.get(logo_path)
        raw_logo = Image.open(BytesIO(response.content))
        raw_logo = raw_logo.convert('RGBA')
        logo_aspect = raw_logo.width / raw_logo.height
        logo_box_aspect = logoWidth / logoHeight
        if logo_aspect > logo_box_aspect:
            new_logo_width = logoWidth
            new_logo_height = int(logoWidth / logo_aspect)
        else:
            new_logo_height = logoHeight
            new_logo_width = int(logoHeight * logo_aspect)
        resized_logo = raw_logo.resize((new_logo_width, new_logo_height), Image.ANTIALIAS)
        paste_logo_x = logoX + (logoWidth - new_logo_width) // 2
        paste_logo_y = logoY + (logoHeight - new_logo_height) // 2
        base_image.paste(resized_logo, (paste_logo_x, paste_logo_y), resized_logo)

    return base_image

def add_text_to_image(img, text, font_io, font_size, start_x, start_y, width, height, anchor_point, alignment, text_color, line_height, primary_color, hex_colors):
    font = ImageFont.truetype(font=font_io, size=font_size)
    draw = ImageDraw.Draw(img)

    r, g, b = hex_to_rgb(primary_color)
    if text_color == 'ai':
        if is_dark_color(r, g, b):
            choose_color = 'white'
        else:
            choose_color = 'black'
    elif text_color == 'primary':
            choose_color = primary_color
    elif text_color == 'secondary':
            colors_array = [hex_to_rgb(hex_color) for hex_color in hex_colors]
            choose_color = colors_array[-1]

    if anchor_point == "center":
        start_x -= width // 2
        start_y -= height // 2
    elif anchor_point == "top-right":
        start_x -= width

    while font_size > 0:
        wrapped_text = ""
        for line in text.split("\n"):
            while len(line) > 0:
                to_draw = line
                while font.getsize(to_draw)[0] > width:
                    to_draw = to_draw.rsplit(' ', 1)[0]
                wrapped_text += to_draw + "\n"
                line = line[len(to_draw):].lstrip()
        wrapped_text = wrapped_text.rstrip()

        if font.getsize_multiline(wrapped_text, spacing=int(font_size*line_height-font_size))[1] <= height:
            break

        font_size -= 1
        font = ImageFont.truetype(font=font_io, size=font_size)

    total_text_height = font.getsize_multiline(wrapped_text, spacing=int(font_size*line_height-font_size))[1]
    total_text_width = max([font.getsize(line)[0] for line in wrapped_text.split("\n")])

    if alignment == "center":
        start_y += (height - total_text_height) // 2
        start_x += (width - total_text_width) // 2
    elif alignment == "right":
        start_x += width - total_text_width

    draw.multiline_text((start_x, start_y), wrapped_text, font=font, fill=choose_color, spacing=int(font_size*line_height-font_size), align=alignment)

    return img

    
def generate_text(business_description, business_name, max_title_char_count, key):
    if key == 'Call-to-action':
        prompt = f"Imagine you're an advertiser for my company named {business_name} and our description is {business_description}. Create a ad creative headline like, 'local, personal service at a fraction of the cost.', 'Your next home could be right around the corner?', 'Name brands are so out of style.', etc.. Be creative and try to think about what might make a person click on the ad. It has to be less than {max_title_char_count} characters",
    if key == 'Headline':
        prompt = f"Imagine you're an advertiser for my company named {business_name} and our description is {business_description}. Create a ad creative call-to-action like, 'Looking to improve your style?', 'Want a Safer Home?', 'Shop our newest collection!', etc.. It has to be less than {max_title_char_count} characters",
    if key == 'Description':
        prompt = f"Imagine you're a social media manager for my company named {business_name} and our description is {business_description}. Create a catchy description that makes people understand and want us. It has to be less than {max_title_char_count} characters and avoid hashtags.",
        
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=max_title_char_count,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    try:
        print(f"Attempting to literal_eval this string: '{original_string}'")
        original_string = ast.literal_eval(original_string)
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        print(f"Problematic string: '{original_string}'")
        original_string = original_string
    caption = remove_emojis(original_string)
    if len(caption) > max_title_char_count:
        return generate_text(business_description, business_name, max_title_char_count, key)

    return caption

# ---------------------- Utility Functions ----------------------#

def generate_image_from_params(FOLDER_NUM, business_description, business_name, primary_color, specified_colors, base_image_url, logo_path):

    credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(settings.GS_BUCKET_NAME)

    # ---------------------- JSON Loading ----------------------

    # -------- DEPLOY --------#
    blob = bucket.blob(f'graphic_design_posts/{FOLDER_NUM}/settings.json')
    json_data = blob.download_as_text()
    params = json.loads(json_data)

    DEFAULT_VALUES = {
        'start_x': 0,
        'start_y': 0,
        'width': 0,
        'height': 0,
        'font_size': 0,
        'font_weight': 'normal',
        'font': 'Arial',
        'alignment': 'left',
        'anchor_point': 'top-left',
        'max_char_count': '0',
        'prompt': 'Headline',
        'text_color': 'ai',
        'line_height': '1.2',
    }

    isLogo = params.get('isLogo', False)
    logoX = params.get('logo_start_x', 0)
    logoY = params.get('logo_start_y', 0)
    logoWidth = params.get('logo_width', 150)
    logoHeight = params.get('logo_height', 150)
    isImage = params.get('isImage', False)
    imgX = params.get('img_start_x', 0)
    imgY = params.get('img_start_y', 0)
    imgWidth = params.get('img_width', 1024)
    imgHeight = params.get('img_height', 1024)
    print(imgHeight)
    isBlur = params.get('isBlur', False)
    blur_amount = params.get('blur_amount', 0)
    text_boxes = {}
    i = 1
    while True:
        key_check = f'text_box_{i}_start_x'
        if key_check not in params:
            break

        text_box = {}
        for key, default in DEFAULT_VALUES.items():
            param_key = f'text_box_{i}_{key}'
            text_box[key] = params.get(param_key, default)
        
        text_boxes[f'text_box_{i}'] = text_box
        i += 1

    # ---------------------- Main Execution ---------------------- #

    recolored_image = process_images(FOLDER_NUM, primary_color, specified_colors, isImage, base_image_url, imgX, imgY, imgWidth, imgHeight, bucket, isBlur, blur_amount, logo_path, isLogo, logoX, logoY, logoWidth, logoHeight,)
    
    for box_name, box_data in text_boxes.items():
        font_path = box_data["font"]
        FontBlob = bucket.blob(f'graphic_design_posts/fonts/{font_path}')
        if FontBlob.exists():
            font_data = FontBlob.download_as_bytes()
            if font_data:
                # Write to a temporary file to check if the font_data is correct
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as temp_font_file:
                    temp_font_file.write(font_data)
                    font_io = temp_font_file.name
                
            else:
                print("The font data is empty.")
        else:
            print("The font file does not exist in the bucket.")

        max_char_count = ast.literal_eval(box_data["max_char_count"])
        line_height = ast.literal_eval(box_data["line_height"])

        text = generate_text(
            business_description, 
            business_name, 
            max_char_count, 
            box_data["prompt"]
        )
        
        recolored_image = add_text_to_image(
            recolored_image, 
            text, 
            font_io, 
            box_data["font_size"], 
            box_data["start_x"], 
            box_data["start_y"],
            box_data["width"], 
            box_data["height"],
            box_data["anchor_point"],
            box_data["alignment"], 
            box_data["text_color"], 
            line_height,
            primary_color,
            specified_colors
        )

        # Clean up the temporary file
        os.remove(font_io)

    return recolored_image

    # ---------------------- Main Execution ---------------------- #
