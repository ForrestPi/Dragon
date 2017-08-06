# --------------------------------------------------------
# Dragon
# Copyright(c) 2017 SeetaTech
# Written by Ting Pan
# --------------------------------------------------------

import numpy as np
from multiprocessing import Process
from six.moves import range as xrange

from dragon.config import logger

from .utils import GetProperty

class BlobFetcher(Process):
    def __init__(self, **kwargs):
        super(BlobFetcher, self).__init__()
        self._batch_size = GetProperty(kwargs, 'batch_size', 100)
        self._partition  = GetProperty(kwargs, 'partition', False)
        if self._partition:
            self._batch_size = int(self._batch_size / kwargs['group_size'])
        self.Q_in = self.Q_out = None
        self.daemon = True

        def cleanup():
            logger.info('Terminating BlobFetcher......')
            self.terminate()
            self.join()
        import atexit
        atexit.register(cleanup)

    def im_list_to_blob(self):
        datum = self.Q_in.get()
        im_blob = []
        label_blob = np.zeros((self._batch_size, len(datum[1])), dtype=np.float32) \
                        if len(datum) > 1 else None
        for i in xrange(0, self._batch_size):
            im_blob.append(datum[0])
            if label_blob is not None: label_blob[i, :] = datum[1]
            if i != self._batch_size - 1: datum = self.Q_in.get()
        channel_swap = (0, 3, 1, 2)
        im_blob = np.array(im_blob, dtype=np.float32)
        im_blob = im_blob.transpose(channel_swap)
        return (im_blob, label_blob)

    def run(self):
        while True:
            self.Q_out.put(self.im_list_to_blob())