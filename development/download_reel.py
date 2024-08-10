import instaloader
import os

def download_instagram_reel(url, target_folder):
    L = instaloader.Instaloader()

    os.makedirs(target_folder, exist_ok=True)

    shortcode = url.split('/')[-2]

    video_path = None
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_folder)
        
        video_files = [f for f in os.listdir(target_folder) if f.endswith('.mp4')]
        if video_files:
            video_path = os.path.join(target_folder, video_files[0])
        
        print(f"Reel downloaded successfully in folder '{target_folder}': {shortcode}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return video_path

if __name__ == "__main__":
    reel_url = "https://www.instagram.com/p/C7VVkJOt3eA/?utm_source=ig_web_copy_link"
    nested_subfolder = "Staging Functions"
    video_path = download_instagram_reel(reel_url, nested_subfolder)
    if video_path:
        print(f"Path of the downloaded video: {video_path}")
    else:
        print("Video could not be found.")