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

# FROM gcr.io/oss-fuzz-base/base-builder
# RUN apt-get update && apt-get install -y --allow-downgrades --allow-remove-essential --allow-change-held-packages git make pkg-config autoconf autogen libtool zlib1g zlib1g-dev cmake
# RUN git clone --depth 1 https://github.com/AcademySoftwareFoundation/openexr openexr
# COPY build.sh $SRC/
# COPY openexr_deepscanlines_fuzzer.cc $SRC/
# ENV CXXFLAGS="$CXXFLAGS -D_GLIBCXX_DEBUG -I/usr/local/include"
# ENV LDFLAGS="$LDFLAGS -L/usr/local/lib"
# WORKDIR $WORK/

FROM gcr.io/oss-fuzz-base/base-builder
RUN apt-get update
RUN apt-get install -y --allow-downgrades --allow-remove-essential --allow-change-held-packages git make pkg-config autoconf autogen libtool zlib1g zlib1g-dev cmake

# Append -D_GLIBCXX_DEBUG to CXXFLAGS in order to use the libstdc++ debug mode
# and perform range checks.
ENV CXXFLAGS="$CXXFLAGS -D_GLIBCXX_DEBUG"
ENV LDFLAGS="$LDFLAGS -L/usr/local/lib"
RUN bash -c 'sed -i "s|^export CXXFLAGS=.*$|export CXXFLAGS=\"$CXXFLAGS\"|" /root/.bashrc'
RUN bash -c 'sed -i "s|^export LDFLAGS=.*$|export LDFLAGS=\"$LDFLAGS\"|" /root/.bashrc'

COPY build.sh $SRC/
COPY openexr_deepscanlines_fuzzer.cc $SRC/

WORKDIR /fuzzing
RUN git clone https://github.com/openexr/openexr.git

# LINT.IfChange
ENV LD_LIBRARY_PATH="/lib/x86_64-linux-gnu"
WORKDIR /fuzzing/openexr/build
RUN cmake -DBUILD_TESTING=OFF -DPYILMBASE_ENABLE=OFF -DCMAKE_BUILD_TYPE=Release ..
RUN make install
RUN ldconfig
# LINT.ThenChange(//depot/google3/security/fuzzing/autofuzz/rotation/alembic.Dockerfile)

WORKDIR /fuzzing
