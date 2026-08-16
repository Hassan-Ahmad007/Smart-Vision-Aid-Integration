# Smart Vision Aid (SVA)

## An Intelligent Assistive System for Visually Impaired Users

Smart Vision Aid (SVA) is an AI powered assistive technology project designed to help visually impaired individuals move more safely and independently in their daily lives.

The system combines **computer vision, artificial intelligence, OCR, currency recognition, GPS based navigation, obstacle detection, voice interaction, and sensor based feedback** into a single assistive platform.

SVA is designed around a simple idea:

> **Give visually impaired users more information about their surroundings through voice and tactile feedback, without requiring constant interaction with a smartphone or computer screen.**

The project was developed as a Final Year Project by students of Computer Science under the supervision of **Miss Sadaf Mehmood**.

---

## Project Overview

Visually impaired individuals face several challenges in everyday activities, including:

* Detecting obstacles in their path
* Identifying objects around them
* Reading printed text, signs, and documents
* Recognizing currency
* Navigating to unfamiliar locations
* Maintaining awareness of their surroundings
* Getting assistance during unsafe situations

Traditional white canes and basic smart sticks can help detect nearby obstacles, but they generally cannot understand what the obstacle is, read text, recognize currency, or provide route guidance.

Smart Vision Aid addresses these limitations by combining multiple assistive technologies into one system.

The project consists of a **smart stick and processing system**, supported by AI based software modules and hardware sensors.

---

## Who Is SVA For?

Smart Vision Aid is primarily designed for:

* People with partial or complete visual impairment
* Visually impaired users who need assistance with mobility and environmental awareness
* Caregivers and family members who want to monitor a user's safety
* Rehabilitation centers
* Assistive technology organizations
* Researchers and students working on accessible AI and embedded systems

---

## Key Features

### 1. Voice Controlled Interface

The system is controlled primarily through voice commands.

Users can activate the system and select different modes using natural voice commands such as:

```text
Activate

Reading mode

Detection mode

Currency mode

Stop mode

Shutdown
```

The current implementation uses **Vosk** for offline speech recognition and a **text to speech system** for spoken responses.

---

### 2. Real Time Object Detection

SVA uses **YOLOv8** and a camera to identify objects in the user's surroundings.

The object detection module:

* Captures live camera frames
* Runs YOLOv8 object detection
* Filters detections using a confidence threshold
* Tracks detections across multiple frames
* Uses a voting mechanism to confirm objects
* Announces confirmed objects through voice
* Uses a speech cooldown to prevent repeated announcements

For example, after confirming an object, the system can provide an audio message such as:

```text
Person ahead
```

The system also displays bounding boxes and detection information during operation.

---

### 3. Reading and OCR

The Reading Mode allows the user to read printed documents, signs, labels, and other text.

The system uses:

* OpenCV
* Image preprocessing
* Tesseract OCR
* OCR confidence evaluation
* Image quality analysis
* Frame stability detection
* Best frame selection
* Gemini based text cleaning

The reading process works by first checking whether the document is stable and clear enough to capture.

The system evaluates:

* Sharpness
* Contrast
* Image quality
* Frame stability

Once a suitable frame is captured, multiple preprocessing versions are generated and passed through OCR.

The extracted text is then processed and cleaned before being converted into speech.

### Reading Pipeline

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

This approach helps reduce errors caused by blurry, unstable, or poorly captured images.

---

### 4. Pakistani Currency Recognition and Counting

SVA includes a dedicated currency recognition module for Pakistani banknotes.

The module uses a custom trained YOLO model to recognize supported denominations.

Currently supported denominations include:

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

The system doesn't simply recognize the note. It also maintains a running total.

For example:

```text
Rs. 500 detected
        ↓
Rs. 500 added
        ↓
Total = Rs. 500
```

If the user then shows another Rs. 1000 note:

```text
Rs. 1000 detected
        ↓
Rs. 1000 added
        ↓
Total = Rs. 1500
```

To prevent the same banknote from being counted repeatedly, the system waits until the current note is removed before accepting the next note.

### Currency Recognition Pipeline

