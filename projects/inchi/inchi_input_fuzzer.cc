// Copyright 2020 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <limits>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <string>

#include "inchi_api.h"

static constexpr size_t kSizeMax = std::numeric_limits<size_t>::max();

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {

  if (size == kSizeMax)
    return 0;

  char szINCHISource[size + 1];
  memcpy(szINCHISource, data, size);
  szINCHISource[size] = '\0'; // InChI string must be null-terminated

  // Buffer lengths taken from InChI API reference, located at
  // https://www.inchi-trust.org/download/104/InChI_API_Reference.pdf, page 24
  char szINCHIKey[29], szXtra1[65], szXtra2[65];
  GetINCHIKeyFromINCHI(szINCHISource, 0, 0, szINCHIKey, szXtra1, szXtra2);

  inchi_InputINCHI inpInChI;
  inpInChI.szInChI = const_cast<char *>(szINCHISource);

  inchi_Output out;
  GetINCHIfromINCHI(&inpInChI, &out);

  inchi_OutputStruct outStruct;
  GetStructFromINCHI(&inpInChI, &outStruct);

  FreeINCHI(&out);
  FreeStructFromINCHI(&outStruct);

  return 0;
}
