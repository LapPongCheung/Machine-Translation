import numpy as np
from data_utils import UNK_TOKEN
from data_utils import load_dict


class TextIterator:
    """Simple Text iterator."""

    def __init__(self, source, source_dict,
                 batch_size=128, maxlen=None,
                 n_words_source=-1,
                 skip_empty=False,
                 shuffle_each_epoch=False,
                 sort_by_length=False,
                 maxibatch_size=20,
                 ):

        if shuffle_each_epoch:
            self.source_orig = source
            #self.source = shuffle.main([self.source_orig], temporary=True)
        else:
            self.source = open(source, 'r', encoding='utf-8')

        self.source_dict = load_dict(source_dict)
        self.batch_size = batch_size
        self.maxlen = maxlen
        self.skip_empty = skip_empty

        self.n_words_source = n_words_source

        if self.n_words_source > 0:
            for key, idx in self.source_dict.items():
                if idx >= self.n_words_source:
                    del self.source_dict[key]

        self.shuffle = shuffle_each_epoch
        self.sort_by_length = sort_by_length

        self.shuffle = shuffle_each_epoch
        self.sort_by_length = sort_by_length

        self.source_buffer = []
        self.k = batch_size * maxibatch_size

        self.end_of_data = False

    def __iter__(self):
        return self

    def __len__(self):
        return sum([1 for _ in self])

    def reset(self):
        if self.shuffle:
        	pass
            #self.source = shuffle.main([self.source_orig], temporary=True)
        else:
            self.source.seek(0)

    def __next__(self):
        if self.end_of_data:
            self.end_of_data = False
            self.reset()
            raise StopIteration

        source = []

        # fill buffer, if it's empty
        if len(self.source_buffer) == 0:
            for k_ in range(self.k):
                ss = self.source.readline()
                if ss == "":
                    break
                self.source_buffer.append(ss.strip().split())

            # sort by buffer
            if self.sort_by_length:
                slen = np.array([len(s) for s in self.source_buffer])
                sidx = slen.argsort()

                _sbuf = [self.source_buffer[i] for i in sidx]

                self.source_buffer = _sbuf
            else:
                self.source_buffer.reverse()

        if len(self.source_buffer) == 0:
            self.end_of_data = False
            self.reset()
            raise StopIteration

        try:
            # actual work here
            while True:
                # read from source file and map to word index
                try:
                    ss = self.source_buffer.pop()
                except IndexError:
                    break
                ss = [self.source_dict[w] if w in self.source_dict
                      else UNK_TOKEN for w in ss]

                if self.maxlen and len(ss) > self.maxlen:
                    continue
                if self.skip_empty and (not ss):
                    continue
                source.append(ss)

                if len(source) >= self.batch_size:
                    break
        except IOError:
            self.end_of_data = True

        # all sentence pairs in maxibatch filtered out because of length
        if len(source) == 0:
            source = self.next()

        return source