```text
Camera
   ↓
YOLO Currency Model
   ↓
Denomination Detection
   ↓
Confidence Filtering
   ↓
Duplicate Detection Removal
   ↓
Stable Frame Verification
   ↓
Currency Amount
   ↓
Running Total
   ↓
Voice Feedback
```

---

### 5. GPS Route Guidance

The navigation module is designed to provide voice based route guidance.

The intended workflow is:

```text
Voice Destination
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
Navigation Instructions
       ↓
Voice Feedback
```

The navigation system obtains the user's current coordinates and calculates a route to the selected destination.

It then tracks the user's movement and provides navigation instructions such as:

```text
Go straight for 100 meters.
Turn right.
Turn left.
```

The navigation module is designed to work with the GPS hardware used by the project.

---

### 6. Obstacle Detection

The project documentation also defines a hardware based obstacle detection system using ultrasonic sensors.

The ultrasonic sensors are intended to detect obstacles within the user's walking path.

The system can provide tactile feedback through vibration motors when an obstacle is detected.

According to the project requirements, the ultrasonic system is designed around a detection range of approximately:

```text
30 cm to 300 cm
```

This provides an additional safety layer alongside camera based object detection.

---

### 7. Dual Feedback

SVA is designed to provide feedback through two main channels:

**Audio feedback**

Used for:

* Object descriptions
* OCR results
* Currency results
* Navigation instructions
* System status
* Warnings

**Vibration feedback**

Used for:

* Nearby obstacle warnings
* Tactile safety alerts

This combination allows the user to receive information without relying entirely on audio.

---

### 8. Guardian Monitoring

The project documentation includes a guardian monitoring system intended to provide caregivers with information about the user's safety and location.

The system is designed to support:

* Live location monitoring
* GPS status
* Camera status
* System status
* Error status
* Safety monitoring
* Emergency notifications

Firebase Realtime Database is used in the software architecture for cloud based status and location information.

The current codebase contains the Firebase integration and cloud monitoring logic, although some of the monitoring and navigation integration is currently disabled/commented in `main.py`.

---

## How the System Works

The overall system follows a modular architecture.

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
   Voice Input         Mode Manager       Voice Output
      Vosk              Threading           TTS Queue
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
   Object Detection      Reading         Currency
      YOLOv8             OCR              YOLO
          │                │                │
          │             Tesseract          │
          │                │                │
          │             Gemini              │
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    Route Guidance
                       GPS + Maps
                           │
                           ▼
                   User Feedback
                 Audio + Vibration
