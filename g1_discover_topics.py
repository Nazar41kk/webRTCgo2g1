import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

seen_topics = {}

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
    await conn.connect()
    print("Connected! Intercepting all messages...\n")

    # Try to log connection details
    try:
        stats = await conn.pc.getStats()
        for report in stats.values():
            if hasattr(report, 'type') and report.type == 'candidate-pair' and getattr(report, 'state', None) == 'succeeded':
                print(f"Connected to remote IP: {getattr(report, 'remoteCandidateId', 'unknown')}")
    except Exception as e:
        print(f"(Could not get connection stats: {e})")


    # Patch run_resolve to log every message topic and type
    original_run_resolve = conn.datachannel.pub_sub.run_resolve

    def patched_run_resolve(message):
        topic = message.get("topic", "<no topic>")
        msg_type = message.get("type", "<no type>")
        data = message.get("data")
        data_summary = ""
        if isinstance(data, dict):
            data_summary = str(list(data.keys()))
        elif data is not None:
            data_summary = f"({type(data).__name__}, len={len(str(data))})"

        key = (msg_type, topic)
        if key not in seen_topics:
            seen_topics[key] = 0
            print(f"NEW  type={msg_type!r:20s}  topic={topic!r:40s}  data={data_summary}")
        else:
            seen_topics[key] += 1
            if seen_topics[key] % 10 == 0:
                print(f"[x{seen_topics[key]}] type={msg_type!r:20s}  topic={topic!r:40s}")

        original_run_resolve(message)

    conn.datachannel.pub_sub.run_resolve = patched_run_resolve

    # Try disabling traffic saving to unlock full data stream
    await conn.datachannel.disableTrafficSaving(True)

    # Try subscribing to common candidate topics
    candidates = [
        # Go2 UTLidar topics
        "ulidar", "utlidar", "rt/lidar", "lidar",
        "slam", "rt/slam", "map", "rt/map",
        "rt/utlidar/voxel_map_compressed",
        "rt/utlidar/voxel_map",
        "rt/pointcloud2",
        # G1 Mid360 / Livox topics
        "rt/mid360/lidar",
        "rt/mid360/voxel_map",
        "rt/mid360/voxel_map_compressed",
        "rt/livox/lidar",
        "rt/livox/voxel_map",
        "rt/scan",
        "rt/scan_matched_points",
        "rt/pointcloud",
        "rt/cloud",
        "rt/g1/lidar",
    ]
    for topic in candidates:
        conn.datachannel.pub_sub.subscribe(topic, lambda msg, t=topic: None)
        print(f"Subscribed to: {topic}")

    print("\nListening for 30 seconds...\n")
    await asyncio.sleep(30)

    print("\n=== Summary of all seen topics ===")
    for (msg_type, topic), count in sorted(seen_topics.items()):
        print(f"  type={msg_type!r:20s}  topic={topic!r:40s}  count={count}")

asyncio.run(main())
