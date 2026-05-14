README — DAY 2 DEVELOPMENT UPDATE
Retail Brain OS
Anonymous Visitor Tracking System
Project Overview

Retail Brain OS is an AI-powered retail intelligence platform designed to transform standard CCTV systems into smart business analytics infrastructure for retail environments.

The long-term goal of the project is to provide Indian retailers with realtime customer movement analytics, visitor behavior understanding, occupancy monitoring, heatmaps, billing conversion analytics, and intelligent store insights — without storing permanent personal identities.

Day 2 focused on upgrading the system from simple object detection into a realtime visitor tracking and analytics engine.

Day 2 Objective

The primary objective of Day 2 was:

Convert Realtime Detection Into Realtime Tracking

On Day 1, the system could only detect people using YOLOv8.

Each frame was processed independently, meaning the system had no understanding of whether a detected person was the same individual across multiple frames.

Day 2 solved this limitation by introducing:

multi-person tracking
persistent anonymous visitor IDs
movement continuity
visitor metadata management
movement path visualization
analytics dashboard system
Technologies Used
Purpose	Technology
Detection Model	YOLOv8
Tracking System	ByteTrack
Video Processing	OpenCV
Programming Language	Python
Numerical Operations	NumPy
Environment	Python Virtual Environment (venv)
Core Pipeline After Day 2
Live Camera Feed
        ↓
Frame Capture
        ↓
YOLOv8 Person Detection
        ↓
ByteTrack Multi-Person Tracking
        ↓
Persistent Visitor IDs
        ↓
Visitor Metadata Storage
        ↓
Movement Trail Generation
        ↓
Realtime Analytics Dashboard
        ↓
Live Visualization
Features Implemented
1. Realtime Multi-Person Tracking

The system can now track multiple visitors simultaneously in realtime.

Each detected visitor is assigned a temporary anonymous tracking ID.

Example:

Visitor ID: 1
Visitor ID: 5
Visitor ID: 9

These IDs remain stable while the visitor remains visible inside the camera frame.

2. Persistent Anonymous Visitor IDs

The system now maintains identity continuity across frames.

This allows the system to understand:

which visitor is moving
visitor movement continuity
independent customer sessions

This forms the foundation for future retail analytics features.

3. Active Visitor Count

The system now calculates:

Active Visitors

Meaning:

The number of visitors currently visible in the camera frame.

This will later support:

occupancy analytics
crowd monitoring
congestion alerts
4. Total Visitors Seen

The system now tracks:

Total Visitors Seen

Meaning:

The total number of unique visitor IDs generated during the current runtime session.

This becomes the foundation for future:

footfall analytics
store traffic analysis
conversion analytics
5. Visitor Metadata System

A structured visitor data storage system was implemented.

For every visitor, the system now stores:

visitor_id
first_seen_time
last_seen_time
frames_visible
current_position
movement_path

This converts the project from simple computer vision into structured retail intelligence infrastructure.

6. Movement Trail System

A realtime movement trail system was implemented.

The system continuously stores visitor movement coordinates and visualizes visitor paths directly on the camera feed.

This enables future implementation of:

entry/exit detection
heatmaps
path analysis
customer behavior analytics
zone intelligence

Movement trails visually demonstrate how visitors move throughout the environment.

7. Integrated Analytics Dashboard

A lightweight realtime dashboard panel was integrated directly into the OpenCV interface.

The system now separates:

visual detection feed
FROM
analytical information

This creates a cleaner and more professional visualization pipeline.

The dashboard currently displays:

Active Visitors
Total Visitors Seen
FPS
Visitor Details
Visibility Duration
Position Data
Frames Visible
8. Clean Realtime Visualization

The camera feed was redesigned to display only essential information:

bounding boxes
visitor IDs
movement trails
center points
FPS

This improves readability and creates a more production-style AI surveillance interface.

Current Folder Structure
Retail-OS/
│
├── vision/
│   ├── detection/
│   │   └── detect.py
│   │
│   └── videos/
│
├── venv/
│
├── requirements.txt
├── .gitignore
└── README.md
Main File
detect.py

This file currently handles:

webcam access
frame processing
YOLOv8 inference
ByteTrack tracking
visitor ID management
visitor metadata storage
movement trail rendering
dashboard rendering
FPS calculation
realtime visualization

Current Limitation

The current tracking system can maintain identity continuity only while a visitor remains visible inside the camera frame.

If a visitor completely exits the frame and later reappears, a new temporary ID may be assigned.

This is expected behavior for ByteTrack-based tracking systems.

Planned Future Upgrade

Future phases of the project will implement:

Temporary Anonymous Re-Identification System

This future system will:

estimate returning visitors
maintain short-term visitor memory
avoid permanent identity storage
automatically delete old visitor data after 10–15 days

The system will remain privacy-focused and will avoid permanent biometric identity storage.

Performance Improvements Implemented

The Day 2 system includes several realtime optimizations:

resized frame processing
person-only filtering
optimized inference pipeline
lightweight tracking
efficient trail management
realtime FPS monitoring

This helps maintain smooth realtime performance closer to production CCTV systems.

How To Run
Activate Virtual Environment
Windows
venv\Scripts\activate
Install Dependencies
pip install ultralytics opencv-python numpy
Run The System
python vision/detection/detect.py