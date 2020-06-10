// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "draco/src/draco/compression/decode.h"
#include "draco/src/draco/core/decoder_buffer.h"
#include "draco/src/draco/mesh/mesh.h"
#include "draco/src/draco/point_cloud/point_cloud.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  draco::DecoderBuffer buffer;
  buffer.Init(reinterpret_cast<const char *>(data), size);

  // Decode the input data into a geometry. We do not care about the return
  // value for this test.
  const auto statusor = draco::Decoder::GetEncodedGeometryType(&buffer);
  if (!statusor.ok())
    return 0;
  const draco::EncodedGeometryType geom_type = statusor.value();
  if (geom_type == draco::TRIANGULAR_MESH) {
    draco::Decoder decoder;
    decoder.DecodeMeshFromBuffer(&buffer);
  } else if (geom_type == draco::POINT_CLOUD) {
    // Failed to decode it as mesh, so let's try to decode it as a point
    // cloud.
    draco::Decoder decoder;
    decoder.DecodePointCloudFromBuffer(&buffer);
  }

  return 0;
}