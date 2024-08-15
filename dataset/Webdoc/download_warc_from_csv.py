import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import argparse
import time
import json
from io import BytesIO
import gzip
import os
from itertools import islice, chain
from multiprocessing import Process
from multiprocessing import Pool
import sys
from importlib import reload
import itertools
import pickle
import logging
import signal
import pandas as pd
from urllib.parse import urlparse
import multiprocessing
from multiprocessing import Process, Queue, Value, cpu_count
from multiprocessing.queues import Empty

# def requests_retry_session(retries=8, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
#     session = session or requests.Session()
#     retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
#                   status_forcelist=status_forcelist)
#     adapter = HTTPAdapter(max_retries=retry)
#     session.mount('http://', adapter)
#     return session


def get_url(warc):
    thiswarc = warc
    matched_lines = [line for line in thiswarc.split('\n') if "WARC-Target-URI: " in line]
    url = matched_lines[0].replace('WARC-Target-URI: ', '')
    url = url.replace("\r", "")
    # print url
    return url


def get_uri(warc):
    matched_lines = [line for line in warc.split('\n') if "WARC-Record-ID: <urn:uuid:" in line]
    uri = matched_lines[0].replace('WARC-Record-ID: <urn:uuid:', '')
    uri = uri.replace('>', '')
    uri = uri.replace("\r", "")
    return uri


def get_name(url):
    name = os.path.basename(url)
    if len(name) < 1:
        name = url
    return name


session = requests.Session()
def requests_retry_session():
    # return requests.Session()
    return session

def download_page(job, i):
    # print "Downloading " + record['filename']
    filepath = job['directory'] + '/' + job['uri']
    if os.path.exists(filepath):
        print("Already downloaded %s" % filepath)
        return job['uri']
    offset, length = int(job['offset']), int(job['length'])
    directory = job['directory']
    offset_end = offset + length - 1

    # We'll get the file via HTTPS so we don't need to worry about S3 credentials
    # Getting the file on S3 is equivalent however - you can request a Range
    prefix = 'https://commoncrawl.s3.amazonaws.com/'
    prefix = 'https://data.commoncrawl.org/'
    url = ""
    uri = None
    # We can then use the Range header to ask for just this set of bytes
    try:
        resp = requests_retry_session().get(prefix + job['filename'],
                            headers={'Range': 'bytes={}-{}'.format(offset, offset_end)})
    except Exception as x:
        print('It failed :(', str(x))
        raise
    else:
        # The page is stored compressed (gzip) to save space
        # We can extract it using the GZIP library
        raw_data = BytesIO(resp.content)

        try:
            f = gzip.GzipFile(fileobj=raw_data)

            data = ''
            for line in f.readlines():
                # line = line.decode("utf-8")
                line = line.decode(job.get('charset', 'utf-8'))
                data += str(line)

        except (OSError, IOError) as err:  # except OSError because IOError was merged to OSError in Python 3.3
            print(err)
            print("Exception for directory: %s" % directory.strip())
            data = ""
        except UnicodeDecodeError:
            print("Failed to decode content stream")
            data = ""

        response = ""
        if len(data):
            try:

                try:
                    warc, header, response = data.strip().split('\r\n\r\n', 2)
                except Exception as e:
                    # print e
                    warc, header = data.strip().split('\r\n\r\n', 2)

                # response_code = header.
                http_res_line = header.strip().split('\n')[0]
                http_res_code_array = http_res_line.split(' ')
                http_res_code = http_res_code_array[1] + ' ' + http_res_code_array[2]
                url = get_url(warc)
                # print url
                name = get_name(url)

                if name.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.mp3', '.avi', '.zip', '.tar',
                                            '.gz')):  # or name == 'robots.txt' or len(response)==0:
                    print(url + '\tnull\tfile not allowed')
                elif len(response) == 0:
                    print(url + '\tnull' + '\t' + http_res_code)
                elif name == 'robots.txt':
                    print(url + '\tnull' + '\trobots')
                else:
                    uri = get_uri(warc)
                    # print uri
                    os.makedirs(directory, exist_ok=True)
                    filepath = directory + '/' + uri
                    file = open(filepath, 'w')
                    file.write(response)
                    file.close()
                    print(url + '\t' + uri + '\t' + http_res_code)
            except Exception as e:
                print (url, " skipped", str(e))
                pass

        resp.close()

    return uri


