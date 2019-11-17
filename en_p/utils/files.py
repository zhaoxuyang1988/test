# -*- coding:utf-8 -*-
import shutil
import os
import re
import sys
import json
import pymysql
import requests
import tempfile

def get_cur_path():
    '''
    @summary:
    '''
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)

def get_files(dir_name, recursive=False, suffix_names=(".TXT",)):
    '''
    @summary: walk target directory get files with suffix
    '''
    if not os.path.isdir(dir_name):
        return
    for name in os.listdir(dir_name):
        suffix = get_suffix(name)
        full_name = os.path.join(dir_name, name)

        if os.path.isfile(full_name):
            if not suffix_names:
                yield full_name
            elif suffix.upper() in suffix_names:
                yield full_name
        elif os.path.isdir(full_name) and recursive:
            for full_name in get_files(full_name, recursive, suffix_names):
                yield full_name
        else:
            pass

def get_suffix(file_name): 
    '''
    @summary: get suffix name with point (.txt)
    @param f_name: file name
    @return: suffix with point like (.txt)
    '''
    try:
        return os.path.splitext(file_name)[1]
    except IndexError as error:
        print(error)
        return

def get_file_name(f_name):
    '''
    @summary: return file name without suffix
    '''
    try:
        return os.path.splitext(f_name)[0]
    except Exception as error:
        print(error)
        return

def get_create_time(file_name):
    '''
    @summary:
    '''
    #return os.stat(file_name).st_ctime
    #return datetime.fromtimestamp(os.path.getctime(file_name))
    return os.path.getctime(file_name)

def check_path(path):
    '''
    @summary: if not exist path create it
    '''
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path)
    except Exception:
        return False
    return True

def is_crown_dir(dir_name):
    '''
    @summary:
    '''
    if not os.path.isdir(dir_name):
        return False
    for name in os.listdir(dir_name):
        full_name = os.path.join(dir_name, name)
        if os.path.isdir(full_name):
            return False
    return True

def get_crown_dirs(dir_name):
    '''
    @summary:
    '''
    if not os.path.isdir(dir_name):
        return
    for name in os.listdir(dir_name):
        full_name = os.path.join(dir_name, name)
        if os.path.isfile(full_name):
            continue
        elif os.path.isdir(full_name):
            if is_crown_dir(full_name):
                yield full_name
            else:
                for f_name in get_crown_dirs(full_name):
                    yield f_name
    return

def remove_empty_dir(path):
    '''
    @summary: delete empty directory
    '''
    if not os.path.isdir(path):
        return
    for name in os.listdir(path):
        sub_dir = os.path.join(path, name)
        remove_empty_dir(sub_dir)
    if os.listdir(path):
        return
    try:
        os.rmdir(path)
    except IOError as error:
        print("ERROR")
        return

def get_content_list(f_txt):
    '''
    @summary:
    '''
    with open(f_txt, "r", encoding="utf-8") as h_file:
        while True:
            text = h_file.readline()
            if not text:
                break
            yield text.strip()

def get_content(f_txt, encoding=None):
    '''
    @summary:
    '''
    with open(f_txt, "r", encoding=encoding) as h_file:
        return h_file.read()

def save_file(f_txt, text_list):
    '''
    @summary:
    '''
    with open(f_txt, "w") as h_file:
        h_file.writelines(text_list)
            
def save_mess(f_name, mess_str):
    '''
    @summary:
    '''
    with open(f_name, "a", encoding="utf-8") as h_file:
        if isinstance(mess_str, list):
            h_file.write("\n".join(mess_str))
            h_file.write("\n")
        else:
            h_file.write(mess_str)
            h_file.write("\n")

def load_json(f_json):
    '''
    @summary:
    '''
    con_list = get_content_list(f_json)
    json_str = ""
    for str_value in con_list:
        str_value = str_value.replace("\n", "")
        str_value = str_value.replace("\r", "")
        json_str += str_value
    return json.loads(json_str)

def get_video_file(path, video_id):
    '''
    '''
    for f_video in get_files(path, True, (".MP4", ".AVI")):
        if f_video.find(video_id) <= 0:
            continue
        return f_video

def get_upload_dict():
    f_log = "upload.log"
    upload_dict = {}
    if not os.path.isfile(f_log):
        return upload_dict
    for content in get_content_list(f_log):
        value_list = content.strip().split("\t")
        try:
            cat_name, key = value_list
            keys = upload_dict.get(cat_name, [])
            keys.append(key)
            upload_dict[cat_name] = keys
        except Exception as error:
            pass
    return upload_dict

def get_int_list(str_value):
    return re.findall(r'\d+', str_value)

def get_hex_list(str_value):
    return re.findall(r'[0-9|a-f|A-F]+', str_value)

def save_image(u_dict, tar_path):
    os.mkdir(tar_path)
    count = 0
    for key in u_dict:
        count += 1
        if count >= 400:
            break
        f_img = u_dict[key]
        dst = os.path.join(tar_path, os.path.basename(f_img))
        shutil.copy(f_img, dst)

import tarfile
def extract_tar_files(f_tar):
    
    des_dir = os.path.join(os.path.dirname(f_tar), "photos")
    with tarfile.open(f_tar) as fp:
        for name in fp.getnames():
            fp.extract(name, path=des_dir)


def make_targz(output_filename, keys):
    try:
        f_path = os.path.dirname(output_filename)    
        if not os.path.isdir(f_path):
            os.makedirs(f_path)
        with tarfile.open(output_filename, "w:gz") as h_tar:   
            for f_img in keys:
                if not os.path.isfile(f_img):
                    continue
                h_tar.add(f_img, arcname=os.path.basename(f_img))
    except Exception as error:
        return False
    return True

def get_escape_str(ori_str):
    # for pymysql get safe string
    if ori_str is None:
        return pymysql.NULL
    if isinstance(ori_str, str):
        return "'{}'".format(pymysql.escape_string(ori_str))
    return ori_str

def string_to_file(string):
    temp_file = tempfile.NamedTemporaryFile()
    temp_file.write(string)
    temp_file.flush()
    temp_file.seek(0)
    return temp_file

def get_remote_file(url):
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 "\
                "Safari/537.36", 
                'Rerfer': url}

    response = session.get(url, headers=headers)
    if response.status_code != 200:
        return
    return string_to_file(response.content)

