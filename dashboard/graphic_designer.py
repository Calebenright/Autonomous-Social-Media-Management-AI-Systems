
from PIL import Image, ImageDraw, ImageFont
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

# from decouple import config
# openai.api_key = config('OPENAI_API_KEY')

OPENAI_API_KEY='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'
openai.api_key = OPENAI_API_KEY

# ---------------------- Utility Functions ----------------------

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
    """Determine if a color is dark based on its luminance."""
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

def process_images(FOLDER_NUM, primary_color, hex_colors, isImage, base_image_url, bucket):
    
    folder_path = f"graphic_design_posts/{FOLDER_NUM}/PNG"
    primary_rgb = hex_to_rgb(primary_color)
    random.shuffle(hex_colors)
    colors = [primary_rgb] + [hex_to_rgb(hex_color) for hex_color in hex_colors]
    blobs = bucket.list_blobs(prefix=folder_path)
    png_files = [blob.name for blob in blobs if blob.name.endswith('.png')]

    if isImage and base_image_url:
        response = requests.get(base_image_url)
        base_image = Image.open(BytesIO(response.content))
    else:
        base_image_blob = bucket.blob(png_files[0])
        base_image_data = base_image_blob.download_as_bytes()
        base_image = Image.open(BytesIO(base_image_data))
        base_image = recolor_image(base_image, colors[0])

    # Process other images
    for idx, file_path in enumerate(png_files[1:]):
        blob = bucket.blob(file_path)
        img_data = blob.download_as_bytes()
        img = Image.open(BytesIO(img_data))
        recolored_img = recolor_image(img, colors[idx+1])
        base_image = Image.alpha_composite(base_image, recolored_img)

    return base_image


def add_title_to_image(image, title_text, title_font_path, title_font_size, title_start_x, title_start_y, title_alignment, text_alignment, text_color, title_wrap_width, line_height_multiplier):
    draw = ImageDraw.Draw(image)
    title_font_path.seek(0)
    font_title = ImageFont.truetype(title_font_path, title_font_size)
    line_height = line_height_multiplier * title_font_size
    wrapped_title_text = textwrap.fill(title_text, width=title_wrap_width)
    textbox_width = max([draw.textbbox((0, 0), line, font=font_title)[2] for line in wrapped_title_text.split('\n')])

    y = title_start_y
    for line in wrapped_title_text.split('\n'):
        line_width = draw.textbbox((0, 0), line, font=font_title)[2]
        if title_alignment == 'center':
            horizontal_position = title_start_x + (textbox_width - line_width) // 2
        elif title_alignment == 'right':
            horizontal_position = title_start_x + textbox_width - line_width
        else:
            horizontal_position = title_start_x

        draw.text((horizontal_position, y), line, font=font_title, fill=text_color)
        y += line_height

    return image, y

def add_text_to_image(image, wrapped_text, title_height, title_start_x, text_font_path, text_font_size, text_start_x, text_start_y, text_alignment, text_color, line_height_multiplier):
    draw = ImageDraw.Draw(image)
    font_regular = ImageFont.truetype(text_font_path, text_font_size)
    line_height = line_height_multiplier * text_font_size
    y = text_start_y if text_start_y != 0 else (title_height if title_height is not None else 0)
    x = text_start_x if text_start_x != 0 else title_start_x
    for line in wrapped_text.split('\n'):
        line_width = draw.textbbox((0, 0), line, font=font_regular)[2]
        if text_alignment == 'center':
            horizontal_padding = (image.width - line_width) // 2
        elif text_alignment == 'right':
            horizontal_padding = image.width - line_width - x
        else: 
            horizontal_padding = 0

        draw.text((x + horizontal_padding, y), line, font=font_regular, fill=text_color)
        y += line_height 

    return image

def calculate_total_text_height(draw, title_text, text, font_title, font_text, line_height_title, line_height_text, add_title, add_text, text_wrap_width, title_wrap_width):
    wrapped_title = textwrap.fill(title_text, width=title_wrap_width) if add_title else ""
    wrapped_text = textwrap.fill(text, width=text_wrap_width) if add_text else ""
    return len(wrapped_title.split('\n')) * line_height_title + len(wrapped_text.split('\n')) * line_height_text

