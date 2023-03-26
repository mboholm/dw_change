import click
import gensim
from gensim.models.word2vec import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
from pathlib import Path
import pickle
import util    # MB create_logger, load_counts
from semantic_change import angular_distance
import numpy as np
import random

#print("GenSim version:", gensim.__version__) # MB

log = util.create_logger(f"", 'train.log', True) 

class StopTrainingException(Exception):
    pass

class AngularChange(CallbackAny2Vec):
    def __init__(self, stop_threshold, epochs, model_prefix):
        self.prev_wv = None
        self.prev_loss = None
        self.stop_threshold = stop_threshold
        self.max_epochs = epochs
        self.epoch = 0
        self.model_prefix = model_prefix
        with open(f'{self.model_prefix}.log', 'w') as f:
            f.write("alpha\tangular_change\ttrain_loss\n")

    def on_epoch_begin(self, model):  # MB  Note: no arguments
        self.cur_alpha = model.alpha - ((model.alpha - model.min_alpha) * float(self.epoch) / self.max_epochs)
        log.info(f"{self.model_prefix}: Starting epoch {self.epoch+1} of {self.max_epochs}.")
        log.info(f"{self.model_prefix}: Alpha: {self.cur_alpha:.06f}")
        self.prev_wv = model.wv.vectors.copy()

    def on_epoch_end(self, model):    # MB  Note: no arguments
        self.epoch += 1
        change = angular_distance(self.prev_wv, model.wv.vectors).mean()
        loss = model.get_latest_training_loss()
        loss_delta = loss - self.prev_loss if self.epoch > 1 else 0
        log.info(f"{self.model_prefix} epoch {self.epoch:02d}: Average angular change: {change:.06f} (threshold: {self.stop_threshold:0.6f}) | Epoch loss: {loss} | Delta loss: {loss_delta:+f}")
        with open(f'{self.model_prefix}.log', 'a') as f:
            f.write(f"{self.cur_alpha:0.6f}\t{change:0.6f}\t{loss}\n")
        if change < self.stop_threshold:
            log.info(f"{self.model_prefix}: Change threshold reached.")
            raise StopTrainingException
        elif self.epoch == self.max_epochs:
            log.info(f"{self.model_prefix}: Last epoch finished.")
            raise StopTrainingException
        self.prev_loss = loss
        model.running_training_loss = 0.0 # see: https://github.com/RaRe-Technologies/gensim/issues/2735


def corpus_counts(filename): # MB counts the no. of lines (examples) and words in a file (= data, I guess) 
    examples, words = 0, 0
    with open(filename, 'r') as f:
        for line in f.readlines():
            examples += 1
            words += len(line.rstrip('\n').split())
    return examples, words

class EpochSaver(CallbackAny2Vec):  
    def __init__(self, model_prefix):
        self.model_prefix = model_prefix
        self.epoch = 0
    def on_epoch_end(self, model): # MB  Note: no arguments
        self.epoch += 1
        output_path = f"{self.model_prefix}_E{self.epoch:02d}"
        log.info(f"Saving {output_path}")
        model.save(output_path)

# MB
# I guess the CallbackAny2Vec objects work by having
# predefined names of its method defintions
# on_epoch_begin, on_epoch_end
# If these objects are provided to training
# they will be called by e.g. x.on_epoch_begin() 
# https://radimrehurek.com/gensim/models/callbacks.html#gensim.models.callbacks.CallbackAny2Vec


@click.command()
@click.argument('token_counts_file')      # MB   one "w\tc\n" per line
@click.argument('corpus_file')            # MB   That which goes into training
                                          # MB   Why two files? 
                                          #      I guess the corpus files is 
                                          #      some kind of gensim object 
                                          #      gensim.models.word2vec.LineSentence
                                          #      However, it seems to be just a 
                                          #      one-example-per-line text file

# MB
# The vocab for training is built from the token_counts
# The corpus_file goes (directly) into training

# From GENSIM, wpg:
# corpus_file (str, optional) – Path to a corpus file in LineSentence format. 
# You may use this argument instead of sentences to get performance boost. 
# Only one of sentences or corpus_file arguments need to be passed (not both of them).


@click.argument('model_prefix')
@click.option('--init-model', default=None,
        help='Path to model to initalize vectors with.')
