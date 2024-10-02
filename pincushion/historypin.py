import logging
import time

import requests
import tqdm

logger = logging.getLogger(__name__)

def get_data(user_id: int):
    data = {}
    data['user'] = get_json('user/get', {"id": user_id})
    data['collections'] = list(get_listing(user_id, 'projects', 'collection'))
    data['tours'] = list(get_listing(user_id, 'projects', 'tour'))
    data['pins'] = list(get_listing(user_id, 'pin'))

    return data

def get_listing(user_id: int, listing_type: str, item_type=None, progress=True):
    """
    Iterate through a Historypin listing for a user by type (projects or pin). For projects
    you need to further specify whether you want collections or tours.
    """
    params = {"user": user_id, "page": 0, "limit": 100}

    if item_type is not None:
        params["type"] = item_type

    if progress:
        count = get_json(f'{listing_type}/listing', params)['count']
        desc = item_type or listing_type
        bar = tqdm.tqdm(desc=f"{desc:20}", total=count)
    else:
        bar = None

    while True:
        params['page'] += 1
        page = get_json(f'{listing_type}/listing', params)
        if len(page['results']) == 0:
            break

        for result in page['results']:

            if bar is not None:
                bar.update(1)

            # get and return the full item metadata for the resource
            if listing_type == 'projects':
                yield get_json(f'{result["slug"]}/projects/get', {})
            elif listing_type == 'pin':
                yield get_json('pin/get', {"id": result['id']})


def get_json(api_path: str, params: dict, sleep=0.5) -> dict:
    time.sleep(sleep)
    url = f'https://www.historypin.org/en/api/{api_path}.json'
    logger.info(f"fetching {url} {params}")
    return requests.get(url, params=params).json()