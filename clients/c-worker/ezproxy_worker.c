#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <unistd.h>

#ifndef SERVER_URL
#define SERVER_URL "http://127.0.0.1:8000"
#endif

#ifndef WORKER_PASSWORD
#error "Build with -DWORKER_PASSWORD='\"your-password\"'"
#endif

#ifndef WORKER_ID
#define WORKER_ID "ezproxy-c-worker"
#endif

#ifndef BATCH_SIZE
#define BATCH_SIZE 100
#endif

#define MAX_JOBS 1000
#define MAX_RESPONSE (1024 * 1024)
#define REPORT_BUFFER (1024 * 1024)

typedef struct {
    char *data;
    size_t size;
} memory_t;

typedef struct {
    char job_id[64];
    char ip[64];
    char type[16];
    int port;
    int alive;
    double latency_ms;
} job_t;

static size_t write_memory(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t real_size = size * nmemb;
    memory_t *mem = (memory_t *)userp;

    if (mem->size + real_size + 1 > MAX_RESPONSE) {
        return 0;
    }

    char *ptr = realloc(mem->data, mem->size + real_size + 1);
    if (!ptr) {
        return 0;
    }

    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, real_size);
    mem->size += real_size;
    mem->data[mem->size] = 0;
    return real_size;
}

static int http_post_json(const char *path, const char *json, memory_t *response) {
    CURL *curl = curl_easy_init();
    if (!curl) {
        return 0;
    }

    char url[512];
    snprintf(url, sizeof(url), "%s%s", SERVER_URL, path);

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    response->data = malloc(1);
    response->size = 0;
    if (!response->data) {
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        return 0;
    }
    response->data[0] = 0;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_memory);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    return res == CURLE_OK && http_code >= 200 && http_code < 300;
}

static int extract_string_after(const char *start, const char *key, char *out, size_t out_size) {
    const char *p = strstr(start, key);
    if (!p) {
        return 0;
    }
    p = strchr(p, ':');
    if (!p) {
        return 0;
    }
    p = strchr(p, '"');
    if (!p) {
        return 0;
    }
    p++;
    const char *end = strchr(p, '"');
    if (!end) {
        return 0;
    }
    size_t len = (size_t)(end - p);
    if (len >= out_size) {
        len = out_size - 1;
    }
    memcpy(out, p, len);
    out[len] = 0;
    return 1;
}

static int extract_int_after(const char *start, const char *key, int *out) {
    const char *p = strstr(start, key);
    if (!p) {
        return 0;
    }
    p = strchr(p, ':');
    if (!p) {
        return 0;
    }
    *out = atoi(p + 1);
    return 1;
}

static double parse_timeout(const char *json) {
    const char *p = strstr(json, "\"timeout\"");
    if (!p) {
        return 8.0;
    }
    p = strchr(p, ':');
    if (!p) {
        return 8.0;
    }
    double timeout = atof(p + 1);
    return timeout > 0.0 ? timeout : 8.0;
}

static int parse_jobs(const char *json, job_t *jobs, int max_jobs) {
    int count = 0;
    const char *p = json;

    while (count < max_jobs && (p = strstr(p, "\"job_id\"")) != NULL) {
        job_t job;
        memset(&job, 0, sizeof(job));
        if (!extract_string_after(p, "\"job_id\"", job.job_id, sizeof(job.job_id)) ||
            !extract_string_after(p, "\"ip\"", job.ip, sizeof(job.ip)) ||
            !extract_int_after(p, "\"port\"", &job.port) ||
            !extract_string_after(p, "\"type\"", job.type, sizeof(job.type))) {
            p += 8;
            continue;
        }
        jobs[count++] = job;
        p += 8;
    }

    return count;
}

