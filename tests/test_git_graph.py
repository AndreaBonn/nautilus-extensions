"""Tests for git-graph pure functions."""

import subprocess

import pytest
from conftest import ROOT, _load_module_functions, requires_git

_ns = _load_module_functions(
    ROOT / "git-graph" / "git_graph.py",
    "git_graph",
    ["hex_to_rgb", "get_git_log"],
)
hex_to_rgb = _ns["hex_to_rgb"]
get_git_log = _ns["get_git_log"]


class TestHexToRgb:
    def test_white(self):
        r, g, b = hex_to_rgb("#FFFFFF")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(1.0)
        assert b == pytest.approx(1.0)

    def test_black(self):
        r, g, b = hex_to_rgb("#000000")
        assert r == pytest.approx(0.0)
        assert g == pytest.approx(0.0)
        assert b == pytest.approx(0.0)

    def test_red(self):
        r, g, b = hex_to_rgb("#FF0000")
        assert r == pytest.approx(1.0)
        assert g == pytest.approx(0.0)
        assert b == pytest.approx(0.0)

    def test_without_hash(self):
        r, g, b = hex_to_rgb("00FF00")
        assert r == pytest.approx(0.0)
        assert g == pytest.approx(1.0)
        assert b == pytest.approx(0.0)

    def test_returns_normalized_values(self):
        r, g, b = hex_to_rgb("#808080")
        assert 0.49 < r < 0.51
        assert 0.49 < g < 0.51
        assert 0.49 < b < 0.51


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def git_repo(tmp_path):
    """Create a minimal git repo with two commits on main."""
    env = {
        "HOME": str(tmp_path),
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": "/usr/bin:/bin",
    }

    def git(*args):
        subprocess.run(
            ["git"] + list(args),
            cwd=str(tmp_path),
            env=env,
            check=True,
            capture_output=True,
        )

    git("init", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test User")

    (tmp_path / "file.txt").write_text("hello")
    git("add", ".")
    git("commit", "-m", "first commit")

    (tmp_path / "file.txt").write_text("world")
    git("add", ".")
    git("commit", "-m", "second commit")

    return tmp_path


@pytest.fixture()
def git_repo_feature_branch(git_repo):
    """Extend git_repo with a feature branch that has one extra commit."""
    env = {
        "HOME": str(git_repo),
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": "/usr/bin:/bin",
    }

    def git(*args):
        subprocess.run(
            ["git"] + list(args),
            cwd=str(git_repo),
            env=env,
            check=True,
            capture_output=True,
        )

    git("checkout", "-b", "feature/test")
    (git_repo / "feature.txt").write_text("feature work")
    git("add", ".")
    git("commit", "-m", "feature commit")

    return git_repo


# ── Tests ────────────────────────────────────────────────────────────────────


@requires_git
class TestGetGitLog:
    def test_returns_list_and_dict_on_repo_with_commits(self, git_repo):
        # Arrange / Act
        commits, branch_color_map = get_git_log(str(git_repo))

        # Assert
        assert commits is not None
        assert branch_color_map is not None
        assert isinstance(commits, list)
        assert isinstance(branch_color_map, dict)

    def test_commit_count_matches_history(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        assert len(commits) == 2

    def test_commit_dict_has_required_keys(self, git_repo):
        commits, _ = get_git_log(str(git_repo))
        required_keys = {
            "hash",
            "full_hash",
            "refs",
            "branches",
            "author",
            "date",
            "message",
            "is_head",
        }

        for commit in commits:
            assert required_keys.issubset(commit.keys()), f"Missing keys in commit: {commit}"

    def test_commit_hash_is_short_eight_chars(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        for commit in commits:
            assert len(commit["hash"]) == 8

    def test_commit_full_hash_is_forty_chars(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        for commit in commits:
            assert len(commit["full_hash"]) == 40

    def test_most_recent_commit_is_head(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        # git log --all returns newest first
        assert commits[0]["is_head"] is True

    def test_older_commits_are_not_head(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        for commit in commits[1:]:
            assert commit["is_head"] is False

    def test_commit_messages_are_preserved(self, git_repo):
        commits, _ = get_git_log(str(git_repo))
        messages = [c["message"] for c in commits]

        assert "second commit" in messages
        assert "first commit" in messages

    def test_message_truncated_at_60_chars(self, git_repo, tmp_path):
        """A commit with a long message should be truncated to 60 chars + ellipsis."""
        long_msg = "A" * 80
        env = {
            "HOME": str(git_repo),
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "t@t.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "t@t.com",
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": "/usr/bin:/bin",
        }
        (git_repo / "extra.txt").write_text("extra")
        subprocess.run(
            ["git", "add", "."], cwd=str(git_repo), env=env, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", long_msg],
            cwd=str(git_repo),
            env=env,
            check=True,
            capture_output=True,
        )

        commits, _ = get_git_log(str(git_repo))
        head_commit = commits[0]

        assert len(head_commit["message"]) <= 61  # 60 chars + "…"
        assert head_commit["message"].endswith("…")

    def test_branch_color_map_contains_main_branch(self, git_repo):
        _, branch_color_map = get_git_log(str(git_repo))

        assert "main" in branch_color_map

    def test_branch_colors_are_hex_strings(self, git_repo):
        _, branch_color_map = get_git_log(str(git_repo))

        for branch, color in branch_color_map.items():
            assert color.startswith("#"), f"Color for {branch!r} is not a hex string: {color!r}"
            assert len(color) == 7

    def test_multiple_branches_appear_in_color_map(self, git_repo_feature_branch):
        _, branch_color_map = get_git_log(str(git_repo_feature_branch))

        assert "main" in branch_color_map
        assert "feature/test" in branch_color_map

    def test_max_commits_limits_results(self, git_repo):
        commits, _ = get_git_log(str(git_repo), max_commits=1)

        assert len(commits) == 1

    def test_empty_repo_returns_none_none(self, tmp_path):
        """A git repo with no commits should return (None, None)."""
        env = {
            "HOME": str(tmp_path),
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": "/usr/bin:/bin",
        }
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(tmp_path),
            env=env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "t@t.com"],
            cwd=str(tmp_path),
            env=env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "T"],
            cwd=str(tmp_path),
            env=env,
            check=True,
            capture_output=True,
        )

        commits, branch_color_map = get_git_log(str(tmp_path))

        assert commits is None
        assert branch_color_map is None

    def test_nonexistent_path_returns_none_none(self, tmp_path):
        """A nonexistent path should return (None, None) without raising."""
        nonexistent = str(tmp_path / "does_not_exist")

        commits, branch_color_map = get_git_log(nonexistent)

        assert commits is None
        assert branch_color_map is None

    def test_non_git_directory_returns_none_none(self, tmp_path):
        """A directory that is not a git repo should return (None, None)."""
        commits, branch_color_map = get_git_log(str(tmp_path))

        assert commits is None
        assert branch_color_map is None

    def test_author_field_is_non_empty_string(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        for commit in commits:
            assert isinstance(commit["author"], str)
            assert commit["author"].strip() != ""

    def test_date_field_is_non_empty_string(self, git_repo):
        commits, _ = get_git_log(str(git_repo))

        for commit in commits:
            assert isinstance(commit["date"], str)
            assert commit["date"].strip() != ""

    def test_remote_refs_excluded_from_branches(self, git_repo):
        """origin/* refs should not appear in the branches list."""
        commits, _ = get_git_log(str(git_repo))

        for commit in commits:
            for branch in commit["branches"]:
                assert not branch.startswith("origin/"), (
                    f"Remote ref {branch!r} leaked into branches list"
                )
