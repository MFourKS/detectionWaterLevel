import datetime

import cv2
from inference import get_model
import supervision as sv
import json
import warnings
from supervision import Position
from tkinter import messagebox

class VideoProcessor:
    def __init__(self, video_width, video_height, model_id):
        self.video_width = video_width
        self.video_height = video_height
        self.model = get_model(model_id)
        if model_id is None:
            self.log("Error: Model initialization failed.")

        # self.csv_sink = sv.JSONSink("det.json")
        self.bounding_box_annotator = sv.BoundingBoxAnnotator()
        # self.label_annotator = sv.LabelAnnotator()
        self.log_file = open("log.txt", "a")

        self.tracker = sv.ByteTrack()
        self.load_coordinates_from_json()
        self.line_zones = []
        for item in self.coordinates:
            coord = int(item[0] * (video_height / 480))
            color_line = item[1]
            severity_level = item[-1]
            start_point = sv.Point(x=0, y=coord)
            end_point = sv.Point(x=video_width, y=coord)
            line_zone = sv.LineZone(start=start_point, end=end_point, triggering_anchors=[Position.TOP_CENTER])
            self.line_zones.append((line_zone, severity_level, color_line))

    def process_frame(self, frame):
        if self.model is None:
            return frame
        annotated_frame = frame.copy()

        # run inference on the current frame
        results = self.model.infer(frame)
        if not results:
            self.log("Error: Inference results are empty.")
            return annotated_frame
        # load the results into the supervision Detections API
        # detections = sv.Detections.from_inference(results)
        detections = sv.Detections.from_inference(results[0].dict(by_alias=True, exclude_none=True))
        if not detections:
            self.log("Error: No detections found.")
            return annotated_frame

        detections = self.tracker.update_with_detections(detections)
        annotated_frame = self.bounding_box_annotator.annotate(
            scene=frame, detections=detections)
        for line_zone, severity_level, color_line in self.line_zones:
            crossed_in, crossed_out = line_zone.trigger(detections)
            if any(crossed_in):
                warning_message = f"Уровень воды поднялся выше {color_line} линии, уровень опасности = {severity_level}"
                warnings.warn(warning_message, Warning)
                self.display_warning(warning_message)
                self.log(warning_message)
            if any(crossed_out):
                print(f"Уровень воды опустился ниже {color_line} линии")
        # for line_zone, _, _ in self.line_zones:
        #     line_zone_annotator = sv.LineZoneAnnotator(display_in_count=False, display_out_count=False)
        #     annotated_frame = line_zone_annotator.annotate(annotated_frame, line_zone)


        # annotate the frame with the inference results
        # annotated_frame = self.bounding_box_annotator.annotate(
        #     scene=frame, detections=detections)
        # annotated_frame = self.label_annotator.annotate(
        #     scene=annotated_frame, detections=detections)
        annotated_frame_resized = cv2.resize(annotated_frame, (640, 480))

        return annotated_frame_resized


    def load_coordinates_from_json(self):
        try:
            with open("coordinates.json", "r") as file:
                self.coordinates = json.load(file)
        except FileNotFoundError:
            self.coordinates = []
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        self.log_file.write(log_message + "\n")
        self.log_file.flush()


    def display_warning(self, message):

        # root = tk.Tk()
        # root.withdraw()
        messagebox.showwarning("Изменение уровня воды", message)
        # root.mainloop()


class FrameBroadcast:
    def __init__(self, video_file, model_id):
        self.cap = cv2.VideoCapture(video_file)
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # self.video_processor = VideoProcessor()
        self.video_processor = VideoProcessor(self.video_width, self.video_height, model_id)
    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return ret, self.video_processor.process_frame(frame)
        else:
            return ret, None

    def release(self):
        self.cap.release()


if __name__ == "__main__":
    video_file = "river_video.mp4"
    model_id = "test-it8jo/1"
    frame_broadcast = FrameBroadcast(video_file, model_id)
    while True:
        ret, frame = frame_broadcast.get_frame()
        if not ret:
            break

        cv2.imshow('Annotated Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    frame_broadcast.release()
    cv2.destroyAllWindows()