def run_workers(num_workers, jobs):
    """ Queue up all jobs start workers with job_queue
    catch KeyboardInterrupt to allow interrupting all workers
    Not using Pool to better hande KeyboardInterrupt gracefully
    Adapted from example at:
    http://bryceboe.com/2012/02/14/python-multiprocessing-pool-and-keyboardinterrupt-revisited/
    """

    # Queue up all jobs
    job_queue = Queue()
    counter = Value('i', 0)

    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    # optionally shuffle queue
    # if shuffle:
    #     jobs = list(jobs)
    #     random.shuffle(jobs)

    for job in jobs:
        job_queue.put(job)

    workers = []

    for i in range(0, num_workers):
        tmp = Process(target=do_work,
                      args=(job_queue, counter, i, return_dict))
        tmp.start()
        workers.append(tmp)

    try:
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C, interrupting all workers')
        for worker in workers:
            worker.terminate()
            worker.join()
        raise

    return return_dict


def do_work(job_queue, counter, i, return_dict):
    """ Process work function, read more fetch page jobs
    from queue until all jobs are finished
    """
    finished = []
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            job = job_queue.get_nowait()
            # fetch_result_page(job)
            uri = download_page(job, i)

            num_done = 0
            with counter.get_lock():
                counter.value += 1
                num_done = counter.value

            job['uri'] = uri
            finished.append(job)
            logging.info('{0} page(s) finished'.format(num_done))

        except Empty:
            pass

        except KeyboardInterrupt:
            break

        except Exception as e:
            if not job:
                raise

            time.sleep(10)

            retries = job.get('retries', 0)
            if retries < job['max_retries']:
                logging.error('Retrying Page {0} {1}'.format(job['url'], str(e)))
                job['retries'] = retries + 1
                job_queue.put_nowait(job)
            else:
                logging.error('Max retries exceeded for page {0}'.
                              format(job['url']))

    return_dict[i] = finished
    logging.info('process finished ' + str(len(finished)))




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('cdx_file',
                        help='cdx record file')
    parser.add_argument("-o", "--output_folder", required=True, help="The folder where files would be output")
    parser.add_argument('-p', '--processes', type=int, help='Number of worker processes to use')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s: [%(levelname)s]: %(message)s',
                        level=logging.INFO)

    logging.getLogger("requests").setLevel(logging.WARNING)

    recs = pd.read_csv(args.cdx_file, header='infer')
    # convert df to list of dicts
    recs = recs.to_dict('records')

    if not recs:
        logging.info('empty cdx record')

    directory = "warc_files"

    # if os.path.exists(directory):
    #     logging.warning('cdx already processed')
    #     sys.exit(0)

    os.makedirs(directory, exist_ok=True)

    recs_todo = []
    for rec in recs:
        rec['directory'] = args.output_folder + '/' + rec['domain'].replace('.', '_')
        rec['max_retries'] = 5
        rec['rough_total'] = len(recs)
        recs_todo.append(rec)
    logging.info('queuing {} downloads'.format(len(recs_todo)))
    recs = recs_todo
    # recs = recs[:5]

    if not args.processes:
        try:
            num_workers = cpu_count() * 2
        except NotImplementedError:
            num_workers = 4
    else:
        num_workers = args.processes

    try:
        return_dict = run_workers(num_workers, recs)
    except:
        import shutil
        shutil.rmtree(directory)

    finished = []
    for fins in return_dict.values():
        finished.extend(fins)

    
