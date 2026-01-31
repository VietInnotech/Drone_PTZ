#!/bin/bash

# Stream local webcam to MediaMTX
# Requires ffmpeg installed

DEVICE="/dev/video0"
RTSP_URL="rtsp://localhost:8559/webcam_stream"

echo "Streaming $DEVICE to $RTSP_URL..."

ffmpeg -f v4l2 -input_format mjpeg -framerate 30 -video_size 1280x720 -i $DEVICE \
    -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2M -maxrate 2M -bufsize 1M \
    -f rtsp $RTSP_URL
