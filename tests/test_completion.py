# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean CLI v1.0. Copyright 2021 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from lean.commands import lean
from lean.components.util.click_shell_completion import register_shell_completion


def test_completion_command_prints_powershell_script() -> None:
    result = CliRunner().invoke(lean, ["completion", "--shell", "powershell"])

    assert result.exit_code == 0
    assert "Register-ArgumentCompleter -Native -CommandName lean" in result.output
    assert "_LEAN_COMPLETE" in result.output
    assert "Set-PSReadLineOption -PredictionSource HistoryAndPlugin" in result.output
    assert "Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete" in result.output


def test_click_shell_completion_prints_powershell_source_script() -> None:
    register_shell_completion()

    result = CliRunner().invoke(lean, [], prog_name="lean", env={
        "_LEAN_COMPLETE": "powershell_source"
    })

    assert result.exit_code == 0
    assert "Register-ArgumentCompleter -Native -CommandName lean" in result.output


def test_click_shell_completion_returns_powershell_completions() -> None:
    register_shell_completion()

    result = CliRunner().invoke(lean, [], prog_name="lean", env={
        "_LEAN_COMPLETE": "powershell_complete",
        "COMP_WORDS": "lean cl",
        "COMP_CWORD": "cl"
    })

    assert result.exit_code == 0

    completions = [json.loads(line) for line in result.output.strip().splitlines()]
    completion_values = [item["value"] for item in completions]
    assert "cloud" in completion_values


def test_click_shell_completion_prints_bash_source_script() -> None:
    result = CliRunner().invoke(lean, [], prog_name="lean", env={
        "_LEAN_COMPLETE": "bash_source"
    })

    assert result.exit_code == 0
    assert "complete -o nosort -F" in result.output


def test_completion_on_writes_powershell_profile() -> None:
    with TemporaryDirectory() as directory, patch.object(Path, "home", return_value=Path(directory)):
        result = CliRunner().invoke(lean, ["completion", "on", "--shell", "powershell"])

        assert result.exit_code == 0

        profile_path = Path(directory) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        assert profile_path.exists()

        content = profile_path.read_text(encoding="utf-8")
        assert "# >>> lean completion >>>" in content
        assert "Register-ArgumentCompleter -Native -CommandName lean" in content


def test_completion_off_removes_powershell_profile_block() -> None:
    with TemporaryDirectory() as directory, patch.object(Path, "home", return_value=Path(directory)):
        profile_path = Path(directory) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            "# before\n# >>> lean completion >>>\nlean block\n# <<< lean completion <<<\n# after\n",
            encoding="utf-8"
        )

        result = CliRunner().invoke(lean, ["completion", "off", "--shell", "powershell"])

        assert result.exit_code == 0

        content = profile_path.read_text(encoding="utf-8")
        assert "# >>> lean completion >>>" not in content
        assert "# before" in content
        assert "# after" in content
