
#!/usr/bin/env python
# coding: utf-8

import os
import math
import time
import json
import random
import time

from collections import OrderedDict

import numpy as np
import tensorflow as tf

from data_iterator import TextIterator

# import util as util
import data_utils as data_utils
from data_utils import prepare_batch

from seq2seq_model import Seq2SeqModel

# Data loading parameters
tf.app.flags.DEFINE_string('source_vocabulary', 'ipo_data/data.src.tok.bpe.json', 'Path to source vocabulary')
tf.app.flags.DEFINE_string('target_vocabulary', 'ipo_data/data.tgt.tok.bpe.json', 'Path to target vocabulary')
tf.app.flags.DEFINE_string('source_train_data', 'ipo_data/train.src', 'Path to source training data')
tf.app.flags.DEFINE_string('target_train_data', 'ipo_data/train.trg', 'Path to target training data')
tf.app.flags.DEFINE_string('source_valid_data', 'ipo_data/valid.src', 'Path to source validation data')
tf.app.flags.DEFINE_string('target_valid_data', 'ipo_data/valid.trg', 'Path to target validation data')

# Network parameters
tf.app.flags.DEFINE_string('cell_type', 'lstm', 'RNN cell for encoder and decoder, default: lstm')
tf.app.flags.DEFINE_string('attention_type', 'bahdanau', 'Attention mechanism: (bahdanau, luong), default: bahdanau')
tf.app.flags.DEFINE_integer('hidden_units', 512, 'Number of hidden units in each layer')
tf.app.flags.DEFINE_integer('depth', 4, 'Number of layers in each encoder and decoder')
tf.app.flags.DEFINE_integer('embedding_size', 512, 'Embedding dimensions of encoder and decoder inputs')
tf.app.flags.DEFINE_integer('num_encoder_symbols', 30000, 'Source vocabulary size')
tf.app.flags.DEFINE_integer('num_decoder_symbols', 30000, 'Target vocabulary size')
tf.app.flags.DEFINE_boolean('bidirectional', True, 'Use birdictioanl rnn cell')

tf.app.flags.DEFINE_boolean('use_residual', True, 'Use residual connection between layers')
tf.app.flags.DEFINE_boolean('attn_input_feeding', False, 'Use input feeding method in attentional decoder')
tf.app.flags.DEFINE_boolean('use_dropout', True, 'Use dropout in each rnn cell')
tf.app.flags.DEFINE_float('dropout_rate', 0.2, 'Dropout probability for input/output/state units (0.0: no dropout)')

# Training parameters
tf.app.flags.DEFINE_float('learning_rate', 0.0002, 'Learning rate')
tf.app.flags.DEFINE_float('max_gradient_norm', 5.0, 'Clip gradients to this norm')
tf.app.flags.DEFINE_integer('batch_size', 128, 'Batch size')
tf.app.flags.DEFINE_integer('max_epochs', 10, 'Maximum # of training epochs')
tf.app.flags.DEFINE_integer('max_load_batches', 20, 'Maximum # of batches to load at one time')
tf.app.flags.DEFINE_integer('max_seq_length', 50, 'Maximum sequence length')
tf.app.flags.DEFINE_integer('display_freq', 10, 'Display training status every this iteration')
tf.app.flags.DEFINE_integer('save_freq', 10000, 'Save model checkpoint every this iteration')
tf.app.flags.DEFINE_integer('valid_freq', 10000, 'Evaluate model every this iteration: valid_data needed') #1150000
tf.app.flags.DEFINE_string('optimizer', 'adam', 'Optimizer for training: (adadelta, adam, rmsprop)')
tf.app.flags.DEFINE_string('model_dir', 'model/', 'Path to save model checkpoints')
tf.app.flags.DEFINE_string('model_name', 'translate.ckpt', 'File name used for model checkpoints')
tf.app.flags.DEFINE_boolean('shuffle_each_epoch', False, 'Shuffle training dataset for each epoch')
tf.app.flags.DEFINE_boolean('sort_by_length', True, 'Sort pre-fetched minibatches by their target sequence lengths')
tf.app.flags.DEFINE_boolean('use_fp16', False, 'Use half precision float16 instead of float32 as dtype')
tf.app.flags.DEFINE_string('loss_dir', 'loss/', 'Path to save traning and valid loss')

