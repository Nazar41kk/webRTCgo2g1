import asyncio
import threading
import numpy as np
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

latest_points = None
points_lock = threading.Lock()

def lidar_callback(msg):
    global latest_points
    try:
        points = msg["data"]["data"]["points"]
        if points is not None and len(points) > 0:
            with points_lock:
                latest_points = np.array(points)
    except (KeyError, TypeError) as e:
        print(f"Callback error: {e}, keys={list(msg.get('data', {}).keys())}")

async def webrtc_task():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)

    await conn.connect()
    print("Connected!")

    # Native decoder gives clean Nx3 numpy points instead of raw mesh buffers
    conn.datachannel.set_decoder("native")

    await conn.datachannel.disableTrafficSaving(True)
    conn.datachannel.pub_sub.subscribe("rt/utlidar/voxel_map_compressed", lidar_callback)
    print("Subscribed to rt/utlidar/voxel_map_compressed\n")

    while True:
        await asyncio.sleep(0.1)

def run_asyncio():
    asyncio.run(webrtc_task())

def main():
    t = threading.Thread(target=run_asyncio, daemon=True)
    t.start()

    fig = plt.figure(figsize=(10, 10), facecolor="black")
    ax = fig.add_subplot(111)
    ax.set_facecolor("black")
    ax.set_title("G1 LiDAR — Top-down SLAM view", color="white", fontsize=14)
    ax.set_xlabel("X (m)", color="white")
    ax.set_ylabel("Y (m)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("white")
    ax.set_xlim(-8, 8)
    ax.set_ylim(-8, 8)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.15, color="white")

    # Robot marker at origin
    ax.plot(0, 0, "r+", markersize=14, markeredgewidth=2, zorder=10)

    scatter = ax.scatter([], [], s=2, c=[], cmap="plasma",
                         vmin=-0.5, vmax=2.0, alpha=0.85)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Height Z (m)", color="white")
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    info_text = ax.text(0.02, 0.97, "Waiting for data...", transform=ax.transAxes,
                        color="lime", fontsize=9, va="top", family="monospace")

    frame_count = [0]

    def update(_frame):
        with points_lock:
            pts = latest_points
        if pts is not None and len(pts) > 0:
            x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
            scatter.set_offsets(np.column_stack((x, y)))
            scatter.set_array(z)
            frame_count[0] += 1
            info_text.set_text(
                f"Points: {len(pts):,}  |  Frame: {frame_count[0]}\n"
                f"X:[{x.min():.1f}, {x.max():.1f}]  "
                f"Y:[{y.min():.1f}, {y.max():.1f}]  "
                f"Z:[{z.min():.1f}, {z.max():.1f}]"
            )
        return scatter, info_text

    ani = animation.FuncAnimation(fig, update, interval=100,
                                  blit=True, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
