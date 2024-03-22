import datetime
import cv2
import supervision as sv
import json
import warnings
import tkinter as tk
import PIL.Image, PIL.ImageTk
import multiprocessing
import threading
from inference import get_model
from supervision import Position
from tkinter import messagebox
from tkinter import ttk
from tkinter import Button
from detection import FrameBroadcast
from interface import CameraApp
from detection import VideoProcessor