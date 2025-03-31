# Dev Setup for Mirrulations

## Basic set up
- Once you clone mirrulations create virtual environment:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
- Run `dev_setup.py` script:
  - `python3 dev_setup.py`
  - provide API KEY, AWS ACCESS KEY, and AWS SECRET ACCESS KEY

## Optional adjustments
  - **Adjust Timestamp**
    - In the `job_queue.py` located in `mirrulations-core/src/mirrcore` adjust line 89 and 90 to desired time and day(format: `YYYY-MM-DD 00:00:00`)
  - **Adjust Clients**
    - In the `docker-compose.yml` remove clients you don't want to use(using too many clients can cause api key to be timed out)
  - **Adjust Bucket**
    - In the `client.py` file located in `mirrulations-client/src/mirrclient` adjust line 63 to desired bucket(will actually write to that bucket)
    - In the `s3_saver.py` file in the same folder adjust line 22

## Docker set up
  - `docker-compose build` to build (`docker compose build` if command doesn't work)
  - `docker-compose up -d` to launch containers
  - `docker-compose down` to kill containers

## Check Data
  - In your home directory a folder called `data` should be created, navigate to that folder and in the `data` folder within that `data` directory you should see a `raw-data` folder with data in it(`tree` command to see folders and files)
  - You can also use `redis-cli` command to check redis server, use the `keys *` command to view all keys and `get <key>` to retrieve them.
  - If adjusted to desired bucket, view your bucket to see data.