# Decoding parameters
tf.app.flags.DEFINE_integer('beam_width', 3, 'Beam width used in beamsearch')
tf.app.flags.DEFINE_integer('decode_batch_size', 80, 'Batch size used for decoding')
tf.app.flags.DEFINE_integer('max_decode_step', 500, 'Maximum time step limit to ydecode')
tf.app.flags.DEFINE_boolean('write_n_best', False, 'Write n-best list (n=beam_width)')
tf.app.flags.DEFINE_string('model_path', './new_model/translate.ckpt-408000', 'Path to a specific model checkpoint.')

tf.app.flags.DEFINE_string('decode_input', r'preprocess/raw_text.src.bpe', 'Decoding input path')  # here is the input files
tf.app.flags.DEFINE_string('decode_output', 'data/output.de', 'Decoding output path')
tf.app.flags.DEFINE_string('decode_reference', './ipo_data/test.trg', 'Decoding reference path')

# Runtime parameters
tf.app.flags.DEFINE_boolean('allow_soft_placement', True, 'Allow device soft placement')
tf.app.flags.DEFINE_boolean('log_device_placement', False, 'Log placement of ops on devices')

FLAGS = tf.app.flags.FLAGS

def load_config(FLAGS):
    
    # config = json.load(open('%s.json' % FLAGS.model_path, 'rb'))
    # for key, value in FLAGS.__flags.items():
    #     config[key] = value
    config = OrderedDict(sorted(FLAGS.__flags.items()))

    return config


def load_model(session, config):
    
    model = Seq2SeqModel(config, 'decode')
    if tf.train.checkpoint_exists(FLAGS.model_path):
        print('Reloading model parameters..')
        model.restore(session, FLAGS.model_path)
    else:
        raise ValueError(
            'No such file:[{}]'.format(FLAGS.model_path))
    return model


def decode():
    # Load model config
    
    config = load_config(FLAGS)

    # Load source data to decode
    test_set = TextIterator(source=config['decode_input'],
                            batch_size=config['decode_batch_size'],
                            source_dict=config['source_vocabulary'],
                            maxlen=None,
                            n_words_source=config['num_encoder_symbols'])

    # Load inverse dictionary used in decoding
    target_inverse_dict = data_utils.load_reverse_dict(config['target_vocabulary'])

    # Initiate TF session
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=FLAGS.allow_soft_placement, 
        log_device_placement=FLAGS.log_device_placement, gpu_options=tf.GPUOptions(allow_growth=True))) as sess:

        # Reload existing checkpoint
        start = time.time()
        model = load_model(sess, config)
        print (time.time() - start)
        start = time.time()
        try:
            print('Decoding {}..'.format(FLAGS.decode_input))
            if FLAGS.write_n_best:
                fout = [open(("%s_%d" % (FLAGS.decode_output, k)), 'w', encoding='utf-8') \
                        for k in range(FLAGS.beam_width)]
            else:
                fout = [open(FLAGS.decode_output, 'w', encoding='utf-8')]

            
            for idx, source_seq in enumerate(test_set):
                source, source_len = prepare_batch(source_seq)
                predicted_ids = model.predict(sess, encoder_inputs=source, 
                                              encoder_inputs_length=source_len)
                   
                # Write decoding results
                for k, f in reversed(list(enumerate(fout))):
                    for seq in predicted_ids:
                        f.write(str(data_utils.ids2sentence(seq[:,k], target_inverse_dict)) + '\n')
                    if not FLAGS.write_n_best:
                        break
                print('  {}th line decoded'.format(idx * FLAGS.decode_batch_size))
            print (time.time() - start)    
            print('Decoding terminated')
        except IOError:
            pass
        # finally:
        #     [f.close() for f in fout]


def main(_):
    decode()


if __name__ == '__main__':
    tf.app.run()

