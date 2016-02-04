import concurrent.futures
import glob
import json
import os
from urllib.parse import urlparse
from urllib.request import urlopen
import sys

from boto.s3.connection import S3Connection
from boto.s3.key import Key


DATA_DIR = 'data'
KEYS = (
    'video_flv_url',
    'video_mp4_url',
    'video_ogv_url',
    'video_webm_url',
)
PYTUBE_BUCKET = 'pytube'
AWSID, AWSSECRET = os.environ.get('AWSID'), os.environ.get('AWSSECRET')


def generate_paths_to_copy(json_file_paths):
    for json_file_path in json_file_paths:

        with open(json_file_path) as fp:
            data = json.load(fp)

        if isinstance(data, dict):
            data = [data]

        for media_record in data:
            for key in KEYS:
                value = media_record.get(key)
                if value and 'rackcdn' in value:
                    yield value


def copy(args):
    bucket, source, dest = args
    sys.stdout.write('Working on {}\n'.format(source))
    sys.stdout.flush()
    response = urlopen(source)

    headers = {'Content-Type' : response.info().get_content_type()}
    k = Key(bucket)
    k.name = dest
    k.set_contents_from_string(response.read(), headers)


def main():
    conn = S3Connection(AWSID, AWSSECRET)
    bucket = conn.get_bucket(PYTUBE_BUCKET)

    pattern = '{}/**/*.json'.format(DATA_DIR)
    json_file_paths = glob.iglob(pattern, recursive=True)
    paths = sorted(generate_paths_to_copy(json_file_paths))

    args = ((bucket, path, urlparse(path).path) for path in paths)

    with concurrent.futures.ThreadPoolExecutor() as p:
        futures = p.map(copy, args)
        for future in concurrent.futures.as_completed(futures):
            future.result()  # allow exceptions to percolate up

    print('Done.')


main()

