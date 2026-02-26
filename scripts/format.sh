#! /bin/sh

set -e

THIS_DIR=$(dirname "$0")
cd $THIS_DIR/..

clang-format -i $(git ls-files '*.cpp.j2' '*.cpp' '*.hpp.j2' '*.hpp', '*.h', '*.h.j2')
gofmt -w $(git ls-files '*.go.j2' '*.go')