```

The system is divided into independent modules so that each major functionality can be developed, tested, and maintained separately.

---

## System Workflow

A typical interaction with SVA follows this process:

### Step 1: System Activation

The user says:

```text
Activate
```

The voice controller recognizes the command and activates SVA.

The system responds:

```text
Smart Vision Aid activated. Please select your mode.
```

### Step 2: Mode Selection

The user selects a mode using voice.

For example:

```text
Detection mode
```

or:

```text
Reading mode
```

or:

```text
Currency mode
```

### Step 3: Camera Verification

Before starting a camera based module, the system checks whether the external camera is available.

### Step 4: Module Execution

The selected module runs in its own thread.

This allows the main voice controller to remain responsive.

### Step 5: Processing

The selected AI or computer vision pipeline processes camera or sensor data.

### Step 6: Feedback

The result is communicated to the user using audio and, where applicable, vibration feedback.

### Step 7: Stop or Switch Mode

The user can say:

```text
Stop
```

to stop the current mode and return to mode selection.

The system can also be shut down using:

```text
Shutdown
```

---

## System Modules

| Module               | Purpose                                | Main Technologies             |
| -------------------- | -------------------------------------- | ----------------------------- |
| Voice Control        | Voice commands and system control      | Vosk, PyAudio                 |
| Object Detection     | Identify objects around the user       | YOLOv8, OpenCV                |
| Reading              | Read printed text                      | OpenCV, Tesseract OCR, Gemini |
| Currency Recognition | Recognize and count Pakistani currency | YOLO, OpenCV                  |
| Route Guidance       | Provide destination based navigation   | GPS, Geocoding, Routing       |
| Obstacle Detection   | Detect nearby obstacles                | Ultrasonic Sensors            |
| Feedback             | Communicate results to the user        | TTS, Vibration                |
| Guardian Monitoring  | Monitor location and system status     | Firebase                      |

---

## Hardware

The project documentation specifies the following hardware components:

* Arduino
* GPS module
* Bluetooth module
* Ultrasonic sensors
* Vibration motor
* Camera
* Laptop or processing unit

The smart stick provides the physical platform for the sensors and feedback components, while the processing unit handles the computationally intensive AI and vision tasks.

---

## Software and Technologies

### Programming Language

* Python

### Artificial Intelligence and Computer Vision

* YOLOv8
* Ultralytics
* OpenCV
* Tesseract OCR
* Custom trained YOLO currency model

### Speech

* Vosk
* PyAudio
* Windows System.Speech
* Text to Speech

### Natural Language Processing

* Gemini based text cleaning for OCR results

### Navigation

* GPS hardware
* Geocoding
* Route calculation
* Route tracking

### Hardware Communication

* Arduino
* Bluetooth
* Ultrasonic sensors
* GPS module
* Vibration motor

### Cloud

* Firebase Realtime Database

---

## Project Architecture

The project follows a modular architecture.

The central controller is responsible for:

* Voice recognition
* Mode selection
* Thread management
* Camera management
* Speech queue management
* System shutdown
* Module switching

Individual modules handle their own processing.

### Main Software Modules

```text
main.py
│
├── vision_module.py
│
├── reading_module.py
│
├── currency_module.py
│
└── navigation/
    └── route_guidance.py
