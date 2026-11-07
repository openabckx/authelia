"""Exercise the actual source-built runtime without external services or secrets."""
import argparse
import os
import pathlib
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request


def wait_for_login(url, process):
    deadline = time.monotonic() + 90
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.read().decode()
        except OSError:
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("Runtime did not serve login HTML") from None
            time.sleep(0.5)


def main(background_mode="default"):
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--image")
    target.add_argument("--binary")
    args = parser.parse_args()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="authelia-smoke-") as directory:
        root = pathlib.Path(directory)
        root.chmod(0o755)
        assets = pathlib.Path(__file__).with_name("assets").resolve()
        mounted_assets = root / "assets"
        shutil.copytree(assets, mounted_assets)
        if background_mode == "override":
            shutil.copyfile(assets / "logo.png", mounted_assets / "background.png")
        elif background_mode == "missing":
            (mounted_assets / "background.png").unlink()
        data = root / "data"
        data.mkdir(mode=0o777)
        data.chmod(0o777)  # Disposable test volume, writable by the image's UID 1000.
        config_root = "/smoke" if args.image else directory
        runtime = ["docker", "run", "--rm", args.image, "authelia"] if args.image else [args.binary]
        password = secrets.token_urlsafe(24)
        generated = subprocess.check_output(runtime + ["crypto", "hash", "generate", "argon2", "--password", password], text=True)
        digest = next(line.removeprefix("Digest: ").strip() for line in generated.splitlines()
                      if line.startswith("Digest: "))
        (root / "users.yml").write_text(
            f"users:\n  smoke:\n    disabled: false\n    displayname: Smoke\n    password: '{digest}'\n")
        (root / "configuration.yml").write_text(f"""
server:
  address: 'tcp://{'0.0.0.0:9091' if args.image else f'127.0.0.1:{port}'}'
log:
  level: info
identity_validation:
  reset_password:
    jwt_secret: '{secrets.token_hex(32)}'
authentication_backend:
  file:
    path: '{config_root}/users.yml'
access_control:
  default_policy: two_factor
session:
  secret: '{secrets.token_hex(32)}'
  cookies:
    - domain: example.com
      authelia_url: https://login.example.com
storage:
  encryption_key: '{secrets.token_hex(32)}'
  local:
    path: '{config_root}/data/db.sqlite3'
notifier:
  filesystem:
    filename: '{config_root}/data/notifications.txt'
""")
        branding = {"AUTHELIA_BRANDING_TEXT": "Fork CI & branding",
                    "AUTHELIA_BRANDING_URL": "https://example.com/branding",
                    "AUTHELIA_BRANDING_PRIMARY_COLOR": "#e91e63",
                    "AUTHELIA_BRANDING_BACKGROUND_IMAGE": str(background_mode != "disabled").lower(),
                    "AUTHELIA_BRANDING_BACKGROUND_OPACITY": "0.35",
                    "AUTHELIA_BRANDING_BACKGROUND_BLUR": "4"}
        if args.binary:
            branding["AUTHELIA_SERVER_ASSET_PATH"] = str(mounted_assets)
        name = "authelia-smoke-" + secrets.token_hex(6)
        if args.image:
            uid = subprocess.check_output(["docker", "run", "--rm", args.image, "id", "-u"], text=True).strip()
            assert uid != "0", "image runs as root"
            command = ["docker", "run", "--name", name, "-p", f"127.0.0.1:{port}:9091",
                       "-v", f"{directory}:/smoke:ro", "-v", f"{data}:/smoke/data:rw"]
            if background_mode != "default":
                command.extend(["-v", f"{mounted_assets}:/abckx/assets:ro"])
            for key, value in branding.items():
                command.extend(["-e", f"{key}={value}"])
            command += [args.image, "--config", "/smoke/configuration.yml"]
            version_command = ["docker", "run", "--rm", args.image, "authelia", "--version"]
        else:
            command = [args.binary, "--config", str(root / "configuration.yml")]
            version_command = [args.binary, "--version"]
        version = subprocess.check_output(version_command, text=True).strip()
        assert os.environ.get("EXPECTED_VERSION", "4.39.28-abckx-dev") in version, version
        print(version, flush=True)
        with (root / "runtime.log").open("w+") as log:
            process = subprocess.Popen(command, env={**os.environ, **branding}, stdout=log, stderr=log)
            try:
                try:
                    html = wait_for_login(f"http://127.0.0.1:{port}/", process)
                except RuntimeError:
                    if args.image:
                        diagnostic = subprocess.run(["docker", "logs", name], stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT, text=True, check=False).stdout
                    else:
                        log.seek(0)
                        diagnostic = log.read()
                    print(re.sub(r"[0-9a-f]{64}", "[redacted]", diagnostic), flush=True)
                    raise
                for expected in ('data-brandingtext="Fork CI &amp; branding"',
                                 'data-brandingurl="https://example.com/branding"'):
                    assert expected in html, f"missing {expected}"
                    print(expected, flush=True)
                assert 'src="./static/' in html or 'src="/static/' in html, "missing compiled portal assets"
                print("PASS: source-built runtime serves escaped branding and compiled portal assets", flush=True)
                assets = pathlib.Path(__file__).with_name("assets")
                for asset_name, route in (("logo.png", "/static/media/logo.png"), ("favicon.ico", "/favicon.ico")):
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}{route}", timeout=5) as response:
                        assert response.read() == (assets / asset_name).read_bytes(), f"incorrect overlay: {asset_name}"
                    print(f"PASS: runtime serves official {asset_name} bytes", flush=True)
                if background_mode not in ("missing", "disabled"):
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/static/media/background.png", timeout=5) as response:
                        assert response.read() == (mounted_assets / "background.png").read_bytes()
                    print(f"PASS: {background_mode} background bytes", flush=True)
                subprocess.run(["node", str(pathlib.Path(__file__).with_name("browser-smoke.mjs")),
                                f"http://127.0.0.1:{port}/"], check=True, timeout=90,
                               env={**os.environ, "SMOKE_PASSWORD": password, "BACKGROUND_MODE": background_mode})
            finally:
                if args.image:
                    subprocess.run(["docker", "rm", "--force", name], check=False, stdout=subprocess.DEVNULL)
                process.terminate()
                process.wait(timeout=15)


if __name__ == "__main__":
    for mode in ("default", "override", "missing", "disabled"):
        main(mode)
