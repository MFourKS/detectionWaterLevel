import cv2
from inference import get_model
import supervision as sv

class VideoProcessor:
    def __init__(self):
        self.model = get_model(model_id="test-it8jo/1")
        self.bounding_box_annotator = sv.BoundingBoxAnnotator()
        self.label_annotator = sv.LabelAnnotator()

    def process_frame(self, frame):
        # run inference on the current frame
        results = self.model.infer(frame)

        # load the results into the supervision Detections API
        detections = sv.Detections.from_inference(results[0].dict(by_alias=True, exclude_none=True))

        # annotate the frame with the inference results
        annotated_frame = self.bounding_box_annotator.annotate(
            scene=frame, detections=detections)
        annotated_frame = self.label_annotator.annotate(
            scene=annotated_frame, detections=detections)

        return annotated_frame

class FrameBroadcast:
    def __init__(self, video_file):
        self.cap = cv2.VideoCapture(video_file)
        self.video_processor = VideoProcessor()

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
    frame_broadcast = FrameBroadcast(video_file)
    while True:
        ret, frame = frame_broadcast.get_frame()
        if not ret:
            break

        cv2.imshow('Annotated Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    frame_broadcast.release()
    cv2.destroyAllWindows()