@click.option('--min-count', default=100,
        help='Minimum frequency for a word to appear in the vocabulary.')  # MB  High number !?
@click.option('--ns-exponent', default=0.75)  # MB   The exponent used to shape the negative sampling distribution (GENSIM, wpg)
@click.option('--alpha', default=0.025)       # MB   The initial learning rate (GENSIM, wpg)
@click.option('--epochs', default=50)
@click.option("--stop-threshold", type=float, default=1e-4,
        help="Average angular change between epochs below which training will be stopped.")
@click.option('--save-checkpoints/--no-save-checkpoints', default=True)  # MB   Syntax
@click.option('--n-threads', default=4)
def cli(token_counts_file, corpus_file, model_prefix, init_model, min_count,
        ns_exponent, alpha, epochs, stop_threshold, save_checkpoints, n_threads):

    log.info(f"Loading token counts.")
    token_counts = util.load_counts(token_counts_file)
    total_tokens = sum(token_counts.values())
    log.info(f"Unique tokens: {len(token_counts)}, total tokens: {total_tokens}.")

# MB parameter name? `size` vs `vector_size`  
    model = Word2Vec(size=200, window=5, sg=1, negative=5,
            min_count=min_count, sample=1e-5, ns_exponent=ns_exponent,
            alpha=alpha, workers=n_threads)

# MB Gensim 4+ use this:
    #model = Word2Vec(vector_size=200, window=5, sg=1, negative=5,
    #        min_count=min_count, sample=1e-5, ns_exponent=ns_exponent,
    #        alpha=alpha, workers=n_threads)    

    log.info(f"Bulinding vocab with min count {min_count}")
    model.build_vocab_from_freq(token_counts)

    #print("---> FROM PYTHON:", "MIN_COUNT", min_count) #MB
    #print("---> FROM PYTHON:", "LEN VOC"  , len(model.wv)) #MB  

    corpus_examples, corpus_words =  corpus_counts(corpus_file)       
    log.info(f"Corpus sentences: {corpus_examples}, corpus tokens: {corpus_words}.")  

    # MB
    # token_counts vs corpus_counts? Is this not the same number?
    # In training, why do we need no. of corpus eaxamples and no. of words in corpus?

    # https://tedboy.github.io/nlps/generated/generated/gensim.models.Word2Vec.intersect_word2vec_format.html
    # In-vocab words not in init_model are left alone (randomly initialized).
    # Out of vocab words in init_model are ignored.
    # lockf=1.0 means that imported word vectors are trained (=0.0 means frozen)
    if init_model is not None:
        model.intersect_word2vec_format(init_model, binary=False, lockf=1.0)  # mb commented out

        # mb new ideas for gensim 4.0 from: 
        # https://stackoverflow.com/questions/69412142/process-to-intersect-with-pre-trained-word-vectors-with-gensim-4-0-0
        # https://datascience.stackexchange.com/questions/97568/fine-tuning-pre-trained-word2vec-model-with-gensim-4-0
        # https://gist.github.com/kaanakdeniz/6ff7d418333f5aa2fea671b17f75154c

        # MB gensim 4+ use  this:
        #print("---> FROM PYTHON:", "LEN LOCKF", model.wv.vectors_lockf.shape) #MB
        #model.wv.vectors_lockf = np.ones(len(model.wv))   # mb
        #print("---> FROM PYTHON:", "LEN LOCKF POST", model.wv.vectors_lockf.shape) #MB 
        #model.wv.intersect_word2vec_format(init_model, binary=False, lockf=1.0)   # mb https://radimrehurek.com/gensim/models/keyedvectors.html#gensim.models.keyedvectors.KeyedVectors
        #print("---> FROM PYTHON:", "LEN VOC POST", len(model.wv)) #MB

    callbacks = [AngularChange(stop_threshold, epochs, model_prefix)]
    if save_checkpoints:
        callbacks.append(EpochSaver(model_prefix))

    try:
        model.train(corpus_file=corpus_file, epochs=epochs, callbacks=callbacks, compute_loss=True,
                total_examples=corpus_examples, total_words=corpus_words)
    except (StopTrainingException, KeyboardInterrupt):
        pass

    log.info(f"Saving {model_prefix}.")
    model.save(f"{model_prefix}")
    model.wv.save_word2vec_format(f"{model_prefix}.w2v")

if __name__ == '__main__':
    cli()
