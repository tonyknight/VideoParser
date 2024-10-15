import os
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define the directory containing your media files
media_dir = "/path/to/your/folder"
output_file = "media_info.csv"
scan_mode = "quick"  # Change this to 'extensive' for ffmpeg scan
max_workers = 4  # Number of parallel threads to use

# Function to run shell commands and capture output
def run_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return result.stdout.strip()
    except Exception as e:
        return None

# Function to extract media info
def extract_media_info(file_path):
    filename = os.path.basename(file_path)
    full_path = os.path.abspath(file_path)
    filename = filename.replace(",", "_")
    full_path = full_path.replace(",", "_")
    container = file_path.split(".")[-1]

    try:
        if scan_mode == "quick":
            # Quick scan using ffprobe
            codec = run_command(f"ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 '{file_path}'")
            resolution = run_command(f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 '{file_path}'")
            total_tracks = int(run_command(f"ffprobe -v error -show_entries stream=index -of csv=p=0 '{file_path}' | wc -l"))
            video_tracks = int(run_command(f"ffprobe -v error -select_streams v -show_entries stream=index -of csv=p=0 '{file_path}' | wc -l"))
            audio_tracks = int(run_command(f"ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 '{file_path}' | wc -l"))
            subtitle_tracks = int(run_command(f"ffprobe -v error -select_streams s -show_entries stream=index -of csv=p=0 '{file_path}' | wc -l"))
            chapter_tracks = int(run_command(f"ffprobe -v error -show_entries chapters=index -of csv=p=0 '{file_path}' | wc -l"))
        else:
            # Extensive scan using ffmpeg
            codec = run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Video:' | sed -n 's/.*, \(.*\) (.*, Video: \(.*\),.*/\\2/p'")
            resolution = run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Video:' | awk '{{for(i=1;i<=NF;i++){{if($i~/[0-9]{{3,4}}x[0-9]{{3,4}}/){{print $i}}}}}}'")
            total_tracks = int(run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Stream #' | wc -l"))
            video_tracks = int(run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Video:' | wc -l"))
            audio_tracks = int(run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Audio:' | wc -l"))
            subtitle_tracks = int(run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Subtitle:' | wc -l"))
            chapter_tracks = int(run_command(f"ffmpeg -i '{file_path}' 2>&1 | grep 'Chapter:' | wc -l"))
        
        # Replace h265 or hevc codecs with HEVC
        if codec in ["hevc", "h265"]:
            codec = "HEVC"

        # Get the file size in MB
        file_size = int(run_command(f"du -m '{file_path}' | cut -f1"))

        # Get the video duration in seconds
        duration_sec = float(run_command(f"ffprobe -v error -select_streams v:0 -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{file_path}'"))
        duration = "{:02}:{:02}:{:02}".format(int(duration_sec // 3600), int((duration_sec % 3600) // 60), int(duration_sec % 60))

        # Calculate the overall data rate (bitrate in Mbps)
        data_rate = round((file_size * 8) / duration_sec, 2) if duration_sec > 0 else "N/A"

        return [full_path, filename, container, codec, resolution, data_rate, file_size, duration, total_tracks, video_tracks, audio_tracks, subtitle_tracks, chapter_tracks]
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

# Function to process files in parallel
def process_files_in_parallel(files):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_media_info, file): file for file in files}
        with open(output_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write header
            csvwriter.writerow(["Full Path", "Filename", "Container", "Codec", "Resolution", "Overall Data Rate (Mbps)", "File Size (MB)", "Duration", "TotalTracks", "VideoTracks", "AudioTracks", "SubtitleTracks", "ChapterTracks"])
            for future in as_completed(futures):
                result = future.result()
                if result:
                    csvwriter.writerow(result)

# Find all media files
media_files = [os.path.join(root, file) for root, _, files in os.walk(media_dir) for file in files if file.endswith(('.mp4', '.mkv', '.avi'))]

# Run the parallel processing
process_files_in_parallel(media_files)

print(f"CSV file created: {output_file}")
