import argparse
import os
from os.path import exists
import boto3
import urllib.parse
import jinja2
import configparser
import mimetypes

BUCKET_NAME = 'hw1'


def upload(album, path):
    if path is None:
        path = os.getcwd()

    for filename in os.listdir(path):
        f = os.path.join(path, filename)
        if os.path.isfile(f):
            print(f)
            if mimetypes.MimeTypes().guess_type(f)[0] == 'image/jpeg':
                try:
                    s3.upload_file(Filename=f,
                                   Bucket=BUCKET_NAME,
                                   Key=urllib.parse.quote(album + '/' + f.split('\\')[-1]))
                except:
                    print("Exception thrown. x does not exist.")


def download(album, path):
    if path is None:
        path = os.getcwd()
    objects = s3.list_objects(Bucket=BUCKET_NAME, Prefix=album, )['Contents']
    if len(objects) == 0:
        raise Exception
    for el_obj in objects:
        el = el_obj['Key']
        s3.download_file(BUCKET_NAME, el, path + '/' + el.split('/')[-1])


def list(album):
    if album is None:
        objects = s3.list_objects(Bucket=BUCKET_NAME)['Contents']
        els = set()
        for el_obj in objects:
            el = el_obj['Key']
            if len(el_obj['Key'].split('/')) > 1:
                els.add(el.split('/')[0])
    else:
        objects = s3.list_objects(Bucket=BUCKET_NAME, Prefix=album, )['Contents']
        els = set()
        for el_obj in objects:
            el = el_obj['Key']
            els.add(el.split('/')[-1])
    if len(objects) == 0:
        raise Exception
    for el in els:
        print(el)


def delete(album, photo):
    if photo is None:
        objects = s3.list_objects(Bucket=BUCKET_NAME, Prefix=album, )['Contents']
        for el_obj in objects:
            el = el_obj['Key'].split('/')[-1]
            s3.delete_object(Bucket=BUCKET_NAME, Key=album + '/' + el)
    else:
        s3.delete_object(Bucket=BUCKET_NAME, Key=album + '/' + photo)


def mksite():
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    s3.put_bucket_website(Bucket=BUCKET_NAME,
                          WebsiteConfiguration=website_configuration)

    s3.upload_file(Filename='error.html', Key='error.html', Bucket=BUCKET_NAME)
    objects = s3.list_objects(Bucket=BUCKET_NAME)['Contents']
    els = set()
    for el_obj in objects:
        el = el_obj['Key'].split('/')[0]
        if len(el_obj['Key'].split('/')) > 1:
            els.add(el)
    print(els)
    ind = 0
    for el in els:
        cnts = s3.list_objects(Bucket=BUCKET_NAME, Prefix=el)['Contents']
        urls = []
        titles = []
        for f in cnts:
            urls.append(endpoint_url + '/' + BUCKET_NAME + '/' + (f['Key']))
            titles.append(f['Key'].split('/')[-1])
        with open('album_tmplt.html', 'r') as html_text:
            my_templ = jinja2.Template(html_text.read())
            with open('album' + str(ind) + '.html', 'w') as f2:
                f2.write(my_templ.render(titles=titles, urls=urls))
        s3.upload_file(Filename='album' + str(ind) + '.html', Key='album' + str(ind) + '.html', Bucket=BUCKET_NAME)
        ind += 1
    with open('index_tmplt.html', 'r') as html_text:
            my_templ = jinja2.Template(html_text.read())
            with open('index.html', 'w') as f2:
                f2.write(my_templ.render(titles=els))
    s3.upload_file(Filename="index.html", Key="index.html", Bucket=BUCKET_NAME)



# [DEFAULT]
# bucket = INPUT_BUCKET_NAME
# aws_access_key_id = INPUT_AWS_ACCESS_KEY_ID
# aws_secret_access_key = INPUT_AWS_SECRET_ACCESS_KEY
# region = ru-central1
# endpoint_url = https://storage.yandexcloud.net
def init(create_file=False):
    path = os.path.expanduser('~\\.config\\cloudphoto\\cloudphotorc')
    global endpoint_url
    if not exists(path) and create_file:
        try:
            os.makedirs(os.path.expanduser('~\\.config\\cloudphoto'))
        except:
            print('path already exists')
        bucket = input('Enter bucket')
        aws_access_key_id = input('Enter aws_access_key_id')
        aws_secret_access_key = input('Enter aws_secret_access_key')
        region = input('Enter region')
        endpoint_url = input('Enter endpoint_url')
        config = configparser.ConfigParser()
        config['DEFAULT']['bucket'] = bucket
        config['DEFAULT']['aws_access_key_id'] = aws_access_key_id
        config['DEFAULT']['aws_secret_access_key'] = aws_secret_access_key
        config['DEFAULT']['region'] = region
        config['DEFAULT']['endpoint_url'] = endpoint_url
        with open(path, 'w') as configfile:  # save
            config.write(configfile)
    elif exists(path):
        config = configparser.ConfigParser()
        config.read(path)
        bucket = config['DEFAULT']['bucket']
        aws_access_key_id = config['DEFAULT']['aws_access_key_id']
        aws_secret_access_key = config['DEFAULT']['aws_secret_access_key']
        region = config['DEFAULT']['region']
        endpoint_url = config['DEFAULT']['endpoint_url']
    else:
        raise Exception
    session = boto3.session.Session(aws_secret_access_key=aws_secret_access_key,
                                    aws_access_key_id=aws_access_key_id,
                                    region_name=region)
    global s3, BUCKET_NAME
    s3 = session.client(
        service_name='s3',
        endpoint_url=endpoint_url
    )
    try:
        s3.list_objects(Bucket=bucket)
    except:
        s3.create_bucket(
            Bucket=bucket,
        )

    BUCKET_NAME = bucket


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init()

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('command', metavar='COMMAND', help='command')
    parser.add_argument('--path',
                        help='oath')
    parser.add_argument('--album',
                        help='album name')
    parser.add_argument('--photo',
                        help='photo name')
    args = parser.parse_args()
    command = args.command
    if command == 'upload':
        upload(args.album, args.path)
    elif command == 'init':
        init(create_file=True)
    elif command == 'download':
        download(args.album, args.path)
    elif command == 'delete':
        delete(args.album, args.photo)

    elif command == 'list':
        list(args.album)
    elif command == 'mksite':
        mksite()