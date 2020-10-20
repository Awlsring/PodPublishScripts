import argparse
import time
import lib.audio_uploads as audio
import lib.video_uploads as video
from lib import tools

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=argparse.FileType("r"))
    parser.add_argument("--art", type=argparse.FileType("r"))
    parser.add_argument("--video", type=argparse.FileType("r"))
    parser.add_argument("--thumbnail", type=argparse.FileType("r"))
    parser.add_argument("--metadata", type=argparse.FileType("r"))
    parser.add_argument(
        "--publish-time",
        type=str,
        required=True,
        help="Format: <MM/DD/YYYY HH:MM:SS>. In Pacific time.",
    )

    args = vars(parser.parse_args())

    # Prep Variables for Functions
    pt_time, utc_time = tools.get_publish_time(args)
    ep_date = pt_time.strftime("%m-%d-%y")

    client = audio.create_s3_client()

    if "episode" in args:
        # Upload Audio Files
        episode_audio = audio.upload_episode_audio(args, client, ep_date)
        art_audio_audio = audio.upload_episode_art(args, client, ep_date)
        xml_file = audio.update_xml(args, episode_audio, art_audio_audio, pt_time)
        audio.upload_xml(args, client, xml_file)

    if "video" in args:
        # Upload Video Files
        service = video.create_service()
        video.upload_video(args, service, utc_time)
