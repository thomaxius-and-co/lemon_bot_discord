#!/usr/bin/env bash
set -o errexit

sudo apt install libsystemd-dev

curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
rustup install stable

cd journald-cloudwatch
cargo build --release

