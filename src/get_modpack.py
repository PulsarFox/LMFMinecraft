import json
import os
import sys
from github import Github, Repository, ContentFile
from github import Auth
import requests
import shutil
import logging
from argparse import ArgumentParser, Namespace
import minecraft_launcher_lib

# Osef qu'elle soit exposée, c'est un launcher minecraft frere
CURSEFORGE_API_KEY = "$2a$10$q3yEfWXJ.fIFltHSkjrrYuAi5tbZsSDNKnWbIYBR3kr9sQFO8/z5a"
CURSEFORGE_API_URL = "https://api.curseforge.com"
CURSEFORGE_BACKUP_URL = "https://mediafilez.forgecdn.net"
MODPACK_GITHUB_API_KEY = "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"

MINECRAFT_VERSION = "1.18.2"

REPO_PATH = "PulsarFox/LMFModpack"
CONFIG_FOLDER_NAME = "overrides"
MANIFEST_FILE_NAME = "manifest.json"
TMP_FOLDER_PATH = "../tmp"
headers = {
    'Accept': 'application/json',
    'x-api-key': CURSEFORGE_API_KEY
}

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def download(c: ContentFile, out: str):
    r = requests.get(c.download_url)
    output_path = f'{out}/{c.path}'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        print(f'downloading {c.path} to {out}')
        f.write(r.content)

def download_folder(repo: Repository, folder: str, out: str, recursive: bool):
    contents = repo.get_contents(folder)
    for c in contents:
        if c.download_url is None:
            if recursive:
                download_folder(repo, c.path, out, recursive)
            continue
        download(c, out)

def download_file(repo: Repository, folder: str, out: str):
    c = repo.get_contents(folder)
    download(c, out)

def init_minecraft_forge():
    forge_version = minecraft_launcher_lib.forge.find_forge_version(MINECRAFT_VERSION)
    minecraft_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
    if minecraft_launcher_lib.forge.supports_automatic_install(forge_version):
        minecraft_launcher_lib.forge.install_forge_version(forge_version, minecraft_dir)
    else:
        minecraft_launcher_lib.forge.run_forge_installer(forge_version)

def init_download_modpack_config():
    auth = Auth.Token(MODPACK_GITHUB_API_KEY)
    github = Github(auth=auth)
    repo = github.get_repo(REPO_PATH)
    download_folder(repo, CONFIG_FOLDER_NAME, TMP_FOLDER_PATH, True)
    download_file(repo, MANIFEST_FILE_NAME, TMP_FOLDER_PATH)

def get_all_mod_urls():
    manifest = None
    with open(TMP_FOLDER_PATH + "/" + MANIFEST_FILE_NAME) as f:
        manifest = json.load(f)

    mod_file_urls = []
    for file in manifest["files"]:
        if file["fileID"] != 4406217:
            continue
        logging.info("Downloading mod {mod_id}, file {file_id}...".format(mod_id=file["projectID"], file_id=file["fileID"]))
        r = requests.get("{url}/v1/mods/{mod_id}/files/{file_id}".format(url=CURSEFORGE_API_URL, mod_id=file["projectID"], file_id=file["fileID"]), headers=headers)
        r_obj = r.json()
        print(json.dumps(r_obj, indent=4))
        if r_obj["data"]["downloadUrl"] is None:
            first_file_part = str(file["fileID"])[:4]
            second_file_part = str(file["fileID"])[4:7]
            filename = r_obj["data"]["fileName"]
            fallback_url = "{url}/files/{first_part}/{second_part}/{filename}".format(url=CURSEFORGE_BACKUP_URL, first_part=first_file_part, second_part=second_file_part, filename=filename)
            logging.info("URL NOT FOUND, FALLBACK URL USED: %s", fallback_url)
            mod_file_urls.append(fallback_url)
        else:
            logging.info("Url found: %s", r_obj["data"]["downloadUrl"])
            mod_file_urls.append(r_obj["data"]["downloadUrl"])
    # print(json.dumps(mod_file_urls, indent=4))
            
    


def main():
    # if os.path.exists(TMP_FOLDER_PATH):
    #     shutil.rmtree(TMP_FOLDER_PATH)
    # init_download_modpack_config()
# /files/4406/217/entityculling-forge-1.6.1-mc1.18.2.jar

    # r = requests.get("{url}/v1/mods/{mod_id}/files/{file_id}".format(url=CURSEFORGE_API_URL, mod_id=448233, file_id=4406218), headers=headers)

    # r_obj = r.json()
    # print(json.dumps(r_obj, indent=4))

    get_all_mod_urls()

if __name__ == "__main__":
    main()