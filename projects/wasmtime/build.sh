#!/bin/bash -eu
# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

# Note: This project creates Rust fuzz targets exclusively

build() {
  project=$1
  shift
  fuzzer_prefix=$1
  shift
  PROJECT_DIR=$SRC/$project

  cd $PROJECT_DIR/fuzz && cargo fuzz build -O --debug-assertions "$@"

  FUZZ_TARGET_OUTPUT_DIR=$PROJECT_DIR/target/x86_64-unknown-linux-gnu/release

  for f in $PROJECT_DIR/fuzz/fuzz_targets/*.rs
  do
      src_name=$(basename ${f%.*})
      dst_name=$fuzzer_prefix$src_name
      cp $FUZZ_TARGET_OUTPUT_DIR/$src_name $OUT/$dst_name

      if [[ -d $SRC/wasmtime/wasmtime-libfuzzer-corpus/$dst_name/ ]]; then
          zip -jr \
              $OUT/${dst_name}_seed_corpus.zip \
              $SRC/wasmtime/wasmtime-libfuzzer-corpus/$dst_name/
      fi

      cp $SRC/default.options $OUT/$dst_name.options
  done
}

# Build with all features to enable the binaryen-using fuzz targets, and
# the peepmatic fuzz targets.
build wasmtime "" --all-features

build wasm-tools wasm-tools-