def adjust_vertical_start_position(total_height, specified_y, alignment):
    if alignment == 'center':
        return specified_y - (total_height // 2)
    else: 
        return specified_y
    
def generate_title(business_description, business_name, max_title_char_count, title_method):
    # Define the Business We Are Creating Media For
    if title_method == "cta":
        prompts = [
        f"Create a cta title based on (BUSINESS NAME = {business_name}) or (BUSINESS DESCRIPTION = {business_description}). It has to be less than {max_title_char_count} characters",
        f"I need a call to action based on (BUSINESS NAME = {business_name}) or (BUSINESS DESCRIPTION = {business_description}) It has to be less than {max_title_char_count} characters",
        ]
    else:
        prompts = [
        f"Create a catchy graphic title for (BUSINESS NAME = {business_name}) or (BUSINESS DESCRIPTION = {business_description}). It has to be less than {max_title_char_count} characters",
        f"I need a title for a graphic based on (BUSINESS NAME = {business_name}) or (BUSINESS DESCRIPTION = {business_description}) It has to be less than {max_title_char_count} characters",
        ]
    prompt = random.choice(prompts)
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=max_title_char_count,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    caption = re.sub(r'"+', '', original_string)
    caption = remove_emojis(caption)
    if len(caption) > max_title_char_count:
        return generate_title(business_description, business_name, max_title_char_count, title_method)

    return caption
    
def generate_text(business_description, business_name, max_text_char_count):
    # Define the Business We Are Creating Media For
    prompts = [
    f"Create a catchy graphic cta for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) with a MAXIMUM {max_text_char_count} characters and cannot include special characters",
    f"Create some text for (BUSINESS NAME = {business_name}) and (BUSINESS DESCRIPTION = {business_description}) with a MAXIMUM {max_text_char_count} characters and cannot include special characters",
    ]
    prompt = random.choice(prompts)
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300,
        temperature=1
    )
    original_string = response.choices[0].text.strip()
    caption = re.sub(r'"+', '', original_string)
    caption = remove_emojis(caption)

    return caption

def generate_image_from_params(FOLDER_NUM, business_description, business_name, primary_color, specified_colors, base_image_url):

    # Initialize a GCS client
    credentials = service_account.Credentials.from_service_account_file(settings.GS_CREDENTIALS)
    client = storage.Client(project=credentials.project_id, credentials=credentials)
    bucket = client.bucket(settings.GS_BUCKET_NAME)

    # ---------------------- JSON Loading ----------------------

    # Fetch the JSON from GCS
    blob = bucket.blob(f'graphic_design_posts/{FOLDER_NUM}/params.json')
    json_data = blob.download_as_text()
    params = json.loads(json_data)

    isImage = params.get('isImage', False)
    add_title = params.get('add_title', False)
    add_text = params.get('add_text', False)
    title_font_path = params.get('title_font_path')
    text_font_path = params.get('text_font_path')
    title_font_size = params.get('title_font_size', 36)
    text_font_size = params.get('text_font_size', 24)
    title_start_x = params.get('title_start_x', 50)
    title_start_y = params.get('title_start_y', 50)
    title_alignment = params.get('title_alignment', 'left')
    text_alignment = params.get('text_alignment', 'left')
    text_color = params.get('text_color', 'ai')
    text_wrap_width = params.get('text_wrap_width', 30)
    title_wrap_width = params.get('title_wrap_width', 30)
    max_title_char_count = params.get('max_title_char_count', 30)
    max_text_char_count = params.get('max_text_char_count', 30)
    text_start_x = params.get('text_start_x', 0)
    text_start_y = params.get('text_start_y', 0)
    textbox_alignment = params.get('textbox_alignment', 'top')
    line_height_multiplier = params.get('line_height_multiplier', 1.5)
    title_method = params.get('title_method', "title")

    # ---------------------- Main Execution ----------------------
    titleFontBlob = bucket.blob(f'graphic_design_posts/fonts/{title_font_path}')
    textFontBlob = bucket.blob(f'graphic_design_posts/fonts/{text_font_path}')
    title_font_data = titleFontBlob.download_as_bytes()
    text_font_data = textFontBlob.download_as_bytes()
    title_font_io = BytesIO(title_font_data)

    r, g, b = hex_to_rgb(primary_color)
    if is_dark_color(r, g, b):
        text_color = 'white'
    else:
        text_color = 'black'
    
    text_font_io = BytesIO(text_font_data)
    recolored_image = process_images(FOLDER_NUM, primary_color, specified_colors, isImage, base_image_url, bucket)

    # Placeholder texts for title and regular text (replace with generate_title() and generate_text() when needed)
    title = generate_title(business_description, business_name, max_title_char_count, title_method) if add_title else ""
    text = generate_text(business_description, business_name, max_text_char_count) if add_text else ""
    # title = "hey man"
    # text = " blah blah blah blah blah blah blah blah"

    # Calculate vertical starting position for centered alignment
    if textbox_alignment == 'center' and (add_title or add_text):
        draw_temp = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        font_title_temp = ImageFont.truetype(title_font_io, title_font_size)
        line_height_title_temp = line_height_multiplier * title_font_size
        font_text_temp = ImageFont.truetype(text_font_io, text_font_size)
        line_height_text_temp = line_height_multiplier * text_font_size
        total_height = calculate_total_text_height(draw_temp, title, text, font_title_temp, font_text_temp, line_height_title_temp, line_height_text_temp, add_title, add_text, text_wrap_width, title_wrap_width)
        title_start_y = adjust_vertical_start_position(total_height, title_start_y, textbox_alignment)

    if add_title:
        recolored_image, title_height = add_title_to_image(recolored_image, title, title_font_io, title_font_size, title_start_x, title_start_y, title_alignment, text_alignment, text_color, title_wrap_width, line_height_multiplier)

    if add_text:
        wrapped_text = textwrap.fill(text, width=text_wrap_width)
        recolored_image = add_text_to_image(recolored_image, wrapped_text, title_height, title_start_x, text_font_io, text_font_size, text_start_x, text_start_y, text_alignment, text_color, line_height_multiplier)

    return recolored_image
