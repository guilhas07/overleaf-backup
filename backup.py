import requests
import re
from datetime import datetime
import glob
import json
import pathlib
import math
import time
import zipfile


class Config:
    project_id: str
    email: str
    password: str
    overleaf_dir: str
    url: str = "http://localhost"
    backup_dir: str = "backups"

    def __init__(self):
        pattern = re.compile(
            r"""
        (?P<project_line>^PROJECT_ID="(?P<project>[a-z0-9]*)"$)|                   # your local project id
        (?P<email_line>^EMAIL="(?P<email>[A-Za-z0-9@.]*)"$)|                       # your local overleaf email
        (?P<password_line>^PASSWORD="(?P<password>[A-Za-z0-9@#$%^&+=]*)"$)|        # your local overleaf password
        """,
            re.VERBOSE,
        )
        self.url = "http://localhost"
        with open(".env") as f:
            for line in f:
                line = re.sub(r"\s*", "", line)
                m = pattern.match(line)

                if m is None:
                    continue

                match m.lastgroup:
                    case "project_line":
                        self.project_id = m.group("project")
                    case "email_line":
                        self.email = m.group("email")
                    case "password_line":
                        self.password = m.group("password")
                    case _:
                        pass


def find_most_recent_backup(c: Config, project_name: str) -> str | None:
    max = -1 * math.inf
    recent_file = None
    for file in glob.glob(f"{c.backup_dir}/{project_name}_*.zip"):
        path = pathlib.Path(file)
        mtime = path.stat().st_mtime
        if mtime > max:
            recent_file = str(path)
            max = mtime

    return recent_file


def find_project_name(s: requests.Session, c: Config) -> str | None:
    r = s.get(c.url + "/project")
    projects = re.findall(
        '<meta name="ol-prefetchedProjectsBlob" data-type="json" content="(.*?)"',
        r.text,
    )[0]
    projects = json.loads(projects.replace("&quot;", '"'))
    for project in projects["projects"]:
        if project["id"] == c.project_id:
            return project["name"]
    return None


# NOTE: checking CRCs because comparing two equivelent zips would output different values due to metadata.
def zip_cmp(old_backup: str, new_backup: str):
    with zipfile.ZipFile(old_backup) as old, zipfile.ZipFile(new_backup) as new:
        if len(old.namelist()) != len(new.namelist()):
            return False

        if old.namelist() != new.namelist():
            return False

        for crc1, crc2 in zip(old.infolist(), new.infolist()):
            if crc1.CRC != crc2.CRC:
                return False

    return True


def main() -> int:
    c = Config()

    s = requests.session()
    r = s.get(c.url)

    if r.status_code != 200:
        print("Please make sure overleaf is running locally.")
        return 1

    payload = {
        "email": c.email,
        "password": c.password,
        "_csrf": re.findall('.*_csrf.*value="(.*?)"', r.text)[0],
    }
    r = s.post(c.url + "/login", data=payload)

    project_name = find_project_name(s, c)
    if project_name is None:
        print(f"Error: Couldn't find project with id {c.project_id}")
        return 1

    while True:
        newest_backup = find_most_recent_backup(c, project_name)
        r = s.get(c.url + f"/project/{c.project_id}/download/zip")

        now = datetime.now()
        backup_name = f"{c.backup_dir}/Tese_{now.day}-{now.month}-{now.year}-{now.hour}-{now.minute}.zip"
        with open(
            backup_name,
            "bw",
        ) as f:
            f.write(r.content)

        print(f"{newest_backup=} {backup_name=}")
        if newest_backup and zip_cmp(newest_backup, backup_name):
            print(
                f"Recent backup with name {backup_name} has the same contents of {newest_backup}. Removing {backup_name}..."
            )
            pathlib.Path(backup_name).unlink()
        else:
            print(f"Successfully created backup with name {backup_name}")
        time.sleep(5 * 60)


if __name__ == "__main__":
    SystemExit(main())
