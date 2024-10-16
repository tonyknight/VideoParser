# VideoParser
A Python script that uses ffmpeg or ffprobe to parse through a video library and produce a CSV report of video characteristics, such as codec, data rate and track totals.

Currently, the script takes a hard coded path for the root of the media library and searches for video files recursively. There is also a hard coded path for the CSV output. The other hard coded option is for the number of parallel workers.

The report, in it's current form, outputs fields for Full Path,	Filename,	Container	Codec,	Resolution,	Overall Data Rate (Mbps),	File Size (MB),	Duration,	TotalTracks,	VideoTracks,	AudioTracks,	SubtitleTracks,	ChapterTracks. You can easily add or remove video attributes using standard ffmpeg parameters.

