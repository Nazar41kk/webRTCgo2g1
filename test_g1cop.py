import asyncio
import cv2
import queue
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

frame_queue = queue.Queue()

async def video_callback(track):
    print("Video track received, starting stream...")
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")
        frame_queue.put(img)

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
    await conn.connect()
    print("Connected! Enabling video...")

    conn.video.add_track_callback(video_callback)
    conn.video.switchVideoChannel(True)

    while True:
        if not frame_queue.empty():
            img = frame_queue.get()
            cv2.imshow("G1 Camera", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        await asyncio.sleep(0.001)

    cv2.destroyAllWindows()

asyncio.run(main())