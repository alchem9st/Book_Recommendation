# -*- coding: utf-8 -*-

import os
import sys
import time
import string

from pandas import DataFrame
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
import sklearn.metrics as metrics

# import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pylab

reload(sys)
sys.setdefaultencoding('utf8')

cur_dir = os.getcwd()
reviews_dir = cur_dir + '/selected_books/'
recommendation_file = cur_dir + '/recommendation.txt'
cluster_file = cur_dir + '/words_of_clusters.txt'
features_file = cur_dir + '/features_of_corpus.txt'

table = string.maketrans("", "") # to remove punctuations
book_ids = []
book_names = []
corpus = []


# Build a DataFrame from local files of book reviews
def build_data_frame():
    for filename in os.listdir(reviews_dir):
        if not filename.endswith('.dat'): # invalid data files
            continue

        book_ids.append(filename[:-4])
        file_path = reviews_dir + filename
        sample = ""
        with open(file_path, 'r') as fread:
            # Skip the first line which is the book name
            skip_head = False
            for line in fread:
                if skip_head:
                    words = filter_out_words(line)
                    sample += (' '.join(words) + ' ')
                else:
                    book_names.append(line[:-1])
                    skip_head = True
        corpus.append({'text': sample})

    data_frame = DataFrame(corpus, index=book_ids)
    return data_frame


# Filter out the meaningful words of a string
def filter_out_words(line):
    s = line.lower()
    s = s.translate(table, string.punctuation) # remove punctuation
    # words = []
    # for w in s.split(' '):
    #     if wordnet.synsets(w): # filter out the meaningful words
    #         words.append(w)
    words = s.split(' ')
    return words


# Evaluate the Silhourtte Coefficient error of different number of clusters
def sc_evaluate_clusters(X, max_clusters):
    s = np.zeros(max_clusters + 1)
    s[0] = 0;
    s[1] = 0;
    for k in range(2, max_clusters + 1):
        kmeans = KMeans(init='k-means++', n_clusters=k, n_init=10)
        kmeans.fit_predict(X)
        s[k] = metrics.silhouette_score(X, kmeans.labels_, metric='cosine')

    fig = plt.figure(figsize = (12, 6))
    fig.suptitle('Silhouette Score', fontsize=14, fontweight='bold')
    ax = plt.axes()
    ax.set_xlabel('Number of clusters')
    ax.set_ylabel('Adjusted Rand Index')
    plt.grid(True)
    plt.plot(range(2, len(s)), s[2:])
    pylab.show()


def main():
    start_time = time.time()
    # build the data_frame
    data = build_data_frame()
    print 'DataFrame built at', time.time() - start_time, 's'
    # print data.shape

    # Apply TF-IDF on the corpus
    vectorizer = TfidfVectorizer(stop_words='english', min_df=4, max_df=0.8, max_features=10000) # stop_words='english', max_features=10000
    tfidf = vectorizer.fit_transform(data['text'].values)
    X = tfidf.toarray()
    idf = vectorizer.idf_
    features = vectorizer.get_feature_names()
    print 'TF-IDF vectorized at', time.time() - start_time, 's'

    # Write features of corpus to a local file
    try:
        os.remove(features_file)
    except OSError:
        pass
    with open(features_file, 'w') as fwrite:
        for i in range(len(idf)):
            fwrite.write(features[i] + ', ' + str(idf[i]) + '\n')

    # K Nearest Neighbors
    X = np.array(X)
    nbrs = NearestNeighbors(n_neighbors=6, algorithm='ball_tree').fit(X)
    distances, indices = nbrs.kneighbors(X)
    print 'Get nearest neighbors at', time.time() - start_time, 's'

    # Write recommendation result to a local file
    try:
        os.remove(recommendation_file)
    except OSError:
        pass
    with open(recommendation_file, 'w') as fwrite:
        for nbs in indices:
            # print nbs
            for i in range(len(nbs)):
                fwrite.write(book_names[nbs[i]] + ', ' + book_ids[nbs[i]] + '\n')
            fwrite.write(' ' + '\n')

    # Evaluate number of clusters for Kmeans++
    # sc_evaluate_clusters(X, 5)

    # Clustering with Kmeans++
    k = 95
    kmeans = KMeans(n_clusters=k, init='k-means++', max_iter=200, n_init=1)
    kmeans.fit_predict(X)
    print 'Clustered at', time.time() - start_time, 's'

    # Top words per cluster
    asc_order_centroids = kmeans.cluster_centers_.argsort()
    order_centroids = asc_order_centroids[:,::-1]
    terms = vectorizer.get_feature_names()

    # Write top words of each cluster to a local file
    try:
        os.remove(cluster_file)
    except OSError:
        pass
    with open(cluster_file, 'w') as fwrite:
        for i in range(k):
            fwrite.write("Cluster " + str(i) + '\n')
            for ind in order_centroids[i, :10]:
                fwrite.write(' ' + terms[ind] + '\n')
            fwrite.write('\n')


if __name__ == '__main__':
    main()