```

The navigation system also contains supporting components for destination input, GPS input, route processing, tracking, geocoding, and route calculation.

---

## Project Structure

A simplified project structure is:

```text
Smart-Vision-Aid/
│
├── main.py
├── vision_module.py
├── reading_module.py
├── currency_module.py
│
├── navigation/
│   ├── route_guidance.py
│   ├── gps_input.py
│   ├── voice_input.py
│   ├── navigation_api.py
│   ├── route_processor.py
│   └── tracker.py
│
├── imagepreprocessing.py
├── textextractor.py
├── textcleaner.py
│
├── model/
│
├── best.pt
├── yolov8n.pt
│
├── serviceAccountKey.json
│
├── requirements.txt
│
└── README.md
```

The exact contents of the repository may vary depending on the deployment and configuration environment.

---

## Object Detection Processing

The object detection module uses a lightweight YOLOv8 model and processes selected frames rather than performing inference on every frame.

The implementation uses:

* Confidence thresholding
* Frame skipping
* Detection history
* Multi frame voting
* Top detection selection
* Speech cooldown

The voting mechanism helps confirm that an object is consistently visible before announcing it.

This is particularly important for assistive applications where repeatedly announcing unstable detections could make the system difficult to use.

---

## OCR Processing

The Reading Mode includes several stages before the final speech output.

### Image Quality

The system calculates:

* Blur score
* Contrast score
* Overall quality

### Stability

The system compares consecutive frames to determine whether the document is sufficiently stable.

### Capture

When the page meets the required quality and stability thresholds, candidate frames are collected.

The sharpest suitable frame is selected for OCR.

### OCR

Multiple preprocessing versions are passed through the OCR pipeline.

### Text Cleaning

The resulting OCR text is passed to the text cleaning component, which uses Gemini to improve the final text before speech output.

---

## Currency Counting Logic

Currency recognition uses a custom YOLO model.

The module performs:

1. Camera capture
2. Currency detection
3. Confidence filtering
4. Bounding box processing
5. Duplicate removal using IoU
6. Stable detection verification
7. Denomination extraction
8. Total calculation
9. Voice announcement
10. Waiting for note removal

The note removal state is important because it prevents a single banknote from being counted multiple times while it remains in the camera view.

---

## Voice Control

The voice controller uses a predefined Vosk grammar containing supported commands.

Examples include:

```text
activate
smart vision aid
switch to reading mode
switch to detection mode
switch to currency mode
reading mode
detection mode
currency mode
currency
count currency
money mode
stop
stop mode
shutdown
shut down
exit system
```

This constrained command vocabulary makes the voice interface more predictable and suitable for hands free operation.

---

## Speech Priority System

SVA uses a priority queue for speech output.

Different messages can be assigned different priorities.

For example:

* Critical system messages receive high priority
* Navigation messages can receive high priority
* Normal mode status messages use normal priority
* Guidance messages can be given lower priority

The speech worker processes queued messages and uses Windows PowerShell Speech Synthesis to produce the audio output.

---

## Safety Considerations

Safety is an important part of the SVA design.

The system includes mechanisms for:

* Camera availability checking
* Camera connection failure detection
* GPS status monitoring
* Sensor monitoring
* System status reporting
* Obstacle alerts
* Voice warnings
* Vibration alerts
* Guardian monitoring

The project is intended as an assistive prototype and should not be treated as a replacement for established mobility aids or professional assistance.

---

## Current Project Scope

The project focuses on:

* AI based object detection
* OCR based text recognition
* Pakistani currency recognition
* Currency counting
* GPS based navigation
* Ultrasonic obstacle detection
* Audio feedback
* Vibration feedback
* Bluetooth communication
* Safety monitoring
* Guardian monitoring

---

## Features Outside the Current Scope

The project documentation does not include:

* Facial recognition
* Medical diagnosis
* Fully autonomous navigation
* Advanced indoor localization
* Commercial scale deployment
* Large scale cloud infrastructure

---

## Future Enhancements

Possible future improvements include:

* Improved object detection accuracy
* Faster and more efficient AI models
* Offline navigation
* Multi language voice support
* Customizable voice output
* Improved battery life
* Smaller and lighter hardware
* Advanced indoor navigation
* Better mapping capabilities
* Mobile application integration
* Expanded cloud monitoring
* Improved guardian and emergency features

---

## Limitations

Like any computer vision and embedded assistive system, SVA has practical limitations.

Performance can be affected by:

* Poor lighting
* Camera positioning
* Camera failure
* GPS accuracy
* Weak network connectivity
* Hardware failure
* Battery limitations
* Processing performance
* Environmental conditions

AI based predictions should therefore be treated as assistance rather than guaranteed safety decisions.

---

## Research and Academic Context

Smart Vision Aid was developed as a Final Year Project with the goal of combining concepts from:

* Artificial Intelligence
* Computer Vision
* Natural Language Processing
* Optical Character Recognition
* Embedded Systems
* Internet of Things
* GPS and navigation
* Human Computer Interaction
* Assistive Technology

The project was motivated by the gap between traditional mobility aids and more expensive commercial smart vision systems.

Rather than focusing on a single feature, SVA attempts to bring several assistive functions together into one platform.

---

## Project Team

### Final Year Project Team

| Name             | Roll Number  | Main Responsibility |
| ---------------- | ------------ | ------------------- |
| Ayesha Naeem     | 22101002 052 | Testing             |
| Hassan Ahmad Dar | 22101002 073 | Object Detection    |
| Ahmar Mehmood    | 22101002 079 | Navigation          |
| Masab Ali        | 22101002 095 | OCR                 |

All team members contributed to research, literature review, development, integration, testing, and documentation according to the project requirements.

### Supervisor

**Miss Sadaf Mehmood**

---

## Project Screenshots and Hardware

### Smart Vision Aid Prototype

Place the photograph of the completed smart stick in the repository, for example:

```text
docs/images/smart-vision-aid.jpg
```

Then display it here:

![Smart Vision Aid Prototype](docs/images/smart-vision-aid.jpg)

### System Architecture

If the architecture diagram from the project documentation is added to the repository:

```text
docs/images/system-architecture.png
```

It can be displayed using:

![System Architecture](docs/images/system-architecture.png)

### Object Detection

```text
docs/images/object-detection.png
```

![Object Detection](docs/images/object-detection.png)

### Reading / OCR

```text
docs/images/ocr.png
```

![Reading and OCR](docs/images/ocr.png)

### Currency Recognition

```text
docs/images/currency-recognition.png
```

![Currency Recognition](docs/images/currency-recognition.png)

---

## Getting Started

### Prerequisites

Before running the software, make sure the required hardware and software are available.

Recommended software environment:

* Windows
* Python 3.x
* Camera
* Microphone
* Vosk speech recognition model
* Tesseract OCR
* Required Python packages
* YOLO model weights

Hardware dependent features additionally require:

* Arduino
* GPS module
* Bluetooth module
* Ultrasonic sensors
* Vibration motor

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/Smart-Vision-Aid.git
cd Smart-Vision-Aid
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Make sure the required model files are available in the correct project directories.

The Vosk model should also be placed in the expected `model` directory.

---

## Configuration

Some components require local configuration.

For example:

### Tesseract OCR

The OCR module requires Tesseract OCR to be installed and configured.

The current implementation contains a Windows Tesseract path:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
```

