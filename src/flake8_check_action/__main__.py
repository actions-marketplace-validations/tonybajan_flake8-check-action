import logging
import os
import sys

from flake8.api.legacy import get_style_guide
from flake8.utils import parse_comma_separated_list

from .github import GitHubCheckRun

logger = logging.getLogger(__name__)


def run_check() -> int:
    default_select = 'F'
    github_token = os.getenv('INPUT_REPOTOKEN')
    if not github_token:
        print(
            'No GitHub token found. Set repotoken to ${{ secrets.GITHUB_TOKEN }} in your workflow',
            file=sys.stderr
        )
        sys.exit(1)

    repo = os.environ['GITHUB_REPOSITORY']
    sha = os.environ['GITHUB_SHA']
    workspace = os.environ['GITHUB_WORKSPACE']
    path = os.environ.get('INPUT_PATH') or workspace
    check_run = GitHubCheckRun(github_token, repo, sha, workspace=workspace, path=path)

    select = parse_comma_separated_list(os.getenv('INPUT_SELECT', default_select))
    ignore = parse_comma_separated_list(os.getenv('INPUT_IGNORE', ''))
    line_length = 79
    try:
        line_length = int(os.getenv('INPUT_MAXLINELENGTH') or line_length)
    except ValueError:
        pass

    style_guide = get_style_guide(
        select=select,
        ignore=ignore,
        format='github-check-formatter',
        max_line_length=line_length
    )
    formatter = style_guide._application.formatter
    formatter.check_run = check_run
    style_guide.check_files(paths=[path])

    if not formatter.violations_seen:
        summary = '*No violations*'
        exit_code = 0
    else:
        summary = '*Violations were found*'
        exit_code = 1

    check_run.complete(formatter, summary=summary)
    return exit_code


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    exit_code = run_check()
    sys.exit(exit_code)
