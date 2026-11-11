#!/usr/bin/env python3
import json
import hashlib
import os
import shutil
import signal
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path


LAUNCHER_DIR = Path(__file__).resolve().parent
CONFIG_PATH = LAUNCHER_DIR / "config" / "device_config.json"


class LauncherError(Exception):
    pass


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NeuroonLauncher:
    def __init__(self):
        self.config = self.load_config()
        self.runtime_dir = self.resolve_managed_path("runtime_dir", "runtime")
        self.releases_dir = self.resolve_managed_path("releases_dir", "runtime/releases")
        self.scripts_dir = self.resolve_managed_path("scripts_dir", "runtime/scripts")
        self.tmp_dir = self.resolve_managed_path("tmp_dir", "runtime/tmp")
        self.state_dir = self.resolve_managed_path("state_dir", "state")
        self.logs_dir = self.resolve_managed_path("logs_dir", "logs")
        self.rollback_dir = self.runtime_dir / "rollback"
        self.log_path = self.logs_dir / "launcher.log"
        self.state_path = self.state_dir / "current_release.json"
        self.device_identity_path = self.state_dir / "device_identity.json"
        self.pid_path = self.state_dir / "current_app.pid"
        self.python_bin = self.config.get("python_bin") or "/usr/bin/python3"
        self.request_timeout = int(self.config.get("request_timeout_seconds", 20))
        self.app_stop_timeout = int(self.config.get("app_stop_timeout_seconds", 10))

    def load_config(self):
        if not CONFIG_PATH.exists():
            raise LauncherError(f"Arquivo de configuracao nao encontrado: {CONFIG_PATH}")

        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        if not config.get("serial_dispositivo"):
            raise LauncherError("Campo obrigatorio ausente: serial_dispositivo")
        if not config.get("api_base_url"):
            raise LauncherError("Campo obrigatorio ausente: api_base_url")

        return config

    def resolve_managed_path(self, key, default_value):
        raw_value = self.config.get("paths", {}).get(key, default_value)
        path = Path(raw_value).expanduser()
        if not path.is_absolute():
            path = LAUNCHER_DIR / path
        return path.resolve()

    def ensure_dirs(self):
        for path in [
            self.runtime_dir,
            self.releases_dir,
            self.scripts_dir,
            self.tmp_dir,
            self.state_dir,
            self.logs_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def log(self, message):
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        line = f"[{now_text()}] {message}"
        print(line, flush=True)
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")

    def release_url(self):
        base_url = self.config["api_base_url"].rstrip("/")
        endpoint = self.config.get("release_endpoint", "get_launcher_release.php").lstrip("/")
        params = urllib.parse.urlencode({"serial_dispositivo": self.config["serial_dispositivo"]})
        return f"{base_url}/{endpoint}?{params}"

    def http_get_json(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "neuroon-launcher/1.0"})
        with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))

    def download_file(self, url, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "neuroon-launcher/1.0"})
        with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
            with destination.open("wb") as output_file:
                shutil.copyfileobj(response, output_file)

    def fetch_remote_release(self):
        url = self.release_url()
        self.log(f"Consultando release: {url}")
        data = self.http_get_json(url)
        if not isinstance(data, dict):
            raise LauncherError("Resposta da API nao e um objeto JSON")
        if data.get("success") is False:
            message = data.get("erro") or data.get("mensagem") or "API retornou success=false"
            raise LauncherError(str(message))
        self.validate_release(data)
        return data

    def validate_release(self, data):
        required_fields = [
            "serial_dispositivo",
            "id_dispositivo",
            "id_local",
            "version",
            "package_url",
            "package_sha256",
            "entrypoint",
        ]
        for field in required_fields:
            if not data.get(field):
                raise LauncherError(f"Campo obrigatorio ausente na release: {field}")

        self.validate_sha256(data["package_sha256"], "package_sha256")

        scripts = data.get("scripts", [])
        if scripts is None:
            data["scripts"] = []
            return
        if not isinstance(scripts, list):
            raise LauncherError("Campo scripts deve ser uma lista")
        for script in scripts:
            if not isinstance(script, dict):
                raise LauncherError("Cada script deve ser um objeto")
            if not script.get("name") or not script.get("url") or not script.get("sha256"):
                raise LauncherError("Cada script precisa de name, url e sha256")
            self.validate_sha256(script["sha256"], f"sha256 do script {script.get('name')}")
            if script.get("run_as", "user") not in ("user", "sudo"):
                raise LauncherError("run_as deve ser user ou sudo")

    def validate_sha256(self, value, field_name):
        value = str(value).strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise LauncherError(f"{field_name} invalido")

    def load_state(self):
        if not self.state_path.exists():
            return None
        with self.state_path.open("r", encoding="utf-8") as state_file:
            return json.load(state_file)

    def save_state(self, release):
        state = {
            "version": release["version"],
            "entrypoint": release["entrypoint"],
            "package_url": release["package_url"],
            "package_sha256": release["package_sha256"],
            "serial_dispositivo": release["serial_dispositivo"],
            "id_dispositivo": int(release["id_dispositivo"]),
            "id_local": int(release["id_local"]),
            "installed_at": now_text(),
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as state_file:
            json.dump(state, state_file, indent=2, ensure_ascii=True)
            state_file.write("\n")

        self.save_device_identity(release)

    def save_device_identity(self, release):
        identity = {
            "serial_dispositivo": release["serial_dispositivo"],
            "id_dispositivo": int(release["id_dispositivo"]),
            "id_local": int(release["id_local"]),
            "updated_at": now_text(),
        }
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.device_identity_path.open("w", encoding="utf-8") as identity_file:
            json.dump(identity, identity_file, indent=2, ensure_ascii=True)
            identity_file.write("\n")

    def is_same_release(self, state, release):
        return bool(
            state
            and state.get("version") == release.get("version")
            and state.get("package_sha256") == release.get("package_sha256")
        )

    def safe_under(self, path, parent):
        try:
            Path(path).resolve().relative_to(Path(parent).resolve())
            return True
        except ValueError:
            return False

    def clean_managed_runtime(self):
        self.log("Limpando pastas gerenciadas do runtime")
        for path in [self.releases_dir, self.scripts_dir, self.tmp_dir]:
            if not self.safe_under(path, self.runtime_dir):
                raise LauncherError(f"Caminho fora do runtime gerenciado: {path}")
            if path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)

    def stop_previous_app(self):
        if not self.pid_path.exists():
            return

        try:
            pid = int(self.pid_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            self.unlink_if_exists(self.pid_path)
            return

        if not self.process_exists(pid):
            self.unlink_if_exists(self.pid_path)
            return

        self.log(f"Parando processo anterior do app: PID {pid}")
        self.terminate_process(pid)
        self.unlink_if_exists(self.pid_path)

    def process_exists(self, pid):
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def terminate_process(self, pid):
        try:
            if hasattr(os, "killpg"):
                os.killpg(pid, signal.SIGTERM)
            else:
                os.kill(pid, signal.SIGTERM)
        except OSError:
            return

        deadline = time.time() + self.app_stop_timeout
        while time.time() < deadline:
            if not self.process_exists(pid):
                return
            time.sleep(0.2)

        try:
            if hasattr(os, "killpg"):
                os.killpg(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def install_release(self, release):
        version = self.safe_name(release["version"], "version")
        target_dir = self.releases_dir / version
        package_path = self.tmp_dir / f"{version}.zip"

        self.stop_previous_app()
        self.create_rollback_backup()

        try:
            self.clean_managed_runtime()
            self.log(f"Baixando pacote da versao {version}")
            self.download_file(release["package_url"], package_path)
            self.verify_sha256(package_path, release["package_sha256"])
            self.extract_zip(package_path, target_dir)

            entrypoint = self.find_entrypoint(target_dir, release["entrypoint"])
            self.log(f"Entrypoint encontrado: {entrypoint}")

            self.download_and_run_scripts(release)
            self.save_state(release)
            self.remove_path(self.rollback_dir)
            self.log(f"Versao {version} instalada com sucesso")
        except Exception:
            self.restore_rollback_backup()
            raise

    def create_rollback_backup(self):
        self.remove_path(self.rollback_dir)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

        for name, path in [("releases", self.releases_dir), ("scripts", self.scripts_dir)]:
            if path.exists():
                destination = self.rollback_dir / name
                self.log(f"Criando backup de rollback: {name}")
                shutil.move(str(path), str(destination))

    def restore_rollback_backup(self):
        if not self.rollback_dir.exists():
            return

        self.log("Restaurando ultima versao funcional apos falha")
        for path in [self.releases_dir, self.scripts_dir]:
            self.remove_path(path)

        for name, path in [("releases", self.releases_dir), ("scripts", self.scripts_dir)]:
            backup_path = self.rollback_dir / name
            if backup_path.exists():
                shutil.move(str(backup_path), str(path))

        self.remove_path(self.rollback_dir)

    def remove_path(self, path):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    def unlink_if_exists(self, path):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def safe_name(self, value, field_name):
        value = str(value).strip()
        if not value or any(char in value for char in "/\\"):
            raise LauncherError(f"{field_name} invalido: {value}")
        return value

    def extract_zip(self, zip_path, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                destination = (target_dir / member.filename).resolve()
                if not self.safe_under(destination, target_dir):
                    raise LauncherError(f"Arquivo do zip tenta sair da pasta alvo: {member.filename}")
            archive.extractall(target_dir)

    def verify_sha256(self, path, expected_sha256):
        expected_sha256 = str(expected_sha256).strip().lower()
        digest = hashlib.sha256()
        with Path(path).open("rb") as input_file:
            for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
                digest.update(chunk)

        actual_sha256 = digest.hexdigest()
        if actual_sha256 != expected_sha256:
            raise LauncherError(
                f"Checksum invalido para {Path(path).name}: esperado {expected_sha256}, recebido {actual_sha256}"
            )

    def find_entrypoint(self, release_dir, entrypoint):
        direct_path = (release_dir / entrypoint).resolve()
        if direct_path.exists() and self.safe_under(direct_path, release_dir):
            return direct_path

        matches = list(release_dir.glob(f"*/{entrypoint}"))
        if len(matches) == 1 and self.safe_under(matches[0], release_dir):
            return matches[0].resolve()

        raise LauncherError(f"Entrypoint nao encontrado: {entrypoint}")

    def download_and_run_scripts(self, release):
        scripts = release.get("scripts") or []
        if not scripts:
            self.log("Nenhum script de instalacao recebido")
            return

        version = self.safe_name(release["version"], "version")
        script_dir = self.scripts_dir / version
        script_dir.mkdir(parents=True, exist_ok=True)

        for index, script in enumerate(scripts, start=1):
            script_name = self.safe_name(script["name"], "script.name")
            script_path = script_dir / script_name
            self.log(f"Baixando script {index}/{len(scripts)}: {script_name}")
            self.download_file(script["url"], script_path)
            self.verify_sha256(script_path, script["sha256"])
            script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            self.run_script(script_path, script.get("run_as", "user"))

    def run_script(self, script_path, run_as):
        if run_as == "sudo":
            command = ["sudo", "bash", str(script_path)]
        else:
            command = ["bash", str(script_path)]

        self.log(f"Executando script ({run_as}): {script_path.name}")
        result = subprocess.run(
            command,
            cwd=str(LAUNCHER_DIR),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.stdout:
            for line in result.stdout.splitlines():
                self.log(f"[script:{script_path.name}] {line}")
        if result.returncode != 0:
            raise LauncherError(f"Script falhou ({script_path.name}) com codigo {result.returncode}")

    def current_entrypoint(self, state):
        if not state:
            return None
        version = self.safe_name(state.get("version", ""), "state.version")
        entrypoint = state.get("entrypoint") or "main.py"
        release_dir = self.releases_dir / version
        return self.find_entrypoint(release_dir, entrypoint)

    def start_current_app(self):
        state = self.load_state()
        entrypoint = self.current_entrypoint(state)
        if not entrypoint:
            raise LauncherError("Nenhuma versao instalada para iniciar")

        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        user_name = env.get("USER") or env.get("LOGNAME") or ""
        if user_name:
            env.setdefault("XAUTHORITY", f"/home/{user_name}/.Xauthority")

        env["NEUROON_SERIAL_DISPOSITIVO"] = str(state.get("serial_dispositivo") or self.config["serial_dispositivo"])
        env["NEUROON_ID_DISPOSITIVO"] = str(state.get("id_dispositivo") or "")
        env["NEUROON_ID_LOCAL"] = str(state.get("id_local") or "")
        env["NEUROON_APP_VERSION"] = str(state.get("version") or "")
        env["NEUROON_API_BASE_URL"] = self.config["api_base_url"].rstrip("/")

        self.log(f"Iniciando app: {entrypoint}")
        process = subprocess.Popen(
            [self.python_bin, str(entrypoint)],
            cwd=str(entrypoint.parent),
            env=env,
            start_new_session=True,
        )
        self.pid_path.write_text(str(process.pid), encoding="utf-8")
        return_code = process.wait()
        self.unlink_if_exists(self.pid_path)
        self.log(f"App finalizou com codigo {return_code}")
        return return_code

    def run(self):
        self.ensure_dirs()
        state = self.load_state()

        try:
            release = self.fetch_remote_release()
            if self.is_same_release(state, release):
                self.log(f"Versao atual ja instalada: {release['version']}")
                self.save_state(release)
            else:
                self.log(f"Nova versao detectada: {release['version']}")
                self.install_release(release)
        except Exception as error:
            self.log(f"Falha ao consultar/instalar release: {error}")
            if not state:
                raise
            self.log(f"Tentando iniciar ultima versao instalada: {state.get('version')}")

        return self.start_current_app()


def main():
    try:
        launcher = NeuroonLauncher()
        sys.exit(launcher.run())
    except Exception as error:
        message = f"[{now_text()}] Erro fatal no launcher: {error}"
        print(message, flush=True)
        try:
            (LAUNCHER_DIR / "logs").mkdir(parents=True, exist_ok=True)
            with (LAUNCHER_DIR / "logs" / "launcher.log").open("a", encoding="utf-8") as log_file:
                log_file.write(message + "\n")
        finally:
            sys.exit(1)


if __name__ == "__main__":
    main()
