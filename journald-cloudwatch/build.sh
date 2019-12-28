#!/usr/bin/env bash
set -o errexit

apt-get -q install -y curl pkg-config libsystemd-dev libssl-dev

curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
rustup install 1.39.0

cd journald-cloudwatch
cargo test --release
cargo build --release

