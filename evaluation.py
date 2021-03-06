"""
Purpose:
- Evaluate multimodal embeddings against 6 word similarity tests
"""
from process_eval_set import get_eval_set_list
from argparse import ArgumentParser

import numpy as np
import pandas as pd
from scipy import stats
import os
from pymagnitude import *
import pickle 

def convert_dict_to_txt(path):
    """
    convert the dictionary that contains all predicted embeddings into txt format 
    """
    with open(path+'_all.p', 'rb') as fp:
        word_dict = pickle.load(fp)

    for k, v in word_dict.items():
        v = v.astype('<U100')
        v = np.insert(v, 0, k)
        with open(path+'_all.txt', 'a') as f:
            np.savetxt(f, v.reshape(1, v.shape[0]), fmt='%s')

def compute_pair_sim(word1, word2): 
    """
    compute cosine similarity between two words
    """
    dot_product = np.dot(word1, word2)
    length_word1 = np.linalg.norm(word1)
    length_word2 = np.linalg.norm(word2)
    return dot_product/(length_word1 * length_word2)

def compute_sim(eval_set, word_dict):
    """
    compute similarity for all words in the evaluation set
    @param word_dict: dictionary: keys: words, values: learned embeddings
    @param eval_set_type: type of evaluation set (zs/vis) 
    @return a numpy array of word similarity
    """ 
    word_sim = []
    for i in range(eval_set.shape[0]):
        embedding1 = word_dict[eval_set[i][0]]
        embedding2 = word_dict[eval_set[i][1]]
        pair_sim = compute_pair_sim(embedding1, embedding2)
        word_sim.append(pair_sim)
    word_sim = np.asarray(word_sim)
    
    return word_sim

def compute_sim_magnitude(eval_set, word_dict):
    """
    compute similarity for all words in the evaluation set
    @param word_dict: dictionary: keys: words, values: learned embeddings
    @param eval_set_type: type of evaluation set (zs/vis) 
    @return a numpy array of word similarity
    """ 
    word_sim = []
    for i in range(eval_set.shape[0]):
        embedding1 = word_dict.query(eval_set[i][0])
        embedding2 = word_dict.query(eval_set[i][1])
        pair_sim = compute_pair_sim(embedding1, embedding2)
        word_sim.append(pair_sim)
    word_sim = np.asarray(word_sim)
    
    return word_sim

def evaluate(eval_set_type, word_dict, dict_format):
    """
    Print out evaluation results (correlation, P-value) for all sets, either of type ZS or VIS 
    @param eval_set_type: Type of eval set (ZS/VIS)
    @param word_dict: corresponding dictionary: keys: zs/vis words, values: predicted embeddings 
    """ 
    path = '/data1/minh/evaluation/'
    for i in range(6):
        eval_set = pd.read_csv(path+str(i)+'_'+eval_set_type+'.txt', sep=' ', header=None).as_matrix()
        if dict_format == 'dict':
            model_sim = compute_sim(eval_set, word_dict)
        else:
            model_sim = compute_sim_magnitude(eval_set, word_dict)
        cor, pval = stats.spearmanr(model_sim, eval_set[:,2])
        print("Correlation for {} ({}): {:.3f}, P-value: {:.3f}".format(str(i), eval_set_type, cor, pval))
    print()

def evaluate_all(eval_set_list, word_dict, dict_format):
    """
    Print out evaluation results (correlation, P-value) for all sets (full set)
    @param eval_set_list: List of eval sets (in matrix form)
    @param word_dict: corresponding dictionary: keys: all words, values: predicted embeddings 
    @param dict_format: format of dictionary, 'dict' (normal dictionary) or 'magnitude' (magnitude object)
    """  
    for i in range(len(eval_set_list)):
        if dict_format == 'dict':
            model_sim = compute_sim(eval_set_list[i], word_dict)
        else:
            model_sim = compute_sim_magnitude(eval_set_list[i], word_dict)
        cor, pval = stats.spearmanr(model_sim, eval_set_list[i][:,2])
        print("Correlation for {} (all): {:.3f}, P-value: {:.3f}".format(str(i), cor, pval))
    print() 

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('model', default='normal', type=str, help='[normal, c_linear, c_neural]')
    parser.add_argument('path', type=str, help='path to dictionary that contains predicted embeddings')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    # load evaluation sets
    eval_set_list = get_eval_set_list()

    # open dictionaries that contains predicted embeddings
    with open(args.path+"_vis.p", 'rb') as fp:
        word_dict_vis = pickle.load(fp)
    with open(args.path+"_zs.p", 'rb') as fp:
        word_dict_zs = pickle.load(fp)
    with open(args.path+"_all.p", 'rb') as fp:
        word_dict_all = pickle.load(fp)
    
    #args.m: linear, neural, c_linear, c_neural
    # evaluate a normal model (not concatenated)
    if args.model == 'normal':
        evaluate('vis', word_dict_vis, 'dict')
        evaluate('zs', word_dict_zs, 'dict')
        evaluate_all(eval_set_list, word_dict_all, 'dict')
    # evaluate a concatenated model
    else:    
        word_dict = Magnitude('/data1/embeddings/pymagnitude/word.magnitude')
        
        if args.model == 'c_linear':        
            pred_dict = Magnitude('/data1/embeddings/pymagnitude/predicted_linear.magnitude')
        else:        
            pred_dict = Magnitude('/data1/embeddings/pymagnitude/predicted_neural.magnitude')
        # concatenate a model with glove 
        fused_dict = Magnitude(word_dict, pred_dict)
        print('Dimension of concatenated vectors: {}'.format(fused_dict.dim))

        evaluate('vis', fused_dict, 'magnitude')
        evaluate('zs', fused_dict, 'magnitude')
        evaluate_all(eval_set_list, fused_dict, 'magnitude')

if __name__ == '__main__':
    # convert dictionary to txt file, then convert to Magnitude format in command line 
    # comment out main() if this function is called()
    # args = parse_args()
    # convert_dict_to_txt()
    main()