static int test_proxy(job_t *job, double timeout_seconds) {
    CURL *curl = curl_easy_init();
    if (!curl) {
        return 0;
    }

    char proxy_url[160];
    const char *scheme = "http";
    if (strcmp(job->type, "socks4") == 0) {
        scheme = "socks4";
    } else if (strcmp(job->type, "socks5") == 0) {
        scheme = "socks5";
    }
    snprintf(proxy_url, sizeof(proxy_url), "%s://%s:%d", scheme, job->ip, job->port);

    struct timeval start;
    struct timeval end;
    gettimeofday(&start, NULL);

    curl_easy_setopt(curl, CURLOPT_URL, "http://httpbin.org/ip");
    curl_easy_setopt(curl, CURLOPT_PROXY, proxy_url);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, (long)(timeout_seconds * 1000.0));
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, NULL);

    CURLcode res = curl_easy_perform(curl);
    gettimeofday(&end, NULL);

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
    curl_easy_cleanup(curl);

    job->latency_ms = (double)(end.tv_sec - start.tv_sec) * 1000.0;
    job->latency_ms += (double)(end.tv_usec - start.tv_usec) / 1000.0;
    job->alive = res == CURLE_OK && http_code >= 200 && http_code < 400;
    return job->alive;
}

static int claim_jobs(job_t *jobs, int *job_count, double *timeout_seconds) {
    char payload[1024];
    snprintf(
        payload,
        sizeof(payload),
        "{\"worker_id\":\"%s\",\"password\":\"%s\",\"capacity\":%d}",
        WORKER_ID,
        WORKER_PASSWORD,
        BATCH_SIZE
    );

    memory_t response;
    if (!http_post_json("/api/v1/workers/claim", payload, &response)) {
        fprintf(stderr, "claim failed\n");
        return 0;
    }

    *timeout_seconds = parse_timeout(response.data);
    *job_count = parse_jobs(response.data, jobs, MAX_JOBS);
    free(response.data);
    return 1;
}

static int report_jobs(job_t *jobs, int job_count) {
    char *payload = malloc(REPORT_BUFFER);
    if (!payload) {
        return 0;
    }

    int written = snprintf(
        payload,
        REPORT_BUFFER,
        "{\"worker_id\":\"%s\",\"password\":\"%s\",\"results\":[",
        WORKER_ID,
        WORKER_PASSWORD
    );

    for (int i = 0; i < job_count && written < REPORT_BUFFER - 256; i++) {
        written += snprintf(
            payload + written,
            REPORT_BUFFER - (size_t)written,
            "%s{\"job_id\":\"%s\",\"ip\":\"%s\",\"port\":%d,\"type\":\"%s\",\"status\":\"%s\",\"latency_ms\":%.2f}",
            i == 0 ? "" : ",",
            jobs[i].job_id,
            jobs[i].ip,
            jobs[i].port,
            jobs[i].type,
            jobs[i].alive ? "alive" : "dead",
            jobs[i].latency_ms
        );
    }
    snprintf(payload + written, REPORT_BUFFER - (size_t)written, "]}");

    memory_t response;
    int ok = http_post_json("/api/v1/workers/report", payload, &response);
    if (ok) {
        printf("report: %s\n", response.data);
        free(response.data);
    } else {
        fprintf(stderr, "report failed\n");
    }
    free(payload);
    return ok;
}

int main(void) {
    curl_global_init(CURL_GLOBAL_DEFAULT);

    printf("ezProxy C worker started: server=%s worker_id=%s batch=%d\n", SERVER_URL, WORKER_ID, BATCH_SIZE);

    while (1) {
        job_t jobs[MAX_JOBS];
        int job_count = 0;
        double timeout_seconds = 8.0;

        if (!claim_jobs(jobs, &job_count, &timeout_seconds)) {
            sleep(5);
            continue;
        }

        if (job_count == 0) {
            printf("no jobs, waiting...\n");
            sleep(3);
            continue;
        }

        printf("claimed %d jobs, timeout %.1fs\n", job_count, timeout_seconds);
        for (int i = 0; i < job_count; i++) {
            test_proxy(&jobs[i], timeout_seconds);
            printf("%s:%d %s %.0fms\n", jobs[i].ip, jobs[i].port, jobs[i].alive ? "alive" : "dead", jobs[i].latency_ms);
        }

        report_jobs(jobs, job_count);
    }

    curl_global_cleanup();
    return 0;
}
