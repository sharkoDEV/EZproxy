# ezProxy C Worker

This worker does not scrape. It connects to the ezProxy server, claims proxy-check jobs, tests them with libcurl, then reports results.

## Ubuntu Build

```bash
sudo apt update
sudo apt install -y build-essential libcurl4-openssl-dev
gcc -O2 ezproxy_worker.c -o ezproxy-worker -lcurl \
  -DSERVER_URL='"http://85.11.167.156:8000"' \
  -DWORKER_PASSWORD='"change-me"' \
  -DWORKER_ID='"worker-1"' \
  -DBATCH_SIZE=100
```

`WORKER_PASSWORD` must match `config.json -> workers.password` on the server.

## Run

```bash
./ezproxy-worker
```

With screen:

```bash
screen -S ezproxy-worker -dm bash -lc './ezproxy-worker'
```
