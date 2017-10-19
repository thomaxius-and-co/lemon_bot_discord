#!/usr/bin/env bash
set -o errexit

apt-get install -y curl pkg-config libsystemd-dev libssl-dev

curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
rustup install stable

cd journald-cloudwatch
cargo test --release
cargo build --release

