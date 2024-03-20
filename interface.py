import tkinter as tk
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
import json
from detection import FrameBroadcast
class CameraApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # Open the default camera
        self.cap = cv2.VideoCapture(0)

        # Define color schemes
        self.day_background_color = "#E0E5EB"  # Light background for day mode
        self.day_foreground_color = "#005792"  # Dark foreground for day mode
        self.night_background_color = "#000000"  # Dark background for night mode
        self.night_foreground_color = "#FFFFFF"  # Light foreground for night mode

        # Initialize with day mode
        self.is_day_mode = True


        # Create a frame to contain video canvas and UI elements
        self.main_frame = tk.Frame(window, bg=self.day_background_color)
        self.main_frame.pack()

        # Create a canvas to display video
        self.canvas = tk.Canvas(self.main_frame, width=640, height=480)
        self.canvas.grid(row=0, column=0, padx=5, pady=5)

        # Create a frame for coordinate input and color selection
        self.input_frame = tk.Frame(self.main_frame, bg=self.day_background_color)
        self.input_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.N)

        # Create a list to store coordinates and associated colors
        self.coordinates = []

        # Create a palette for selecting colors
        self.palette_label = tk.Label(self.input_frame, text="Select Color:", bg=self.day_background_color, fg=self.day_foreground_color)
        self.palette_label.grid(row=0, column=0, padx=5, pady=5)
        self.available_colors = ["red", "green", "blue", "yellow", "orange", "purple", "pink"]
        self.palette = ttk.Combobox(self.input_frame, values=self.available_colors)
        self.palette.grid(row=0, column=1, padx=5, pady=5)
        self.palette.current(0)

        # Create a text input for y-coordinate
        self.y_label = tk.Label(self.input_frame, text="Y-coordinate:", bg=self.day_background_color, fg=self.day_foreground_color)
        self.y_label.grid(row=1, column=0, padx=5, pady=5)
        self.y_input = tk.Entry(self.input_frame, width=5)
        self.y_input.grid(row=1, column=1, padx=5, pady=5)
        self.y_input.bind("<Return>", self.add_coordinate)

        # Create a plus button to add coordinates
        self.plus_button = tk.Button(self.input_frame, text="+", command=self.add_coordinate, bg=self.day_background_color, fg=self.day_foreground_color)
        self.plus_button.grid(row=1, column=2, padx=5, pady=5)

        # Create a scrollbar for the listbox
        self.listbox_scrollbar = tk.Scrollbar(self.input_frame, orient=tk.VERTICAL)
        self.listbox_scrollbar.grid(row=3, column=3, padx=5, pady=5, sticky=tk.NS)

        # Create a listbox to display objects
        self.listbox = tk.Listbox(self.input_frame, height=10, width=30, yscrollcommand=self.listbox_scrollbar.set, bg="white")
        self.listbox.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NS)
        self.listbox_scrollbar.config(command=self.listbox.yview)

        # Create a scrollbar for the log text
        self.log_scrollbar = tk.Scrollbar(window)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a text widget to display the log messages
        self.log_label = tk.Label(window, text="Log:", bg=self.day_background_color, fg=self.day_foreground_color)
        self.log_label.pack(side=tk.BOTTOM)

        self.log_text = tk.Text(window, height=4, width=80, yscrollcommand=self.log_scrollbar.set)
        self.log_text.pack(side=tk.BOTTOM)
        self.log_scrollbar.config(command=self.log_text.yview)

        self.mode_button = tk.Button(window, text="Night Mode", command=self.toggle_mode)
        self.mode_button.pack(side=tk.BOTTOM, pady=5)

        self.frame_broadcast = FrameBroadcast("river_video.mp4")

        self.video_stream()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_coordinates_from_json()

        # Bind right-click event to remove coordinate
        self.listbox.bind("<Button-3>", self.remove_coordinate)
        # Bind backspace key event to remove coordinate
        self.window.bind("<BackSpace>", self.remove_coordinate)
        self.canvas.bind("<Button-1>", self.set_y_coordinate)

    def video_stream(self):
        # Retrieve a frame from the video stream
        ret, frame = self.frame_broadcast.get_frame()
        if ret:
            # Convert the frame to a format compatible with Tkinter
            photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            # Update the canvas with the new frame
            self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.canvas.photo = photo

            # Display coordinates on the video frame
            for coord, color in self.coordinates:
                self.canvas.create_rectangle(0, coord - 1, 640, coord + 1, fill=color)

            # Update the canvas to reflect changes
            self.canvas.update_idletasks()

            # Schedule the next call to video_stream after 10 milliseconds
            self.window.after(10, self.video_stream)
        else:
            # If there's no more frames, release resources and close the window
            self.frame_broadcast.release()
            self.window.destroy()

    def add_coordinate(self, event=None):
        value = self.y_input.get()
        try:
            y = int(value)
            if 0 <= y <= 480:
                existing_coords = [coord for coord, _ in self.coordinates]  # Extracting existing y-coordinates
                if y in existing_coords:
                    self.log(f"Coordinate {y} already exists.")
                else:
                    color = self.palette.get()
                    if color in self.available_colors:
                        self.coordinates.append((y, color))
                        self.log(f"Added new coordinate {y} with color {color}")
                        self.update_listbox()
                        # Remove color from available options
                        self.available_colors.remove(color)
                        self.palette["values"] = self.available_colors
                        # Save updated coordinates to JSON file
                        self.save_coordinates_to_json()
                        # Clear the input field
                        self.y_input.delete(0, tk.END)
                    else:
                        self.log(f"Color {color} is already used.")
            else:
                self.log("Y-coordinate must be between 0 and 480.")
        except ValueError:
            self.log("Invalid input. Please enter an integer.")

    def remove_coordinate(self, event):
        # Get the index of the selected item in the listbox
        selected_index = self.listbox.curselection()
        if selected_index:
            index = int(selected_index[0])
            # Remove the selected coordinate from the list and update listbox
            removed_coord = self.coordinates.pop(index)
            self.log(f"Removed coordinate {removed_coord}")
            self.update_listbox()
            # Add the color back to available colors
            if removed_coord[1] not in self.available_colors:
                self.available_colors.append(removed_coord[1])
                self.available_colors.sort()
                self.palette["values"] = self.available_colors
            # Save updated coordinates to JSON file
            self.save_coordinates_to_json()
        else:
            self.log("No coordinate selected.")
    def load_coordinates_from_json(self):
        try:
            with open("coordinates.json", "r") as file:
                self.coordinates = json.load(file)
                self.update_listbox()
        except FileNotFoundError:
            self.coordinates = []

    def save_coordinates_to_json(self):
        with open("coordinates.json", "w") as file:
            json.dump(self.coordinates, file)

    def set_y_coordinate(self, event):
        y = event.y
        if 0 <= y <= 480:
            # Fill the coordinate input field with the clicked y-coordinate
            self.y_input.delete(0, tk.END)
            self.y_input.insert(0, str(y))

            color = self.palette.get()
            # Draw a line on the canvas at the clicked y-coordinate
            self.canvas.create_line(0, y, 640, y, fill=color)

        else:
            self.log("Y-coordinate must be between 0 and 480.")

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for coord, color in self.coordinates:
            self.listbox.insert(tk.END, f"Y: {coord}, Color: {color}")

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def on_closing(self):
        self.frame_broadcast.release()
        self.window.destroy()

    def toggle_mode(self):
        if self.is_day_mode:
            self.window.configure(bg=self.night_background_color)
            self.main_frame.configure(bg=self.night_background_color)
            self.input_frame.configure(bg=self.night_background_color)
            self.listbox.configure(bg="black", fg=self.night_foreground_color)
            self.log_text.configure(bg="black", fg=self.night_foreground_color)
            self.mode_button.config(text="Day Mode")
            self.is_day_mode = False
        else:
            self.window.configure(bg=self.day_background_color)
            self.main_frame.configure(bg=self.day_background_color)
            self.input_frame.configure(bg=self.day_background_color)
            self.listbox.configure(bg="white", fg=self.day_foreground_color)
            self.log_text.configure(bg="white", fg=self.day_foreground_color)
            self.mode_button.config(text="Night Mode")
            self.is_day_mode = True


def main():
    root = tk.Tk()
    app = CameraApp(root, "detectionWaterLevel")
    root.mainloop()

if __name__ == "__main__":
    main()