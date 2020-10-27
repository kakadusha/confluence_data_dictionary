#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import time
import requests
import sys

DEBUG = False

DATA = {"space": {"key": "BD"}}
CONNECTIONS_FILE = "connections.json"
SLEEP_TIME_AFTER_CYCLE = 3  # seconds


def collect_pages(connections):
    pages = []

    responce = requests.get(
        auth=(connections["confluence"]["user"], connections["confluence"]["password"]),
        url="https://kb.ertelecom.ru/rest/api/search?cql=title~table*"
        if not DEBUG
        else "https://kb.ertelecom.ru/rest/api/search?cql=title~nable_dbg*",
        headers={"content-type": "application/json"},
        data=json.dumps(DATA),
    )

    results = json.loads(responce.content)
    pages.extend(results.get("results"))

    responce = requests.get(
        auth=(connections["confluence"]["user"], connections["confluence"]["password"]),
        url="https://kb.ertelecom.ru/rest/api/search?cql=title~database*"
        if not DEBUG
        else "https://kb.ertelecom.ru/rest/api/search?cql=title~natabase_dbg*",
        headers={"content-type": "application/json"},
        data=json.dumps(DATA),
    )

    results = json.loads(responce.content)
    pages.extend(results.get("results"))

    responce = requests.get(
        auth=(connections["confluence"]["user"], connections["confluence"]["password"]),
        url='https://kb.ertelecom.ru/rest/api/search?cql=title~"Hive Data Dictionary"'
        if not DEBUG
        else 'https://kb.ertelecom.ru/rest/api/search?cql=title~"Nive Data Dictionary"',
        headers={"content-type": "application/json"},
        data=json.dumps(DATA),
    )

    results = json.loads(responce.content)
    pages.extend(results.get("results"))

    responce = requests.get(
        auth=(connections["confluence"]["user"], connections["confluence"]["password"]),
        url='https://kb.ertelecom.ru/rest/api/search?cql=title~"ClickHouse Data Dictionary"'
        if not DEBUG
        else 'https://kb.ertelecom.ru/rest/api/search?cql=title~"Nive Data Dictionary"',
        headers={"content-type": "application/json"},
        data=json.dumps(DATA),
    )

    results = json.loads(responce.content)
    pages.extend(results.get("results"))

    return pages


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "DEBUG":
        print("[!] Running in DEBUG mode, page names cnanged Table->Nable_dbg, Database->Natabase_dbg and Hive->Nive")
        DEBUG = True

    with open(CONNECTIONS_FILE, "r") as connections_file:
        connections = json.load(connections_file)

    while True:
        pages = collect_pages(connections)
        if not pages:
            sys.exit(0)

        unic_pages = set([p["content"]["id"] for p in pages])
        print(f"{len(unic_pages)} page(s) found removing...")

        for page in unic_pages:
            print(f"Removing {page}", end=" ")
            responce = requests.delete(
                auth=(connections["confluence"]["user"], connections["confluence"]["password"]),
                url=f"https://kb.ertelecom.ru/rest/api/content/{page}",
                headers={"content-type": "application/json"},
                data=json.dumps(DATA),
            )

            if responce.status_code in (200, 204):
                print("- OK")
            else:
                if responce.status_code == 404:
                    # 404 - not exists it's OK
                    print(f"- Page not exists: {responce}")
                else:
                    print(f"- Error responce: {responce}")

        time.sleep(SLEEP_TIME_AFTER_CYCLE)
