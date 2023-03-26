# dw_change

Repository for thesis project on semantic change and political dog whistles

tbc ...

#### Note on gensim verisions (DEVELOPMENT)
In gensim 4 there is some problem with training a model with weigths initialized from an existing model. The initialization of weigths suggested for gensim 3 (https://tedboy.github.io/nlps/generated/generated/gensim.models.Word2Vec.intersect_word2vec_format.html), does not work in gensim 4. Following the workaround here: https://github.com/RaRE-technologies/gensim/issues/3094, the code runs and models are trained, but some of the word vectors *de facto* in both the trained model and the pre-trained model are *not* updated (i.e., all words in the intersection of trained and pre-trained model should be trained, but are not). It seems *as if* there is something wrong with the `vectors_lockf`, as if some word vectors have random 0s, where they should not. 

In gensim 3, vectors in the intersection of models are updated. However, gensim 3 is not easily run with Python 3.10 (among other things, you must change the source code in order to solve a number of import errors). The code in `sgns_gs3` has with the reguirements in `requirements_noble.txt` been successfully run with Python 3.8.5. 
