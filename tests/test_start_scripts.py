import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def create_fake_project(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    project = tmp_path / "project"
    (project / "backend").mkdir(parents=True)
    (project / "frontend" / "node_modules").mkdir(parents=True)
    (project / ".venv").mkdir()

    for script_name in ("start.sh", "start-backend.sh", "start-frontend.sh"):
        script = project / script_name
        script.write_text((PROJECT_ROOT / script_name).read_text())
        script.chmod(0o755)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_executable(bin_dir / "uv", "#!/usr/bin/env bash\nexec sleep 600\n")
    write_executable(
        bin_dir / "npm",
        "#!/usr/bin/env bash\nif [[ \"$1\" == \"run\" ]]; then exec sleep 600; fi\nexit 0\n",
    )
    return project, {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}


def test_start_script_writes_pid_and_log_files_then_stops_services(tmp_path: Path) -> None:
    project, env = create_fake_project(tmp_path)

    started = subprocess.run(
        [str(project / "start.sh")], cwd=project, env=env, text=True, capture_output=True
    )

    assert started.returncode == 0, started.stderr
    backend_pid = int((project / "tmp/backend.pid").read_text())
    frontend_pid = int((project / "tmp/frontend.pid").read_text())
    assert os.getpgid(backend_pid) == backend_pid
    assert os.getpgid(frontend_pid) == frontend_pid
    assert (project / "tmp/backend.log").is_file()
    assert (project / "tmp/frontend.log").is_file()

    stopped = subprocess.run(
        [str(project / "start.sh"), "--stop"],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
    )

    assert stopped.returncode == 0, stopped.stderr
    assert not (project / "tmp/backend.pid").exists()
    assert not (project / "tmp/frontend.pid").exists()


def test_start_script_fails_and_cleans_up_when_backend_exits_immediately(tmp_path: Path) -> None:
    project, env = create_fake_project(tmp_path)
    bin_dir = Path(env["PATH"].split(":", maxsplit=1)[0])
    write_executable(bin_dir / "uv", "#!/usr/bin/env bash\nexit 1\n")

    result = subprocess.run(
        [str(project / "start.sh")], cwd=project, env=env, text=True, capture_output=True
    )

    assert result.returncode == 1
    assert "Backend failed to start" in result.stderr
    assert not (project / "tmp/backend.pid").exists()
    assert not (project / "tmp/frontend.pid").exists()


@pytest.mark.parametrize("script_name", ["start-backend.sh", "start-frontend.sh"])
def test_single_service_scripts_reject_arguments(tmp_path: Path, script_name: str) -> None:
    project, env = create_fake_project(tmp_path)

    result = subprocess.run(
        [str(project / script_name), "--stop"],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "Usage:" in result.stderr
