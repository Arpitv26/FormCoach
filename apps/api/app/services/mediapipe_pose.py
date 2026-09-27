"""Optional local-video adapter. SDK objects never leave this module."""

import logging
from math import isfinite
from pathlib import Path
from time import monotonic

from app.domain.pose import LANDMARK_NAMES, PoseFrame, PoseLandmark
from app.services.pose_provider import PoseSequence

MAX_VIDEO_BYTES = 250 * 1024 * 1024
MAX_DURATION_MS = 120_000
MAX_SAMPLED_FRAMES = 1800
MAX_DECODED_FRAMES = 30_000
logger = logging.getLogger(__name__)


class VideoInputError(ValueError):
    """An unsupported or unreadable local recording; never replaced with demo results."""


class VideoSetupError(VideoInputError):
    """Optional local packages/model are unavailable; this is not a bad client recording."""


class VideoProcessingTimeout(VideoInputError):
    """Cooperative processing budget expired between native calls."""


def map_landmarks(poses: list, *, allow_dominant_pose=False) -> list[PoseLandmark]:
    """Use normalized coordinates, never world-meter coordinates or fabricated poses."""
    if allow_dominant_pose and len(poses) > 1:

        def area(pose):
            points = [
                p
                for p in pose
                if p.visibility is not None
                and p.visibility >= 0.7
                and 0 <= p.x <= 1
                and 0 <= p.y <= 1
            ]
            if len(points) < 8:
                return 0
            return (max(p.x for p in points) - min(p.x for p in points)) * (
                max(p.y for p in points) - min(p.y for p in points)
            )

        ranked = sorted(((area(pose), i) for i, pose in enumerate(poses)), reverse=True)
        if ranked[0][0] > 0 and ranked[0][0] >= 2 * ranked[1][0]:
            poses = [poses[ranked[0][1]]]
    if len(poses) != 1:
        return []  # No pose / multiple people cannot establish a single participant.
    if len(poses[0]) != len(LANDMARK_NAMES):
        raise VideoInputError("Pose provider did not return the expected 33 landmarks.")
    return [
        PoseLandmark(
            index=index,
            name=name,
            x=point.x,
            y=point.y,
            z=point.z,
            visibility=point.visibility,
        )
        for index, (name, point) in enumerate(zip(LANDMARK_NAMES, poses[0], strict=True))
    ]


