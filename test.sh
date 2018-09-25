#!/usr/bin/env bash
set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { echo travis_fold':'end:$1; }
die() { set +v; echo "$*" 1>&2 ; sleep 1; exit 1; }
# Race condition truncates logs on Travis: "sleep" might help.
# https://github.com/travis-ci/travis-ci/issues/6018

start preflight
ping -c1 container-name.docker.localhost > /dev/null \
    || die 'Update /etc/hosts: "echo 127.0.0.1 container-name.docker.localhost >> /etc/hosts"'
docker info | grep 'Operating System' \
    || die 'Make sure Docker is running'
[ -z "`docker ps -qa`" ] \
    || die 'Kill containers before running tests: "docker ps -qa | xargs docker stop | xargs docker rm"'
[ -z "`lsof -t -i tcp:8000`" ] \
    || die 'Free port 80 before running tests: "lsof -t -i tcp:8000 | xargs kill"'
end preflight

start test
# Travis logs were truncated, so always use "die" to avoid race condition.
coverage run manage.py test --verbosity=2 \
  && coverage report --fail-under 80 \
  || die
end test

start doctest
# Add "--append" if you want to have a single coverage.
coverage run -m doctest *.md \
  && coverage report --fail-under 60 \
  || die
end doctest

start docker
docker system df
# TODO: Make assertions about the disk usage we would expect to see.
end docker

start format
flake8 --exclude build . || die "Run 'autopep8 --in-place -r .'"
end format

start isort
isort --recursive . --verbose --check-only || die "See ERRORs: Run 'isort --recursive .'"
end isort

start wheel
python setup.py sdist bdist_wheel
end wheel