This path should be changed according to the installation location on the target computer.

### Firebase

The Firebase integration requires the appropriate Firebase service account configuration.

Do not upload private credentials such as:

```text
serviceAccountKey.json
```

to a public GitHub repository.

Add sensitive files to `.gitignore` instead.

---

## Running the System

After completing the required configuration, run:

```bash
python main.py
```

The system initializes the microphone and speech recognition model, searches for the external camera, and waits for the activation command.

Say:

```text
Activate
```

Then select the required mode.

For example:

```text
Detection mode
```

---

## Example Usage

### Object Detection

```text
User:
Activate

SVA:
Smart Vision Aid activated. Please select your mode.

User:
Detection mode

SVA:
Starting object detection.

System:
Camera → YOLOv8 → Object confirmation → Voice feedback
```

### Reading

```text
User:
Reading mode

SVA:
Starting reading mode.

System:
Camera → Quality check → Stable frame → OCR → Text cleaning → Speech
```

### Currency

```text
User:
Currency mode

SVA:
Starting currency mode.

System:
Camera → Currency model → Stable detection → Amount → Running total → Speech
```

### Stopping a Mode

```text
User:
Stop

SVA:
Mode stopped. Please select your mode.
```

---

## Design Philosophy

SVA follows a modular design so that each major function can be developed and improved independently.

The system separates:

**Input**

Camera, microphone, GPS, and sensors

**Processing**

AI models, OCR, route processing, and sensor logic

**Output**

Audio, vibration, and monitoring information

This structure makes the project easier to test, debug, and extend.

---

## Why Smart Vision Aid?

The main goal of SVA is not to replace existing mobility aids.

Instead, it adds an intelligent layer around them.

A traditional white cane can help a user detect a physical obstacle.

SVA aims to provide additional information such as:

```text
What is around me?
Can I read this?
What currency am I holding?
Where am I going?
What direction should I take?
Is there an obstacle nearby?
Can someone monitor my safety?
```

By combining these capabilities, the project aims to improve **mobility, environmental awareness, independence, and safety** for visually impaired users.

---

## Academic Project

**Project:** Smart Vision Aid (SVA)

**Type:** Final Year Project

**Field:** Computer Science

**Supervisor:** Miss Sadaf Mehmood

**Institution:** University of Sialkot

**Team:**

* Ayesha Naeem
* Hassan Ahmad Dar
* Ahmar Mehmood
* Masab Ali

---

## License

This project was developed for academic and research purposes.

If you plan to reuse, modify, or distribute the project, please contact the project authors and follow the licensing terms included in this repository.

---

## Acknowledgements

The team would like to acknowledge the project supervisor, faculty members, researchers, open source developers, and the communities behind the technologies used in this project.

Special thanks to the developers and maintainers of the open source tools and frameworks that made this project possible.

---

## Conclusion

Smart Vision Aid demonstrates how artificial intelligence, computer vision, OCR, GPS, embedded systems, and voice interaction can be combined to create an assistive technology platform.

The project provides a foundation for a more capable and accessible assistive system that can be extended with better AI models, improved hardware, multilingual support, mobile applications, offline navigation, and advanced safety features in the future.
