from gensim.models import KeyedVectors

def load_wv(path="wordvectors\word2vec.wordvectors"):
    ## Load word vectors
    wv = KeyedVectors.load(path, mmap='r')
    return wv

def preprocess_input(array, wv):
    ## get only words in vocabulary of models
    return [word for word in array if word in wv.key_to_index]

def get_most_similary(input_array, wv, topn=10):
    ## get n most similar words to input_array
    sims = wv.most_similar(input_array, topn=topn)
    output = {'input':input_array,'similars':{sim[0]:sim[1] for sim in sims}}
    return output
    
# wv = load_wv()
# input_array = ['database']
# processed_input = preprocess_input(input_array, wv)
# sims = get_most_similary(processed_input, wv)

# print(sims)

