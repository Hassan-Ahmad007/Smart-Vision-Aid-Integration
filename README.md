# Smart Vision Aid (SVA)

### AI Powered Assistive System for Visually Impaired Users

Smart Vision Aid (SVA) is a Python based assistive system designed to help visually impaired users understand their surroundings and perform everyday tasks more independently.

The system combines **voice control, computer vision, OCR, currency recognition, GPS based navigation, and obstacle detection** into a single assistive platform. Information is communicated primarily through voice feedback, while vibration feedback is used for obstacle warnings.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Who Is It For](#who-is-it-for)
5. [Key Features](#key-features)
6. [How It Works](#how-it-works)
7. [System Modules](#system-modules)
8. [Technology Stack](#technology-stack)
9. [System Architecture](#system-architecture)
10. [Project Structure](#project-structure)
11. [Installation](#installation)
12. [Configuration](#configuration)
13. [Usage](#usage)
14. [Example Workflows](#example-workflows)
15. [Safety and Limitations](#safety-and-limitations)
16. [Future Improvements](#future-improvements)
17. [License](#license)

---

## Overview

Visually impaired users can face difficulties with:

* Detecting obstacles
* Understanding objects in their surroundings
* Reading printed text
* Recognizing currency
* Navigating unfamiliar locations
* Receiving useful information while walking

Traditional mobility aids can provide physical obstacle detection, but they generally don't provide information about **what an object is, what text says, what currency is being held, or where the user should go**.

Smart Vision Aid addresses these challenges by combining multiple assistive technologies into one system.

The user interacts with SVA mainly through **voice commands**. Depending on the selected mode, the system uses its camera, AI models, OCR, GPS, and sensors to process the environment and provide useful feedback.

---

## Problem Statement

Visually impaired individuals often depend on multiple tools for different everyday tasks.

A traditional white cane can help detect physical obstacles, but it doesn't identify objects, read documents, recognize banknotes, or provide route guidance.

Smart Vision Aid aims to bring these capabilities together into a single assistive system.

The project focuses on improving:

* Mobility
* Environmental awareness
* Accessibility
* Independence
* Safety

---

## Objectives

The main objectives of Smart Vision Aid are:

* Detect and identify objects in the user's surroundings.
* Read printed text and documents using OCR.
* Recognize Pakistani currency denominations.
* Count multiple currency notes and calculate their total.
* Provide GPS based route guidance.
* Detect nearby obstacles using ultrasonic sensors.
* Provide voice based interaction and feedback.
* Provide vibration based obstacle alerts.
* Support location and system monitoring through cloud services.
* Reduce the need for constant interaction with a smartphone or graphical interface.

---

## Who Is It For?

Smart Vision Aid is primarily designed for:

* Visually impaired users
* Users with partial or complete vision loss
* People who need assistance with environmental awareness and mobility
* Caregivers and family members
* Assistive technology researchers and developers

---

# Key Features

## 🎙️ Voice Controlled Interface

SVA provides a hands free voice interface for controlling the system.

The voice system uses **Vosk** for speech recognition and text to speech for communicating responses.

The user can activate the system and select different modes using voice commands.

Example commands include:

```text
Activate
Reading mode
Detection mode
Currency mode
Stop
Shutdown
```

This allows the user to interact with the system without depending on a screen or keyboard.

---

## 👁️ Object Detection

The Object Detection module uses **YOLOv8** and a camera to identify objects in the user's surroundings.

The module includes processing techniques to improve the reliability of detections.

It uses:

* Confidence thresholding
* Frame skipping
* Detection history
* Multi frame voting
* Confirmed object detection
* Speech cooldown

Instead of immediately announcing every detection, the system checks detections across multiple frames and uses voting to confirm an object.

This helps reduce unstable detections and unnecessary repeated announcements.

### Object Detection Workflow

```text
Camera
   ↓
Frame Capture
   ↓
YOLOv8 Detection
   ↓
Confidence Filtering
   ↓
Detection History
   ↓
Multi Frame Voting
   ↓
Confirmed Object
   ↓
Voice Feedback
```

---

## 📖 Reading and OCR

Reading Mode allows the user to capture and listen to printed text.

The system uses **OpenCV, Tesseract OCR, and Gemini based text cleaning**.

Before performing OCR, the system checks whether the document is sufficiently stable and clear.

The processing includes:

* Image quality evaluation
* Sharpness detection
* Contrast evaluation
* Frame stability detection
* Best frame selection
* Image preprocessing
* Tesseract OCR
* OCR result processing
* Gemini based text cleaning
* Voice output

### Reading Workflow

```text
Camera
   ↓
Reading Area
   ↓
Stability Detection
   ↓
Image Quality Evaluation
   ↓
Best Frame Selection
   ↓
Image Preprocessing
   ↓
Tesseract OCR
   ↓
OCR Results
   ↓
Gemini Text Cleaning
   ↓
Voice Output
```

This process is intended to improve the quality of the text before it is communicated to the user.

---

## 💵 Pakistani Currency Recognition

SVA includes a dedicated currency recognition module for Pakistani banknotes.

The system uses a custom trained YOLO model to recognize currency denominations.

Supported denominations in the current implementation are:

```text
Rs. 10
Rs. 20
Rs. 50
Rs. 75
Rs. 100
Rs. 500
Rs. 1000
Rs. 5000
```

The module can recognize a note and maintain a running total.

For example:

```text
Rs. 500 detected
        ↓
Rs. 500 added
        ↓
Total = Rs. 500
```

If another Rs. 1000 note is shown:

```text
Rs. 1000 detected
        ↓
Rs. 1000 added
        ↓
Total = Rs. 1500
```

### Duplicate Counting Prevention

The system doesn't continuously add the same banknote while it remains in front of the camera.

After recognizing a note, the module waits until the note is removed before allowing another note to be counted.

This helps prevent accidental repeated counting.

### Currency Workflow

```text
Camera
   ↓
Currency YOLO Model
   ↓
Denomination Detection
   ↓
Confidence Filtering
   ↓
Duplicate Detection Removal
   ↓
Stable Detection
   ↓
Denomination Identification
   ↓
Running Total
   ↓
Voice Feedback
```

---

## 🧭 Route Guidance

The Route Guidance module is designed to provide voice based navigation.

The navigation workflow includes:

* Voice based destination input
* GPS location
* Destination geocoding
* Route calculation
* Route processing
* Position tracking
* Navigation instructions
* Voice feedback

### Navigation Workflow

```text
Destination
     ↓
Current GPS Location
     ↓
Destination Geocoding
     ↓
Route Calculation
     ↓
Route Processing
     ↓
GPS Tracking
     ↓
Turn Instructions
     ↓
Voice Feedback
```

The system can provide instructions such as:

```text
Go straight for 100 meters.
Turn right.
Turn left.
```

---

## 🚨 Obstacle Detection

The project includes hardware based obstacle detection using ultrasonic sensors.

The ultrasonic sensors are intended to detect obstacles in the user's walking path.

When an obstacle is detected, the system can provide tactile feedback through a vibration motor.

The project documentation specifies an approximate detection range of:

```text
30 cm to 300 cm
```

This provides an additional safety layer alongside camera based object detection.

---

## 🔊 Audio and Vibration Feedback

SVA uses two main feedback methods.

### Voice Feedback

Voice output is used for:

* Object detection results
* OCR results
* Currency recognition
* Currency totals
* Navigation instructions
* System status
* Warnings

### Vibration Feedback

Vibration is mainly used for:

* Nearby obstacle warnings
* Tactile safety alerts

Using both audio and tactile feedback allows the system to communicate information without requiring visual interaction.

---

## ☁️ Guardian and Cloud Monitoring

The project architecture includes cloud based monitoring using **Firebase Realtime Database**.

The monitoring system is designed to support information such as:

* Current location
* GPS status
* Camera status
* System status
* Error status
* Heartbeat information

This functionality is intended to provide caregivers or guardians with additional awareness of the user's system and location status.

---

# How It Works

The overall SVA workflow can be represented as:

```text
                 USER
                   │
                   ▼
             Voice Command
                   │
                   ▼
          Voice Recognition
                Vosk
                   │
                   ▼
            Mode Selection
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    Detection    Reading   Currency
        │          │          │
      YOLO       OCR        YOLO
        │          │          │
        └──────────┼──────────┘
                   │
                   ▼
             Route Guidance
                GPS / Maps
                   │
                   ▼
             Result Processing
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
      Voice Output     Vibration
```

The central controller manages the system and starts the appropriate module based on the user's voice command.

---

# System Modules

| Module               | Main Purpose                         | Main Technologies         |
| -------------------- | ------------------------------------ | ------------------------- |
| Voice Control        | Voice commands and system management | Vosk, PyAudio             |
| Object Detection     | Identify surrounding objects         | YOLOv8, OpenCV            |
| Reading / OCR        | Read printed text                    | OpenCV, Tesseract, Gemini |
| Currency Recognition | Recognize Pakistani banknotes        | YOLO, OpenCV              |
| Currency Counting    | Calculate total value                | Python, Computer Vision   |
| Route Guidance       | Provide navigation instructions      | GPS, Geocoding, Routing   |
| Obstacle Detection   | Detect nearby obstacles              | Ultrasonic Sensors        |
| Feedback             | Communicate results                  | TTS, Vibration            |
| Guardian Monitoring  | Location and system monitoring       | Firebase                  |

---

# Technology Stack

## Programming Language

* Python

## Artificial Intelligence and Computer Vision

* YOLOv8
* Ultralytics
* OpenCV
* Custom trained YOLO currency model

## OCR and Text Processing

* Tesseract OCR
* Gemini

## Speech Processing

* Vosk
* PyAudio
* Windows Speech Synthesis

## Navigation

* GPS
* Geocoding
* Route calculation
* Route tracking

## Hardware

* Camera
* Arduino
* GPS module
* Ultrasonic sensors
* Bluetooth module
* Vibration motor

## Cloud

* Firebase Realtime Database

---

# System Architecture

The project uses a modular architecture where `main.py` acts as the central controller.

```text
                         SMART VISION AID
                                │
                                ▼
                         Voice Controller
                             main.py
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
        Voice Input        Mode Manager       Voice Output
           Vosk               Threads              TTS
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Object Detection      Reading          Currency
           YOLOv8               OCR               YOLO
              │                 │                 │
              │              Tesseract            │
              │              Gemini               │
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                         Route Guidance
                            GPS + Maps
                                │
                                ▼
                         User Feedback
                      Voice + Vibration
```

---

# Project Structure

A simplified structure of the main software components is:

```text
Smart-Vision-Aid/
│
├── main.py
├── vision_module.py
├── reading_module.py
├── currency_module.py
├── route_guidance.py
│
├── models/
│   ├── yolov8n.pt
│   └── best.pt
│
├── requirements.txt
└── README.md
```

Additional configuration, model, navigation, and supporting files may be present depending on the project setup.

### Main Files

| File                 | Purpose                                              |
| -------------------- | ---------------------------------------------------- |
| `main.py`            | Central controller and voice based system management |
| `vision_module.py`   | Real time object detection                           |
| `reading_module.py`  | Document capture and OCR processing                  |
| `currency_module.py` | Pakistani currency recognition and counting          |
| `route_guidance.py`  | GPS based navigation and route guidance              |

---

# Installation

## Requirements

Before running SVA, make sure the required software and hardware are available.

### Software

* Python 3.x
* Windows
* Tesseract OCR
* Vosk speech recognition model
* Required Python packages
* Required YOLO model files

### Hardware

* Camera
* Microphone
* GPS module for navigation
* Arduino
* Ultrasonic sensors
* Bluetooth module
* Vibration motor

Some features depend on their corresponding hardware components.

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Smart-Vision-Aid.git
cd Smart-Vision-Aid
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Some components require additional configuration before running the project.

## Tesseract OCR

Install Tesseract OCR and make sure the executable path matches the configuration used by the project.

The current code uses a Windows based Tesseract path, so this may need to be changed for another computer.

Example:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Path\To\tesseract.exe"
```

---

## Vosk

Download and install the required Vosk speech recognition model.

Place the model in the directory expected by the project.

The Vosk model is required for offline voice command recognition.

---

## YOLO Models

The project requires the appropriate YOLO model files.

The object detection module uses the YOLOv8 model.

The currency module uses the project's custom trained currency model.

Make sure the model files are placed in the correct locations before starting the application.

---

## Firebase

The project includes Firebase based monitoring functionality.

If Firebase monitoring is enabled, the required Firebase configuration and credentials must be provided.

**Do not upload private Firebase credentials or service account files to a public GitHub repository.**

Add sensitive files to `.gitignore`.

Example:

```text
serviceAccountKey.json
.env
```

---

# Usage

Start the application using:

```bash
python main.py
```

After the system starts, use the microphone to provide commands.

### Activate the System

```text
Activate
```

The system activates and waits for a mode selection.

### Object Detection

```text
Detection mode
```

The camera starts detecting surrounding objects.

### Reading Mode

```text
Reading mode
```

The system captures a stable document image, performs OCR, cleans the extracted text, and reads the result aloud.

### Currency Mode

```text
Currency mode
```

The system recognizes Pakistani banknotes and maintains the running total.

### Stop Current Mode

```text
Stop
```

The active module is stopped and the system returns to mode selection.

### Shutdown

```text
Shutdown
```

The application exits.

---

# Example Workflows

## Object Detection

```text
User
  │
  │ "Detection mode"
  ▼
Camera
  │
  ▼
YOLOv8
  │
  ▼
Object Detection
  │
  ▼
Multi Frame Confirmation
  │
  ▼
Voice Announcement
```

Example:

```text
"Person ahead"
```

---

## Reading

```text
User
  │
  │ "Reading mode"
  ▼
Camera
  │
  ▼
Stability Check
  │
  ▼
Best Frame
  │
  ▼
Image Preprocessing
  │
  ▼
Tesseract OCR
  │
  ▼
Gemini Text Cleaning
  │
  ▼
Voice Output
```

---

## Currency Recognition

```text
User
  │
  │ "Currency mode"
  ▼
Camera
  │
  ▼
Custom Currency YOLO Model
  │
  ▼
Denomination Detection
  │
  ▼
Stable Detection
  │
  ▼
Amount Added
  │
  ▼
Running Total
  │
  ▼
Voice Output
```

---

## Route Guidance

```text
User
  │
  │ Destination
  ▼
GPS Location
  │
  ▼
Destination Geocoding
  │
  ▼
Route Calculation
  │
  ▼
Route Processing
  │
  ▼
GPS Tracking
  │
  ▼
Voice Navigation
```

---

# Safety and Limitations

Smart Vision Aid is an assistive technology prototype and should not be considered a complete replacement for established mobility aids, professional assistance, or independent safety judgment.

System performance can be affected by:

* Poor lighting
* Camera positioning
* Camera availability
* GPS accuracy
* Network connectivity
* Hardware limitations
* Processing performance
* Environmental conditions
* AI model accuracy

Camera based AI detection may occasionally produce incorrect or missed detections.

GPS navigation may also become less accurate in areas with weak satellite visibility.

The system should therefore be used as an **assistive tool**, with appropriate safety precautions.

---

# Future Improvements

Future development can include:

* Improved object detection accuracy
* Better performance in low light conditions
* Expanded currency recognition
* Support for additional currencies
* Offline navigation
* Multilingual voice commands
* Improved speech interaction
* Better hardware integration
* Smaller and lighter hardware
* Improved battery efficiency
* Mobile application integration
* Improved guardian monitoring
* Advanced indoor navigation
* Improved emergency assistance

---

# Project Goals

Smart Vision Aid aims to bring several assistive capabilities together into one platform.

The system is designed to answer practical questions such as:

```text
What is around me?
Can I read this?
What currency am I holding?
How much money do I have?
Where am I?
Where do I need to go?
Which direction should I take?
Is there an obstacle nearby?
```

By combining AI, computer vision, OCR, GPS, sensors, and voice interaction, SVA provides a foundation for a more accessible and independent mobility system for visually impaired users.

---

# License

This project was developed as an academic Final Year Project.

For reuse, modification, or distribution, please refer to the license included in this repository.

---

# Acknowledgements

This project makes use of open source technologies and tools from the fields of:

* Artificial Intelligence
* Computer Vision
* Optical Character Recognition
* Speech Processing
* GPS and Navigation
* Embedded Systems
* Assistive Technology

Special thanks to the developers and communities behind the technologies used in Smart Vision Aid.
