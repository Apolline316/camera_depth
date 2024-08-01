# Raspberry Pi - Installation Guide

This guide provides instructions for installing various programming software on your Raspberry Pi.

## Prerequisites

Before starting, make sure you have access to a functional Raspberry Pi and are connected to the Internet.

## Software Installation

### 1. Python

Python is a popular and widely used programming language. On Raspberry Pi, Python is generally pre-installed. You can check the Python version with the following command in the terminal:

```bash
python --version
```

If Python is not installed, you can install it by running the following commands:

```bash
sudo apt update
sudo apt install python3
```

### 2. Visual Studio Code (VS Code)
Visual Studio Code is a very popular open-source code editor developed by Microsoft. It offers extensive support for many programming languages.

To install Visual Studio Code on your Raspberry Pi, follow these steps:

```bash
sudo apt update
sudo apt install code
```

After installation, you can launch VS Code from the menu or using the `code` command in the terminal.

### 3. Thonny
Thonny is a user-friendly integrated development environment (IDE) for Python that is especially suitable for beginners. To install it, follow the provided steps.

```bash
sudo apt update
sudo apt install thonny
```
After installation, you can launch Thonny from the menu or using the terminal command.

## Installation des librairies

To install libraries, first open a terminal. The sections below show how to install various libraries.

But first, you can check which libraries are already installed. To do this, enter the relevant command.

```bash
sudo apt install python-
```

To verify the installation of a library, you can use the command provided, replacing `<library_name>` with the name of the library.
```bash
pip show <librarie_name>
```

### numpy

```bash
sudo apt install python-numpy
```

### matplotlib
```bash
sudo apt install python-matplotlib
```

### picamera2

If you need to update Picamera2, you can do so by performing a full system update or by specifically installing it via the terminal. 

```bash
sudo apt update
sudo apt install -y python3-picamera2
```

This ensures that Picamera2 is updated to the latest version available in the repositories.

If you are using the full version of Raspberry Pi OS and need the GUI dependencies for Picamera2, you can install them with the provided command. 
```bash
sudo apt install -y python3-pyqt5 python3-opengl
```
This installs PyQt5 and the necessary OpenGL dependencies for Picamera2's graphical features.

If you are using Raspberry Pi OS Lite and want to use GUI features with Picamera2, you will need to install PyQt5 and OpenGL separately.

```bash
sudo apt install -y python3-pyqt5 python3-opengl
```

If you want to install Picamera2 without the additional GUI dependencies, use the provided command.


```bash
sudo apt install -y python3-picamera2 --no-install-recommends
```

### openCV

```bash
sudo apt-get install python3-opencv
```

### ArduArducamDepthCamera
To install this library, visit the ToF.md page.
