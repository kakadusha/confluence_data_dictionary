#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import requests
import time

API_BASE_URL = "https://kb.ertelecom.ru/rest/api"
SLEEP_TIME_BEFOR_SEARCH = 3  # seconds, Confluence server needs time to index created pages


def search_by_title(space_key, title_pattern, auth):
    responce = requests.get(
        auth=auth,
        url=f"{API_BASE_URL}/search?cql=title~\"{title_pattern}\"",
        headers={"content-type": "application/json"},
        data=json.dumps({"space": {"key": space_key}}),
    )
    results = json.loads(responce.content)
    return results.get("results")


def get_version(page_id, auth):
    response = requests.get(
        auth=auth,
        url=f"{API_BASE_URL}/content/{page_id}?expand=version",
        headers={"content-type": "application/json"},
    )
    return json.loads(response.content)['version']['number']

#todo: consider to remove as Unused
def post_page(space_key, parent_id, title, content, auth):
    data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": content, "representation": "wiki"}},
    }

    #  print(json.dumps(data))
    responce = requests.post(
        auth=auth,
        url=API_BASE_URL + "/content/",
        headers={"content-type": "application/json"},
        data=json.dumps(data),
    )

    responce_data = json.loads(responce.content)
    if responce.status_code in (200, 204):
        return responce_data["id"]
    else:
        print(f"- x - {responce.status_code} - parent page set to DEFAULT\n{responce.text}")
        return parent_id


def add_page(space_key, parent_id, title, content, auth, print_error_responce=True):
    data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": content, "representation": "wiki"}},
    }
    #  print(json.dumps(data))
    responce = requests.post(
        auth=auth,
        url=API_BASE_URL + "/content/",
        headers={"content-type": "application/json"},
        data=json.dumps(data),
    )
    responce_data = json.loads(responce.content)
    if responce.status_code in (200, 204):
        return int(responce_data["id"])
    else:
        if print_error_responce: print(f"   ! add_page failed - {responce.status_code} - bad responce\n   {responce.text}")
        return -1


def update_page(space_key, parent_id, page_id, title, content, auth, print_error_responce=True):
    version = get_version(page_id, auth)

    data = {
        "id": page_id,
        "type": "page",
        "title": title,
        "version": {"number": version + 1},
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {
            "storage": {
                "value": content,
                "representation": "wiki"
            }
        }
    }

    responce = requests.put(
        auth=auth,
        url=f"{API_BASE_URL}/content/{page_id}",
        headers={"content-type": "application/json"},
        data=json.dumps(data)
    )

    responce_data = json.loads(responce.content)
    if responce.status_code in (200, 204):
        return int(responce_data["id"])
    elif responce.status_code == 400 and ("A page with this title already exists" in responce_data.get("message")):
        if print_error_responce: print(f"   update_page failed - same content page alreeady exists")
        return -1
    else:
        if print_error_responce: print(f"   ! update_page failed - {responce.status_code} - bad responce\n   {responce.text}")
        return -1
    #return responce_data.get('id') or page_id  # unsafe


def add_or_update_page(space_key, parent_id, title, content, auth, print_error_responce=True):
    page_id = add_page(space_key, parent_id, title, content, auth, print_error_responce=False)
    if page_id < 0:
        time.sleep(SLEEP_TIME_BEFOR_SEARCH)
        res = search_by_title(space_key, title, auth)
        if len(res) == 1:
            id = res[0]["content"]["id"]
            print(f"   found same name page {id}, updating...")
            return update_page(space_key, parent_id, int(res[0]["content"]["id"]), title, content, auth, print_error_responce)
    else:
        return page_id


def delete_page(space_key, page_id, auth):
    responce = requests.delete(
        auth=auth,
        url=f"{API_BASE_URL}/content/{page_id}",
        headers={"content-type": "application/json"},
        data=json.dumps({"space": {"key": space_key}}),
    )
    if responce.status_code in (200, 204):
        print(f"Delete {page_id} - OK")
    else:
        if responce.status_code == 404:
            # 404 - not exists it's OK
            print(f"Delete {page_id} - Page not exists: {responce}")
        else:
            print(f"Delete {page_id} - Error responce: {responce}")
    return responce