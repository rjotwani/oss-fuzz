#include <stddef.h>
#include <stdint.h>

#include "sleuthkit_mem_img.h"
#include "sleuthkit/tsk/tsk_tools_i.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  TSK_IMG_INFO* img;
  TSK_FS_INFO* fs;

  img = mem_open(data, size);
  if (img == nullptr) {
    return 0;
  }

  fs = tsk_fs_open_img(img, 0, TSK_FS_TYPE_FAT_DETECT);
  if (fs == nullptr) {
    goto out;
  }

  tsk_fs_fls(fs,
             TSK_FS_FLS_FULL,
             fs->root_inum,
             TSK_FS_DIR_WALK_FLAG_RECURSE,
             nullptr,
             0);

  fs->close(fs);

out:
  img->close(img);

  return 0;
}
