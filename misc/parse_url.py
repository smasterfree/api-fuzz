import random
import urlparse

from misc.utils import id_generator


def fuzz_url_path(url):
    r = urlparse.urlparse(url)
    url_path = r.path
    path_elem = str(url_path).split('/')

    select_elem = random.choice(path_elem)

    # fuzz selected element
    for i, item in enumerate(path_elem):
        if item == select_elem:
            if i == 0:
                pass
            else:
                path_elem[i] = id_generator()

    new_path = '/'.join(path_elem)
    return new_path


if __name__ == '__main__':
    test_url = "http://10.187.3.58:8774/v2/9ac08939bf67465c88cd638107e0a6d6/os-tag-types/11/extra-specs"
    for i in range(100):
        print fuzz_url_path(test_url)
