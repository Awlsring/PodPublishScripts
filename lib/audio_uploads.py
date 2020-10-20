from boto3 import Session
from botocore.config import Config
import json
import os


def create_s3_client():
    """
    Returns boto s3 client
    """
    session = Session(profile_name="PodPublish")

    config = Config(connect_timeout=10, read_timeout=10, retries={"max_attempts": 10})

    return session.client("s3", config=config)


def upload_episode_audio(args, client, ep_date):
    """
    Uploads episodes audio to S3.
    Returns link to episode
    """
    print(f"Uploading {args['episode'].name} as mpp-{ep_date}.mp3")

    client.upload_file(
        args["episode"].name,
        "motionpixelsepisodes",
        f"2020/mpp-{ep_date}.mp3",
        ExtraArgs={"ACL": "public-read"},
    )

    print("Done")

    return f"https://motionpixelsepisodes.s3-us-west-2.amazonaws.com/2020/mpp-{ep_date}.mp3"


def upload_episode_art(args, client, ep_date):
    """
    Uploads Audio thumbnail to S3 Bucket.
    Returns link to art
    """
    print(f"Uploading {args['art'].name} as mpp-art-{ep_date}.mp3")

    client.upload_file(
        args["art"].name,
        "motionpixelspodcast.com",
        f"episodeArt/mpp-art-{ep_date}.png",
        ExtraArgs={"ACL": "public-read"},
    )

    print("Done")

    return f"https://s3-us-west-2.amazonaws.com/motionpixelspodcast.com/episodeArt/mpp-art-{ep_date}.png"


def update_xml(args, episode_link, art_link, pt_time):
    """
    Updates podcast xml file with new episodes
    Returns XML file name
    """

    print("Formatting XML")

    with open(args["metadata"].name) as metadata_json:
        metadata = json.load(metadata_json)

        title = metadata["Audio"]["Title"]
        summary = metadata["Audio"]["Summary"]
        description = metadata["Audio"]["Description"]
        rss_date = pt_time.strftime("%a, %d %b %Y %H:%M:%S %z")
        keywords = metadata["Audio"]["Keywords"]
        length = metadata["Audio"]["Length"]
        bits = metadata["Audio"]["Bits"]

    entry = f"""
            <item>
                <title>{title}</title>
                <link>{episode_link}</link>
                <itunes:image href="{art_link}" />
                <enclosure url="{episode_link}" type="audio/mpeg" length="{bits}" />
                <guid>{episode_link}</guid>
                <pubDate>{rss_date}</pubDate>
                <itunes:author>August Meyer and Matthew Rawlings</itunes:author>
                <itunes:duration>{length}</itunes:duration>
                <itunes:keywords>{keywords}</itunes:keywords>
                <itunes:explicit>yes</itunes:explicit>
                <itunes:summary>{description}

    {summary}</itunes:summary>
                <description>{description}</description>
            </item>\n"""

    files = [f for f in os.listdir(".") if os.path.isfile(f)]

    for file in files:
        if file.startswith("podcast.xml"):
            podcast_xml_file = file

    with open(podcast_xml_file, "r") as xml:
        podcast_xml = xml.readlines()

    i = 0
    for line in podcast_xml:
        if line.startswith("<!-- Episodes -->"):
            podcast_xml[i] = line + entry
        print(podcast_xml[i])
        i = i + 1

    with open(podcast_xml_file, "w") as new_xml:
        for line in podcast_xml:
            new_xml.write(line)

    return podcast_xml_file


def upload_xml(args, client, podcast_xml_file):
    """
    Uploads update XML to s3
    """
    print("Uploading XML")

    client.upload_file(
        podcast_xml_file,
        "motionpixelspodcast.com",
        "podcast.xml",
        ExtraArgs={"ACL": "public-read"},
    )
    print("Done")