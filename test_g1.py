import asyncio
import cv2
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

async def video_callback(track):
    print("Video track received, starting stream...")
    while True:
        try:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")
            cv2.imshow("G1 Camera", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"Video error: {e}")
            break
    cv2.destroyAllWindows()

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)

    await conn.connect()
    print("Connected! Enabling video...")

    conn.video.add_track_callback(video_callback)
    conn.video.switchVideoChannel(True)

    await asyncio.sleep(300)  # stream for 5 minutes, press q to quit

asyncio.run(main())