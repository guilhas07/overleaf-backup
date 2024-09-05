## Description

This tool has the purpose to backup your local self hosted overleaf projects.

## Features:

- Backup one specific project [x]

## TODO:

- Commit automatically upstream [ ]
- Support backup of multiple projects [ ]
- Add more configuration possibilities [ ]

## Requirements:

Python >=3.10

## How to use:

1. Configure your local overleaf installation (see https://github.com/overleaf/toolkit/blob/master/doc/quick-start-guide.md) and run it.

2. Clone this project and create a virtual environment (make sure to use a python version >= 3.10):

```bash
git clone https://github.com/guilhas07/overleaf-backup
cd overleaf-backup
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3. Edit [.env](.env) file with your credentials:

```bash
PROJECT_ID="<YOUR_PROJECT_ID>"
EMAIL="<YOUR_LOCAL_OVERLEAF_EMAIL>"
PASSWORD="<YOUR_LOCAL_OVERLEAF_PASSWORD>"
```

You need to discover your `project_id`. To do that go to your projects url e.g., http://localhost/project and
click on the project you which to backup. You should get a url similar to this: http://localhost/project/66d89c5d0aed571c

Copy the text in front of `project/` so you get `66d89c5d0aed571c`.
An example configuration with this `project_id` and some fake credentials would be:

```bash
PROJECT_ID="66d89c5d0aed571c"
EMAIL="dummyemail@gmail.com"
PASSWORD="dummypassword1234"
```

4. Only step missing is to run the [backup.py](backup.py) tool:

```bash
python backup.py
```

> [!WARNING]  
> Make sure to always source the virtual environment with the command:
>
> ```bash
> . .venv/bin/activate
> python backup.py
> ```
>
> before running the tool. We already did this step on 2
