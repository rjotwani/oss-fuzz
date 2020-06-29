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

# build project
# e.g.
# ./autogen.sh
# ./configure
# make -j$(nproc) all

# build fuzzers
# e.g.
# $CXX $CXXFLAGS -std=c++11 -Iinclude \
#     /path/to/name_of_fuzzer.cc -o $OUT/name_of_fuzzer \
#     $LIB_FUZZING_ENGINE /path/to/library.a

# cmake -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DPYILMBASE_ENABLE=OFF -DCMAKE_BUILD_TYPE=Release -S $SRC/openexr
# cmake -DBUILD_TESTING=OFF -DPYILMBASE_ENABLE=OFF -DCMAKE_BUILD_TYPE=Release $SRC/openexr
# make -j$(nproc)
# make install

$CXX $CXXFLAGS \
    -I /usr/local/include/OpenEXR \
    $LIB_FUZZING_ENGINE \
    $SRC/openexr_deepscanlines_fuzzer.cc \
    $LDFLAGS \
    -lHalf -lIex -lIexMath -lIlmImf -lIlmImfUtil -lIlmThread -lImath \
    -o $OUT/fuzzer_build

# $CXX $CXXFLAGS \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $SRC/test_fuzzer.cc \
#     -fPIC -shared \
#     $WORK/IlmBase/Half/libHalf.so \
#     $WORK/IlmBase/Iex/libIex.so \
#     $WORK/IlmBase/IexMath/libIexMath.so \
#     $WORK/OpenEXR/IlmImf/libIlmImf.so \
#     $WORK/OpenEXR/IlmImfUtil/libIlmImfUtil.so \
#     $WORK/IlmBase/IlmThread/libIlmThread.so \
#     $WORK/IlmBase/Imath/libImath.so \
#     -o $OUT/fuzzer_build

# CXXFLAGS="${CXXFLAGS} -g"
#
# $CXX $CXXFLAGS \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $SRC/test_fuzzer.cc \
#     -fPIC -shared \
#     -L $WORK/IlmBase/Half -lHalf \
#     -L $WORK/IlmBase/Iex -lIex \
#     -L $WORK/IlmBase/IexMath -lIexMath \
#     -L $WORK/OpenEXR/IlmImf -lIlmImf \
#     -L $WORK/OpenEXR/IlmImfUtil -lIlmImfUtil \
#     -L $WORK/IlmBase/IlmThread -lIlmThread \
#     -L $WORK/IlmBase/Imath -lImath \
#     -o $OUT/fuzzer_build

# $CXX $CXXFLAGS \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $SRC/openexr_deepscanlines_fuzzer.cc \
#     /usr/local/lib/libIlmThread-2_5.a \
#     /usr/local/lib/libIexMath-2_5.a \
#     /usr/local/lib/libHalf-2_5.a \
#     /usr/local/lib/libIex-2_5.a \
#     /usr/local/lib/libImath-2_5.a \
#     /usr/local/lib/libIlmImf-2_5.a \
#     /usr/local/lib/libIlmImfUtil-2_5.a \
#     $WORK/IlmBase/IlmThread/libIlmThread-2_5.a
#     $WORK/IlmBase/IexMath/libIexMath-2_5.a
#     $WORK/IlmBase/Half/libHalf-2_5.a
#     $WORK/IlmBase/Iex/libIex-2_5.a
#     $WORK/IlmBase/Imath/libImath-2_5.a
#     $WORK/OpenEXR/IlmImf/libIlmImf-2_5.a
#     $WORK/OpenEXR/IlmImfUtil/libIlmImfUtil-2_5.a
#     -o $OUT/fuzzer_usr

# $CXX $CXXFLAGS \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $SRC/openexr_deepscanlines_fuzzer.cc \
#     -fPIC -shared \
#     -L $WORK/IlmBase/Half -lHalf \
#     -L $WORK/IlmBase/Iex -lIex \
#     -L $WORK/IlmBase/IexMath -lIexMath \
#     -L $WORK/OpenEXR/IlmImf -lIlmImf \
#     -L $WORK/OpenEXR/IlmImfUtil -lIlmImfUtil \
#     -L $WORK/IlmBase/IlmThread -lIlmThread \
#     -L $WORK/IlmBase/Imath -lImath \
#     -o $OUT/fuzzer_usr

# $CXX $CXXFLAGS \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $SRC/openexr_deepscanlines_fuzzer.cc \
#     -fPIC -shared \
#     -L $WORK/IlmBase/Half -lHalf \
#     -L $WORK/IlmBase/Iex -lIex \
#     -L $WORK/IlmBase/IexMath -lIexMath \
#     -L $WORK/OpenEXR/IlmImf -lIlmImf \
#     -L $WORK/OpenEXR/IlmImfUtil -lIlmImfUtil \
#     -L $WORK/IlmBase/IlmThread -lIlmThread \
#     -L $WORK/IlmBase/Imath -lImath \
#     -o $OUT/fuzzer_build

# $CXX $CXXFLAGS \
#     -I $(find $SRC/ -type d -printf '%p -I ') . \
#     -I $(find $WORK/ -type d -printf '%p -I ') . \
#     $LIB_FUZZING_ENGINE \
#     $SRC/main.cpp \
#     $WORK/bin/exrheader \
#     -o $OUT/fuzzer

# $CXX $CXXFLAGS \
#     -I $SRC/ \
#     -I $WORK/IlmBase/config/ \
#     -I $WORK/OpenEXR/config/ \
#     -I $SRC/openexr/IlmBase/Iex/ \
#     -I $SRC/openexr/IlmBase/Half/ \
#     -I $SRC/openexr/IlmBase/Imath/ \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     -L /usr/local/lib \
#     -lHalf -lIex -lIexMath -lIlmImf -lIlmImfUtil -lIlmThread -lImath \
#     $LIB_FUZZING_ENGINE \
#     $SRC/fuzzer.cpp \
#     /usr/local/bin/exrheader \
#     -o $OUT/fuzzer

# for fuzzer in $(find $SRC/ -name '*_fuzzer.cc'); do
#   fuzzer_basename=$(basename -s .cc $fuzzer)
#   $CXX $CXXFLAGS \
#     -I $SRC/openexr/OpenEXR/IlmImf/ \
#     $LIB_FUZZING_ENGINE \
#     $fuzzer \
#     $WORK/libopenexr.a \
#     -o $OUT/$fuzzer_basename
# done
