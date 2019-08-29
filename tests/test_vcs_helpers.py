import pytest
from git import GitCommandError

from semantic_release.errors import GitError
from semantic_release.vcs_helpers import (checkout, commit_new_version, get_commit_log,
                                          get_current_head_hash, get_repository_owner_and_name,
                                          push_new_version, tag_new_version)

from . import mock


@pytest.fixture
def mock_git(mocker):
    return mocker.patch('semantic_release.vcs_helpers.repo.git')


def test_first_commit_is_not_initial_commit():
    assert next(get_commit_log()) != 'Initial commit'


def test_add_and_commit(mock_git):
    commit_new_version('1.0.0')
    mock_git.add.assert_called_once_with('semantic_release/__init__.py')
    mock_git.commit.assert_called_once_with(
        m='1.0.0\n\nAutomatically generated by python-semantic-release',
        author="semantic-release <semantic-release>"
    )


def test_tag_new_version(mock_git):
    tag_new_version('1.0.0')
    mock_git.tag.assert_called_with('-a', 'v1.0.0', m='v1.0.0')


def test_push_new_version(mock_git):
    push_new_version()
    mock_git.push.assert_has_calls([
        mock.call('origin', 'master'),
        mock.call('--tags', 'origin', 'master'),
    ])


def test_push_new_version_with_custom_branch(mock_git):
    push_new_version(branch="release")
    mock_git.push.assert_has_calls([
        mock.call('origin', 'release'),
        mock.call('--tags', 'origin', 'release'),
    ])


@pytest.mark.parametrize("origin_url,expected_result", [
    ("git@github.com:group/project.git", ("group", "project")),
    ("git@gitlab.example.com:group/project.git", ("group", "project")),
    ("git@gitlab.example.com:group/subgroup/project.git", ("group/subgroup", "project")),
    ("https://github.com/group/project.git", ("group", "project")),
    ("https://gitlab.example.com/group/subgroup/project.git", ("group/subgroup", "project")),
])
def test_get_repository_owner_and_name(mocker, origin_url, expected_result):
    class FakeRemote:
        url = origin_url
    mocker.patch('git.repo.base.Repo.remote', return_value=FakeRemote())
    assert get_repository_owner_and_name() == expected_result


def test_get_current_head_hash(mocker):
    mocker.patch('git.objects.commit.Commit.name_rev', 'commit-hash branch-name')
    assert get_current_head_hash() == 'commit-hash'


def test_push_should_not_print_auth_token(mock_git):
    mock_git.configure_mock(**{
        'push.side_effect': GitCommandError('auth--token', 1, b'auth--token', b'auth--token')
    })
    mock.patch('semantic_release.settings.config.ConfigParser.get', 'gitlab')
    with pytest.raises(GitError) as excinfo:
        push_new_version(auth_token='auth--token')
    assert 'auth--token' not in str(excinfo)


def test_checkout_should_checkout_correct_branch(mock_git):
    checkout('a-branch')
    mock_git.checkout.assert_called_once_with('a-branch')
