"""Configures nginx on the portal's Tapis pod: serves the web app, proxies /v3/ to Tapis, and runs the LLM proxy.

LLM proxy (/llm/v1/chat/completions): jobs authenticate with the user's own Tapis access token, which nginx checks
with Tapis before forwarding the request to NRP with the project's NRP key. The key exists only in
/etc/nginx/secrets on the pod, so users and jobs never see it.

Reads TAPIS_JWT and the NRP key (NRP_LLM_KEY or NRP_LLM_API) from the repo's .env. Run it again after every pod
restart: files written with exec_pod_commands live in the container and are lost when the pod restarts.

Each token gets at most 8 concurrent LLM calls (429 beyond that): a parallel run holds up to 4 glm-5 calls
(MODEL_SLOTS) plus the deepseek planner, arbiter and slide-review calls.
"""
import os
import re
import sys
import time

from tapipy.tapis import Tapis


def load_env():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))


load_env()

JWT_TOKEN = os.environ.get("TAPIS_JWT")
if not JWT_TOKEN:
    print("[ERROR] Missing TAPIS_JWT in environment or .env file.")
    sys.exit(1)
NRP_KEY = (os.environ.get("NRP_LLM_KEY") or os.environ.get("NRP_LLM_API") or "").strip()
# The key is written into nginx config syntax; anything but plain token characters could break or inject config
if not re.fullmatch(r"[A-Za-z0-9._~+/=-]{8,}", NRP_KEY):
    print("[ERROR] Missing NRP_LLM_KEY in .env, or it contains characters other than letters, digits and ._~+/=-")
    sys.exit(1)

POD_ID = "smartcurriculumdesigner"
CONF = "/etc/nginx/conf.d/default.conf"
SECRET = "/etc/nginx/secrets/nrp_key.conf"
CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
t = Tapis(base_url="https://icicleai.tapis.io", jwt=JWT_TOKEN)

nginx_conf = """# The caller's Tapis token, from the "Authorization: Bearer <token>" header the OpenAI client sends
map $http_authorization $tapis_jwt {
    "~*^Bearer\\s+(?<tok>\\S+)$" $tok;
    default "";
}
# Limit key: the token's last 64 characters (its signature). nginx caps keys at 255 bytes; a whole-token key
# skipped the limit and wrote every token into the error log (2026-11-12)
map $tapis_jwt $llm_limit_key {
    "~(?<k>.{1,64})$" $k;
    default "";
}
limit_conn_zone $llm_limit_key zone=llm_per_user:10m;

server {
    listen 80;
    listen [::]:80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /v3/ {
        proxy_pass https://icicleai.tapis.io;
        proxy_set_header Host icicleai.tapis.io;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_server_name on;
    }

    # LLM proxy: only chat completions are exposed, and only to callers with a valid Tapis token
    location = /llm/v1/chat/completions {
        auth_request /_tapis_auth;
        limit_conn llm_per_user 8;
        limit_conn_status 429;
        client_max_body_size 20m;            # slide reviews send screenshots
        include %(secret)s;                  # set $nrp_key "...";
        proxy_set_header Authorization "Bearer $nrp_key";
        proxy_set_header Host ellm.nrp-nautilus.io;
        # IPv4 only: the pod has no IPv6 route, and NRP's AAAA address failed the first connect (502s on 2026-11-12).
        # A variable in proxy_pass makes nginx resolve through this resolver rather than once at startup
        resolver %(dns)s ipv6=off valid=300s;
        resolver_timeout 5s;
        set $nrp_upstream ellm.nrp-nautilus.io;
        proxy_pass https://$nrp_upstream/v1/chat/completions;
        proxy_ssl_server_name on;
        proxy_ssl_verify on;                 # the key only goes to the real NRP
        proxy_ssl_trusted_certificate %(ca)s;
        proxy_ssl_verify_depth 4;
        proxy_http_version 1.1;
        proxy_buffering off;                 # replies are streamed
        proxy_read_timeout 900s;             # long thinking calls
        proxy_send_timeout 900s;
    }

    # Tapis answers 200 for a valid token and 401 otherwise (checked 2026-11-11; /v3/oauth2/userinfo answers 400)
    location = /_tapis_auth {
        internal;
        client_max_body_size 20m;            # else the subrequest applies the 1 MB default and every screenshot review 500s
        proxy_pass https://icicleai.tapis.io/v3/jobs/list?limit=1&select=uuid;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header Authorization "";
        proxy_set_header X-Tapis-Token $tapis_jwt;
        proxy_set_header Host icicleai.tapis.io;
        proxy_ssl_server_name on;
        proxy_ssl_verify on;
        proxy_ssl_trusted_certificate %(ca)s;
        proxy_ssl_verify_depth 4;
    }
}
"""


def exec_on_pod(script: str):
    """One shell script on the pod. The Pods API sometimes answers a command with a 500 (it did on 2026-11-11, and
    the same command succeeded when rerun); every step here is safe to repeat, so retry a few times."""
    for attempt in range(1, 4):
        try:
            return t.pods.exec_pod_commands(pod_id=POD_ID, commands=["sh", "-c", script]).execution_results[0]
        except Exception as err:
            if attempt == 3:
                raise
            print(f"[WARN] Pods API error ({type(err).__name__}); retrying ({attempt}/2)...")
            time.sleep(5 * attempt)


def run(script: str, secret: bool = False) -> str:
    """Runs a shell script on the pod; returns stdout or exits with stderr. The pod echoes the command in its reply,
    so for a command holding the key nothing from the reply is printed."""
    out = exec_on_pod(script)
    if out.exit_code != 0:
        print("[ERROR] Pod command failed" + ("" if secret else f": {out.stderr or out.stdout}"))
        sys.exit(1)
    return "" if secret else out.stdout


run(f"test -f {CA_BUNDLE}")
dns = run("awk '/^nameserver/{print $2; exit}' /etc/resolv.conf").strip()
if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", dns):  # it goes into the config, so only a plain IPv4 address
    print(f"[ERROR] Expected an IPv4 nameserver in the pod's /etc/resolv.conf, got {dns!r}")
    sys.exit(1)
nginx_conf = nginx_conf % {"secret": SECRET, "ca": CA_BUNDLE, "dns": dns}
run(f"cp {CONF} {CONF}.bak")
run(f"mkdir -p /etc/nginx/secrets && chmod 700 /etc/nginx/secrets && umask 077 && "
    f"printf 'set $nrp_key \"%s\";\\n' '{NRP_KEY}' > {SECRET}", secret=True)
run(f"cat << 'EOF' > {CONF}\n{nginx_conf}\nEOF")
check = exec_on_pod("nginx -t 2>&1")
if check.exit_code != 0:
    run(f"mv {CONF}.bak {CONF}")
    print(f"[ERROR] nginx rejected the new config; the previous one was restored:\n{check.stdout}{check.stderr}")
    sys.exit(1)
run("nginx -s reload")
print(f"[SUCCESS] Nginx configured and reloaded on '{POD_ID}' pod (web app, /v3/ proxy, LLM proxy).")
