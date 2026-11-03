#!/usr/bin/env bash
# Source this file to restore the current student's GitHub session.
_devops_github_session() {
  if ! command -v gh >/dev/null 2>&1; then
    echo 'Missing gh. Ask the host administrator to install the gh package.' >&2
    return 1
  fi
  if [[ -z "$SID" ]]; then
    read -r -p '本人数字学号: ' SID || return 1
  fi
  if [[ ! "$SID" =~ ^[0-9]{6,16}$ ]]; then
    echo 'SID must be the current student ID (6-16 digits).' >&2
    return 1
  fi
  if [[ -n "${GH_TOKEN:-}" || -n "${GITHUB_TOKEN:-}" ]]; then
    echo 'This shell has GH_TOKEN/GITHUB_TOKEN set. Unset them before using the student login directory.' >&2
    return 1
  fi
  export GH_CONFIG_DIR="$HOME/devops-auth/$SID/github"
  mkdir -p "$GH_CONFIG_DIR" || return 1
  chmod 700 "$HOME/devops-auth/$SID" "$GH_CONFIG_DIR" || return 1
  if ! gh auth status --hostname github.com >/dev/null 2>&1; then
    echo '浏览器登录本人 GitHub；如询问是否配置全局 Git 认证，请选择 No。仓库稍后配置局部认证。'
    gh auth login --hostname github.com --git-protocol https --web --scopes workflow || return 1
  fi
  gh api user --jq '"GitHub account: " + .login' || return 1
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    git config --local --replace-all credential.https://github.com.helper '' || return 1
    git config --local --add credential.https://github.com.helper '!gh auth git-credential' || return 1
  fi
}
_devops_github_session
