from moviepy.editor import VideoFileClip
from PIL import Image

# Path to your video file
temp_video_path = "test.mov"

# Load the video clip
video_clip = VideoFileClip(temp_video_path)

if video_clip.rotation == 90:
    video_clip = video_clip.resize(video_clip.size[::-1])
    video_clip.rotation = 0

# Get the first frame of the video as an array
frame = video_clip.get_frame(0)

# Convert the frame to a PIL Image
pil_image = Image.fromarray(frame)

# Calculate the aspect ratio
aspect_ratio = pil_image.width / pil_image.height

print("Aspect ratio:", aspect_ratio)

# Save the resized image as a JPG file
pil_image.save("first_frame.jpg")

# Close the video clip
video_clip.close()