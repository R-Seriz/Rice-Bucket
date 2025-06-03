# The Homepage for Ricebucket
A little sideproject to consolidate art projects by friends.
View the site at [http://ricebucket.tech/](http://ricebucket.tech/)

## Setup
1. Run `https://github.com/R-Seriz/Rice-Bucket.git` in the directory to store the project and `cd Rice-Bucket`
2. Create a virtual environment if not done so already with `python3 -m venv venv` and activate with `source venv/bin/activate`
3. Install necessary libraries with `pip install -r reqirements.txt`
4. Create a uploads directory with `mkdir uploads`
5. Create a file titled `.env` and add a private key `SECRET_KEY=[ENTER HERE]`
6. [Optional] Import a `database.db` file with users and posts (must populate uploads directory for posts)

## Running for development
`python3 app.py 0`

## Running for production
`nohup python3 app.py 1 &`

## Adding users
`python3 app.py 2`.
