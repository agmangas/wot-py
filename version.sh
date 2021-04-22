#!/usr/bin/env bash

set -e
set -x

if [ -n "$(git status --porcelain)" ]; then
    echo "Git working directory should be clean"
    exit 1
fi

if [[ !("$1" =~ ^(major|minor|patch)$) ]]; then
    echo "Part should be one of major, minor or patch"
    exit 1
fi

if [[ "develop" != $(git branch --show-current) ]]; then
    echo "Current branch is not develop"
    exit 1
fi

bump2version $1

git checkout master \
&& git merge develop \
&& git checkout develop \
&& git push origin --all \
&& git push origin --tags
