import datetime
import pytz


def get_publish_time(args):
    """
    Takes user inputted time, and coverts to a datetime object
    """
    user_time = args["publish_time"]
    time_split = user_time.split(" ")
    date = time_split[0].split("/")
    time = time_split[1].split(":")

    date_time = datetime.datetime(
        int(date[2]),
        int(date[0]),
        int(date[1]),
        int(time[0]),
        int(time[1]),
        int(time[2]),
    )
    pt = pytz.timezone("US/Pacific")

    pt_time = pt.localize(date_time)
    utc_time = pt_time.astimezone(pytz.timezone("utc"))

    return pt_time, utc_time