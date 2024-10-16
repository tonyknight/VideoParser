import os
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # For progress bar
import ffmpeg 
# Define the directory containing your media files
media_dir = "/Volumes/Verona/Video"
output_file = "/Volumes/Verona/VideoDetails.csv"
max_workers = 12  # Number of parallel threads to use


# Function to run shell commands and capture output
def run_command(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        return result.stdout.strip()
    except Exception as e:
        return None


# Function to extract media info using ffmpeg-python
def extract_media_info(file_path):
    filename = os.path.basename(file_path)
    full_path = os.path.abspath(file_path)
    filename = filename.replace(",", "_")
    full_path = full_path.replace(",", "_")
    container = file_path.split(".")[-1]

    try:
        # Extract information using ffmpeg-python
        probe = ffmpeg.probe(file_path)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']

        if video_streams:
            codec = video_streams[0]['codec_name']
            width = video_streams[0].get('width')
            height = video_streams[0].get('height')
            resolution = f"{width}x{height}"
        else:
            codec = "N/A"
            resolution = "N/A"

        # Get duration and size
        duration_sec = float(probe['format']['duration'])
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # File size in MB
        duration = "{:02}:{:02}:{:02}".format(int(duration_sec // 3600), int((duration_sec % 3600) // 60),
                                              int(duration_sec % 60))
        data_rate = round((file_size * 8) / duration_sec, 2) if duration_sec > 0 else "N/A"

        total_tracks = len(probe['streams'])
        video_tracks = len(video_streams)
        audio_tracks = len(audio_streams)
        subtitle_tracks = len(subtitle_streams)
        chapter_tracks = len(probe.get('chapters', []))

        return [full_path, filename, container, codec, resolution, data_rate, file_size, duration, total_tracks,
                video_tracks, audio_tracks, subtitle_tracks, chapter_tracks]

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None


# Function to process files in parallel with progress tracking
def process_files_in_parallel(files):
    total_files = len(files)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_media_info, file): file for file in files}
        with open(output_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write header
            csvwriter.writerow(["Full Path", "Filename", "Container", "Codec", "Resolution", "Overall Data Rate (Mbps)",
                                "File Size (MB)", "Duration", "TotalTracks", "VideoTracks", "AudioTracks",
                                "SubtitleTracks", "ChapterTracks"])

            # Track progress using tqdm progress bar
            with tqdm(total=total_files, desc="Processing files") as progress_bar:
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        csvwriter.writerow(result)
                    progress_bar.update(1)  # Update progress bar for each completed file


# Find all media files
media_files = [os.path.join(root, file) for root, _, files in os.walk(media_dir) for file in files if
               file.endswith(('.mp4', '.mkv', '.avi'))]

# Run the parallel processing with progress output
process_files_in_parallel(media_files)

print(f"CSV file created: {output_file}")
