#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import hashlib

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_checklist(cl_file):
    try:
        with open("./" + cl_file, "r") as cf:
            checklist = json.load(cf)
    except FileNotFoundError:
        checklist = {}
    return checklist


def save_checklist(checklist, checklist_file_name):
    with open(checklist_file_name, "w") as wl_file:
        print(f"Saving checklist {wl_file}")
        json.dump(checklist, wl_file, indent=4)
