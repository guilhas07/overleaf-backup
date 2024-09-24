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
    project_ids: set[str] = set()
    email: str = ""
    password: str = ""
    url: str = "http://localhost"
    backup_dir: str = "backups"

    def __init__(self):
        pattern = re.compile(
            r"""
        (^\s*PROJECT_IDS\s*=\s*"(?P<project>[a-z0-9,]*)"\s*(\#.*)?$)|               # your local project id
        (^\s*EMAIL\s*=\s*"(?P<email>[A-Za-z0-9@\.]*)"\s*(\#.*)?$)|                  # your local overleaf email
        (^\s*PASSWORD\s*=\s*"(?P<password>[ A-Za-z0-9@\#\$%\^&\+=\*]*)"\s*(\#.*)?$) # your local overleaf password
        """,
            re.VERBOSE,
        )

        with open(".env") as f:
            for line in f:
                m = pattern.match(line)
                if m is None:
                    continue

                groups = [k for k in m.groupdict() if m.groupdict()[k] is not None]
                assert (
                    len(groups) == 1
                ), f"Error: It shouldn't match 0 or multiple named groups {groups}"

                match groups[0]:
                    case "project":
                        self.project_ids = set(m.group("project").split(","))
                    case "email":
                        self.email = m.group("email")
                    case "password":
                        self.password = m.group("password")
                    case _:
                        pass
        assert (
            self.password != "" and self.email != ""
        ), "Please provide email and password on your .env configuration"

    def __str__(self) -> str:
        return f"""
            Config:
                {self.email=}
                {self.password=}
                {self.project_ids=}
                {self.url=}
            """


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


def find_projects(s: requests.Session, c: Config) -> dict[str, str]:
    r = s.get(c.url + "/project")
    projects_json_obj = re.findall(
        '<meta name="ol-prefetchedProjectsBlob" data-type="json" content="(.*?)"',
        r.text,
    )[0]
    projects_json_obj = json.loads(projects_json_obj.replace("&quot;", '"'))

    projects: dict[str, str] = {}
    for project in projects_json_obj["projects"]:
        in_ids = project["id"] in c.project_ids
        if project["trashed"]:
            if in_ids:
                print(
                    f"[Warning]: Attempting to backup thrashed project with id={project['id']}"
                )
            continue
        if len(c.project_ids) == 0:
            projects[project["id"]] = project["name"]
        elif in_ids:
            projects[project["id"]] = project["name"]
    return projects


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


def backup_project(s: requests.Session, c: Config, id: str, name: str):
    r = s.get(c.url + f"/project/{id}/download/zip")
    if r.status_code != 200:
        print(f"Error: Couldn't find project with {id=}")
        return

    newest_backup = find_most_recent_backup(c, name)

    now = datetime.now()
    backup_name = f"{c.backup_dir}/{name}_{now.day}-{now.month}-{now.year}-{now.hour}-{now.minute}.zip"
    with open(
        backup_name,
        "bw",
    ) as f:
        f.write(r.content)

    if newest_backup and zip_cmp(newest_backup, backup_name):
        print(
            f"Recent backup with name {backup_name} has the same contents of {newest_backup}. Removing {backup_name}..."
        )
        pathlib.Path(backup_name).unlink()
    else:
        print(f"Successfully created backup with name {backup_name}")


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

    if r.status_code != 200:
        print(
            f"Couldn't login with email {c.email} and password: {c.password}. Make sure to configure them correctly."
        )
        return 1

    projects = find_projects(s, c)
    if len(projects) == 0:
        print(
            f"Error: Couldn't find projects{f' with id {str(c.project_ids)}.' if c.project_ids is not None else '.'}"
        )
        return 1

    while True:
        for project_id, project_name in projects.items():
            try:
                backup_project(s, c, project_id, project_name)
            except Exception as e:
                print(e)
        time.sleep(5 * 60)

        # See if more projects were created. This time don't exit
        projects = find_projects(s, c)
        if len(projects) == 0:
            print(
                f"Error: Couldn't find projects{f' with id {str(c.project_ids)}.' if c.project_ids is not None else '.'}"
            )


if __name__ == "__main__":
    SystemExit(main())
