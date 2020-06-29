#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <vector>

#include <ImfArray.h>
#include <ImfChannelList.h>
#include <ImfDeepFrameBuffer.h>
#include <ImfDeepScanLineInputPart.h>
#include <ImfMultiPartInputFile.h>
#include <ImfNamespace.h>

namespace IMF = OPENEXR_IMF_NAMESPACE;
using namespace IMF;
using IMATH_NAMESPACE::Box2i;
using IMATH_NAMESPACE::V2i;

namespace {

const int width = 90;
const int height = 80;
const int minX = 10;
const int minY = 11;
const Box2i dataWindow(V2i(minX, minY),
                       V2i(minX + width - 1, minY + height - 1));
const Box2i displayWindow(V2i(0, 0), V2i(minX + width * 2, minY + height * 2));

template <typename T>
static void readFile(T *inpart) {
  const Header &fileHeader = inpart->header();

  int channelCount = 0;
  for (ChannelList::ConstIterator i = fileHeader.channels().begin();
       i != fileHeader.channels().end(); ++i, ++channelCount) {
  }

  Array2D<unsigned int> localSampleCount;
  localSampleCount.resizeErase(height, width);
  Array<Array2D<void *> > data(channelCount);

  for (int i = 0; i < channelCount; i++) data[i].resizeErase(height, width);

  DeepFrameBuffer frameBuffer;

  frameBuffer.insertSampleCountSlice(
      Slice(IMF::UINT,
            (char *)(&localSampleCount[0][0] - dataWindow.min.x -
                     dataWindow.min.y * width),
            sizeof(unsigned int) * 1, sizeof(unsigned int) * width));

  std::vector<int> read_channel(channelCount);

  for (int i = 0; i < channelCount; i++) {
    PixelType type = IMF::FLOAT;

    std::stringstream ss;
    ss << i;
    std::string str = ss.str();

    int sampleSize = sizeof(float);

    int pointerSize = sizeof(char *);

    frameBuffer.insert(
        str, DeepSlice(type,
                       (char *)(&data[i][0][0] - dataWindow.min.x -
                                dataWindow.min.y * width),
                       pointerSize * 1, pointerSize * width, sampleSize));
  }

  inpart->setFrameBuffer(frameBuffer);
  inpart->readPixelSampleCounts(dataWindow.min.y, dataWindow.max.y);
  for (int i = 0; i < dataWindow.max.y - dataWindow.min.y + 1; i++) {
    int y = i + dataWindow.min.y;

    for (int j = 0; j < width; j++) {
      for (int k = 0; k < channelCount; k++) {
        data[k][i][j] = new float[localSampleCount[i][j]];
      }
    }
  }
  try {
    inpart->readPixels(dataWindow.min.y, dataWindow.max.y);
  } catch (...) {
  }

  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {
      for (int k = 0; k < channelCount; k++) {
        delete[](float *) data[k][i][j];
      }
    }
  }
}

static void readFileSingle(const char filename[]) {
  DeepScanLineInputFile *file = NULL;
  try {
    file = new DeepScanLineInputFile(filename, 0);
  } catch (...) {
    return;
  }

  try {
    readFile(file);
  } catch (std::exception &e) {
  }

  delete file;
}

static void readFileMulti(const char filename[]) {
  MultiPartInputFile *file = NULL;
  try {
    file = new MultiPartInputFile(filename, 0);
  } catch (...) {
    return;
  }

  for (int p = 0; p < file->parts(); p++) {
    DeepScanLineInputPart *inpart = NULL;
    try {
      inpart = new DeepScanLineInputPart(*file, p);
    } catch (...) {
      continue;
    }
    try {
      readFile(inpart);
    } catch (std::exception &e) {
    }
    delete inpart;
  }

  delete file;
}

}  // namespace

// from cl/164883104
static char *buf_to_file(const char *buf, size_t size) {
  char *name = strdup("/dev/shm/fuzz-XXXXXX");
  int fd = mkstemp(name);
  if (fd < 0) {
    perror("open");
    exit(1);
  }
  size_t pos = 0;
  while (pos < size) {
    int nbytes = write(fd, &buf[pos], size - pos);
    if (nbytes <= 0) {
      perror("write");
      exit(1);
    }
    pos += nbytes;
  }
  if (close(fd) != 0) {
    perror("close");
    exit(1);
  }
  return name;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  char *file = buf_to_file((const char *)data, size);
  readFileSingle(file);
  readFileMulti(file);
  unlink(file);
  free(file);
  return 0;
}