class MediaPipePoseProvider:
    def __init__(
        self,
        model_path: Path,
        *,
        include_visual_frames: bool = False,
        allow_dominant_pose: bool = False,
    ) -> None:
        self.model_path = model_path
        self.include_visual_frames = include_visual_frames
        self.allow_dominant_pose = allow_dominant_pose

    def extract(self, video_path: Path) -> PoseSequence:
        if not video_path.is_file():
            raise VideoInputError(
                "Video file does not exist. Supply a local MP4, MOV, or WebM path."
            )
        if video_path.suffix.lower() not in {".mp4", ".mov", ".webm"}:
            raise VideoInputError("Use an MP4, MOV, or WebM recording.")
        if not 0 < video_path.stat().st_size <= MAX_VIDEO_BYTES:
            raise VideoInputError("Video must be nonempty and at most 250 MiB.")
        if not self.model_path.is_file():
            raise VideoSetupError("Pose model is missing. Follow apps/api/VIDEO_SETUP.md.")
        try:
            import cv2
            import mediapipe as mp
        except ImportError as error:
            raise VideoSetupError(
                "Install optional packages: python -m pip install -r requirements-cv.txt"
            ) from error

        capture = cv2.VideoCapture(
            str(video_path),
            cv2.CAP_FFMPEG,
            [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000],
        )
        try:
            if not capture.isOpened():
                raise VideoInputError("Video could not be decoded. Try an H.264 MP4 export.")
            rotation = capture.get(cv2.CAP_PROP_ORIENTATION_META)
            if rotation not in {0, 90, 180, 270}:
                raise VideoInputError(
                    "Unsupported video rotation metadata. Export an upright clip."
                )
            capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
            if rotation and not capture.get(cv2.CAP_PROP_ORIENTATION_AUTO):
                raise VideoInputError(
                    "Decoder cannot apply video rotation. Export an upright clip."
                )
            sar_num = capture.get(cv2.CAP_PROP_SAR_NUM)
            sar_den = capture.get(cv2.CAP_PROP_SAR_DEN)
            if sar_num > 0 and sar_den > 0 and sar_num != sar_den:
                raise VideoInputError(
                    "Video has nonsquare pixels. Export with square pixels first."
                )
            options = mp.tasks.vision.PoseLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_poses=2,
                output_segmentation_masks=False,
            )
            with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
                return self._extract_frames(
                    capture,
                    cv2,
                    mp,
                    detector,
                    include_visual_frames=self.include_visual_frames,
                    allow_dominant_pose=self.allow_dominant_pose,
                )
        finally:
            capture.release()

    @staticmethod
    def _extract_frames(
        capture, cv2, mp, detector, *, include_visual_frames=False, allow_dominant_pose=False
    ) -> PoseSequence:
        frames = []
        visual_frames = []
        previous_time = -1.0
        last_bucket = -1
        image_shape = None
        started = monotonic()
        expected_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        # Decoder progress is checked at every frame; native read/inference calls may block.
        for frame_index in range(MAX_DECODED_FRAMES + 1):
            if monotonic() - started > 180:
                raise VideoProcessingTimeout(
                    "Video processing exceeded 180 seconds; use a shorter clip."
                )
            ok, bgr = capture.read()
            if not ok:
                if expected_frames > 0 and frame_index < expected_frames - 1:
                    raise VideoInputError("Video decoding stopped before the declared end.")
                break
            if frame_index == MAX_DECODED_FRAMES:
                raise VideoInputError("Video has too many source frames; use a shorter clip.")
            timestamp = capture.get(cv2.CAP_PROP_POS_MSEC)
            if not isfinite(timestamp) or timestamp < 0 or timestamp <= previous_time:
                raise VideoInputError(
                    "Decoder timestamps are missing or non-increasing; export an H.264 MP4."
                )
            previous_time = timestamp
            if timestamp > MAX_DURATION_MS:
                raise VideoInputError("Video exceeds 120 seconds; trim the clip first.")
            height, width = bgr.shape[:2]
            if max(width, height) > 4096 or width * height > 3840 * 2160:
                raise VideoInputError("Video resolution exceeds 4K; export at 1080p.")
            if image_shape is not None and image_shape != (width, height):
                raise VideoInputError("Video dimensions changed during decoding.")
            image_shape = (width, height)
            # Keep the first observed frame in each 1/15-second bucket. Never invent a frame.
            bucket = int((timestamp + 0.001) * 15 / 1000)
            if bucket == last_bucket:
                continue
            last_bucket = bucket
            if include_visual_frames and (
                not visual_frames or timestamp - visual_frames[-1][0] >= 500
            ):
                from app.services.visual_review import encode_review_frame

                try:
                    visual_frames.append((round(timestamp), encode_review_frame(bgr)))
                except Exception as error:
                    logger.warning("Visual sampling unavailable (%s)", type(error).__name__)
                    visual_frames.clear()
                    include_visual_frames = False
            if len(frames) >= MAX_SAMPLED_FRAMES:
                raise VideoInputError(
                    "Video exceeds 1800 sampled frames; trim it below 120 seconds."
                )
            image = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            )
            result = detector.detect_for_video(image, round(timestamp))
            frames.append(
                PoseFrame(
                    frame_index=frame_index,
                    timestamp_ms=round(timestamp),
                    landmarks=map_landmarks(
                        result.pose_landmarks, allow_dominant_pose=allow_dominant_pose
                    ),
                )
            )
        if not frames:
            raise VideoInputError("Video contains no decodable frames.")
        if len(visual_frames) > 64:
            visual_frames = [
                visual_frames[round(i * (len(visual_frames) - 1) / 63)] for i in range(64)
            ]
        return PoseSequence(
            frames, image_shape[0], image_shape[1], round(previous_time), visual_frames
        )
