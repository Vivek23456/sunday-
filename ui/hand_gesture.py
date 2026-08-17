import subprocess
import threading
import time
from pathlib import Path

import cv2
import mediapipe as mp


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "gesture_recognizer.task"
)

CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 15

GESTURE_HOLD_SECONDS = 0.6
GESTURE_COOLDOWN_SECONDS = 1.5

MIN_GESTURE_SCORE = 0.55

DEBUG_PRINT_INTERVAL = 1.0


class HandGestureController:

    def __init__(self):

        self.running = False
        self.thread = None

        self.current_gesture = None
        self.gesture_started = 0.0

        self.last_action = None
        self.last_action_time = 0.0

        self.screen_off = False

        self.last_debug_print = 0.0

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Gesture model not found: "
                f"{MODEL_PATH}"
            )

        base_options = (
            mp.tasks.BaseOptions(
                model_asset_path=str(
                    MODEL_PATH
                )
            )
        )

        vision = mp.tasks.vision

        options = (
            vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=(
                    vision.RunningMode.IMAGE
                ),
                num_hands=1,
                min_hand_detection_confidence=0.35,
                min_hand_presence_confidence=0.35,
                min_tracking_confidence=0.35,
            )
        )

        self.recognizer = (
            vision.GestureRecognizer.create_from_options(
                options
            )
        )

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="sunday-hand-gesture",
        )

        self.thread.start()

        print(
            "Hand gesture controller started."
        )

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join(
                timeout=2.0
            )

            self.thread = None

        try:
            self.recognizer.close()
        except Exception:
            pass

        print(
            "Hand gesture controller stopped."
        )

    def _screen_off(self):

        if self.screen_off:
            return

        result = subprocess.run(
            [
                "xset",
                "dpms",
                "force",
                "off",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:

            print(
                "Could not turn display off:",
                result.stderr.strip(),
            )

            return

        self.screen_off = True

        print(
            "✋ OPEN PALM → DISPLAY OFF"
        )

    def _screen_on(self):

        result = subprocess.run(
            [
                "xset",
                "dpms",
                "force",
                "on",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:

            print(
                "Could not turn display on:",
                result.stderr.strip(),
            )

            return

        self.screen_off = False

        print(
            "✊ CLOSED FIST → DISPLAY ON"
        )

    def _recognize_frame(
        self,
        frame,
    ):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb,
        )

        result = (
            self.recognizer.recognize(
                image
            )
        )

        return result

    def _extract_gesture(
        self,
        result,
    ):

        if not result.gestures:
            return None, 0.0

        if not result.gestures[0]:
            return None, 0.0

        category = (
            result.gestures[0][0]
        )

        name = category.category_name
        score = float(
            category.score
        )

        if (
            name == "Open_Palm"
            and score >= MIN_GESTURE_SCORE
        ):
            return "OPEN_PALM", score

        if (
            name == "Closed_Fist"
            and score >= MIN_GESTURE_SCORE
        ):
            return "CLOSED_FIST", score

        return None, score

    def _recognize_with_fallback(
        self,
        frame,
    ):

        # -------------------------------------------------------
        # PASS 1
        # Full camera frame
        # -------------------------------------------------------

        try:

            result = self._recognize_frame(
                frame
            )

            gesture, score = (
                self._extract_gesture(
                    result
                )
            )

            if gesture is not None:
                return gesture, score

        except Exception:
            pass

        # -------------------------------------------------------
        # PASS 2
        # Enlarged center region
        #
        # This helps when the hand occupies only a small
        # portion of the laptop camera image.
        # -------------------------------------------------------

        height, width = frame.shape[:2]

        crop_width = int(
            width * 0.70
        )

        crop_height = int(
            height * 0.80
        )

        x1 = (
            width - crop_width
        ) // 2

        y1 = (
            height - crop_height
        ) // 2

        x2 = x1 + crop_width
        y2 = y1 + crop_height

        crop = frame[
            y1:y2,
            x1:x2,
        ]

        if crop.size == 0:
            return None, 0.0

        enlarged = cv2.resize(
            crop,
            None,
            fx=1.5,
            fy=1.5,
            interpolation=cv2.INTER_LINEAR,
        )

        try:

            result = self._recognize_frame(
                enlarged
            )

            gesture, score = (
                self._extract_gesture(
                    result
                )
            )

            if gesture is not None:
                return gesture, score

        except Exception:
            pass

        return None, 0.0

    def _handle_gesture(
        self,
        gesture,
        score,
    ):

        now = time.monotonic()

        if gesture != self.current_gesture:

            self.current_gesture = gesture

            self.gesture_started = now

            return

        if gesture is None:
            return

        held_for = (
            now
            - self.gesture_started
        )

        if (
            held_for
            < GESTURE_HOLD_SECONDS
        ):
            return

        if (
            now
            - self.last_action_time
            < GESTURE_COOLDOWN_SECONDS
        ):
            return

        if gesture == self.last_action:

            return

        if gesture == "OPEN_PALM":

            self._screen_off()

        elif gesture == "CLOSED_FIST":

            self._screen_on()

        self.last_action = gesture
        self.last_action_time = now

        self.last_action_time = now

    def _debug(
        self,
        gesture,
        score,
    ):

        now = time.monotonic()

        if (
            now
            - self.last_debug_print
            < DEBUG_PRINT_INTERVAL
        ):
            return

        self.last_debug_print = now

        if gesture is None:

            print(
                "Gesture: none"
            )

        else:

            print(
                f"Gesture: {gesture} "
                f"score={score:.2f}"
            )

    def _run(self):

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )

        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH,
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT,
        )

        camera.set(
            cv2.CAP_PROP_FPS,
            CAMERA_FPS,
        )

        # Try to enable autofocus when supported.
        camera.set(
            cv2.CAP_PROP_AUTOFOCUS,
            1,
        )

        if not camera.isOpened():

            print(
                "Could not open camera "
                f"index {CAMERA_INDEX}."
            )

            self.running = False

            return

        actual_width = int(
            camera.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        actual_height = int(
            camera.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        actual_fps = camera.get(
            cv2.CAP_PROP_FPS
        )

        print(
            "Camera gesture detection active."
        )

        print(
            f"Camera: "
            f"{actual_width}x"
            f"{actual_height} "
            f"@ {actual_fps:.1f} FPS"
        )

        try:

            while self.running:

                success, frame = (
                    camera.read()
                )

                if not success:

                    time.sleep(
                        0.05
                    )

                    continue

                gesture, score = (
                    self._recognize_with_fallback(
                        frame
                    )
                )

                self._debug(
                    gesture,
                    score,
                )

                self._handle_gesture(
                    gesture,
                    score,
                )

                time.sleep(
                    0.01
                )

        finally:

            camera.release()

    def is_screen_off(self):
        return self.screen_off


if __name__ == "__main__":

    controller = (
        HandGestureController()
    )

    controller.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        controller.stop()