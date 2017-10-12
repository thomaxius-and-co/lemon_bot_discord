#!/usr/bin/env bash

curl https://sh.rustup.rs -sSf | sh -s -- -y
export PATH="$HOME/.cargo/bin:$PATH"
rustup install stable
cd journald-cloudwatch
cargo build --release
ls -l target/release
