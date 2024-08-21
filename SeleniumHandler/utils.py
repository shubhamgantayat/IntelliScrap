import urllib
from urllib.request import urlretrieve


def download(link, path, max_retries=2):
    retries = 0
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    while retries < max_retries:
        try:
            retries += 1
            urlretrieve(link, filename=path)
            return 0
        except Exception as e:
            print(e)
    return -1

