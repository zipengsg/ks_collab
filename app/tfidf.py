print("importing...")
import numpy as np
import scipy.sparse as sparse
import re
from nltk import word_tokenize
import nltk.corpus
import nltk.stem.porter
import collections
from sklearn.mixture import GaussianMixture
import sqlite3
import tqdm
import itertools
print("done importing")

#syns = wordnet.synsets("program")
#syns

class Document:
	def __init__(self, title, content):
		self.title = title;
		self.content = content;
		self.words = None;
		self.unique_words = set(); # this includes synonyms
		self.doc_len = 0;
	
	def tokenize(self, use_syn):
		temp = self.content.lower();
		temp = re.sub("[^A-Za-z\s\-]", "", temp); # remove non-abc
		temp = re.sub("[\-]", " ", temp); # hyphen to space
		tokens = nltk.word_tokenize(temp);
		filtered = (w for w in tokens if not w in nltk.corpus.stopwords.words("english") and not w.startswith("http"));
		
		# don't stem if using synonyms
		if not use_syn:
			stemmed = [nltk.stem.porter.PorterStemmer().stem(w) for w in filtered];
			self.words = stemmed;
		else:
			self.words = list(filtered);
		self.unique_words = set(self.words);

		# calculate and add synonyms
		if use_syn:
			self.words *= 20;
			synonyms_of_words = [];
			for w in self.unique_words:
				syns = list(set(itertools.chain.from_iterable([s.lemma_names() for s in nltk.corpus.wordnet.synsets(w)])));
				synonyms_of_words += syns;
			self.words += synonyms_of_words;
			self.unique_words |= set(synonyms_of_words);

		self.doc_len = len(self.words);

class DocCollection:
	def __init__(self, min_ntopics, max_ntopics, use_syn=False):
		self.min_ntopics = min_ntopics;
		self.max_ntopics = max_ntopics;
		self.use_syn = use_syn;

		self.doc_list = [];
		self.unique_words = set();
		self.word_to_i = {};
		self.i_to_word = [];

		# tfidf
		self.tfidf_matrix = None;

		# classification
		self.docj_to_class = [];
		self.class_to_docs = {};
		self.actual_ntopics = -1;

		self._classifier = None;

	def add_doc(self, d):
		self.doc_list.append(d);
		# don't do stemming if we do synonyms
		d.tokenize(self.use_syn);
		self.unique_words |= d.unique_words;

	def generate_word_index_mapping(self):
		i = 0;
		for w in self.unique_words:
			self.word_to_i[w] = i;
			self.i_to_word.append(w);
			i += 1;

	def _compute_tf(self):
		# add tf scores column by column (doc by doc)
		for j in range(len(self.doc_list)):
			word_count_dict = collections.Counter(self.doc_list[j].words);

			tf_insert_data = np.array([[self.word_to_i[w], word_count_dict[w]] for w in word_count_dict], dtype=np.float32);
			tf_values = tf_insert_data[:, 1];
			rows = tf_insert_data[:, 0];
			cols = np.full(rows.shape, 0, dtype=np.int32);

			nwords = len(self.unique_words);
			temp_column = sparse.coo_matrix((tf_values, (rows, cols)), shape=(nwords, 1), dtype=np.float32);
			self.tfidf_matrix = sparse.hstack((self.tfidf_matrix, temp_column), dtype=np.float32);

	def _apply_idf(self):
		N = len(self.doc_list);
		idf = np.zeros((len(self.unique_words)), dtype=np.float32);

		for i in range(len(self.i_to_word)):
			w = self.i_to_word[i];
			docs_containing = [d for d in self.doc_list if w in d.unique_words];
			idf[i] = np.log(N / len(docs_containing));

		nwords = len(self.unique_words);
		idf_matrix = sparse.coo_matrix((nwords, nwords), dtype=np.float32);
		idf_matrix.setdiag(idf);
		idf_matrix = idf_matrix.tocsc();

		self.tfidf_matrix = idf_matrix @ self.tfidf_matrix.tocsc();

	def compute_tfidf(self):
		self.generate_word_index_mapping();

		ndocs = len(self.doc_list);
		nwords = len(self.unique_words);
		self.tfidf_matrix = sparse.dok_matrix((nwords, 0), dtype=np.float32);

		self._compute_tf();
		self._apply_idf();

	def cluster(self):
		# this can be tweaked
		ndim = int(np.sqrt(float(len(self.unique_words))));

		# normalize
		tfidf_col = self.tfidf_matrix;
		tfidf_col_T = self.tfidf_matrix.tocoo().transpose().tocsc();
		inv_norms = 1.0 / np.sqrt((tfidf_col_T * tfidf_col).diagonal());
		ndocs = len(self.doc_list);
		inv_norm_matrix = sparse.coo_matrix((ndocs, ndocs));
		inv_norm_matrix.setdiag(inv_norms);
		inv_norm_matrix = inv_norm_matrix.tocsc();
		normed_tfidf = tfidf_col @ inv_norm_matrix;

		# dimension reduction
		ndim = min(min(normed_tfidf.shape)-1, ndim);
		[_, s, vt] = sparse.linalg.svds(normed_tfidf, k=ndim, which="LM");
		s = np.diag(s);
		reduced_tfidf = s @ vt;

		# EM clustering
		em_input_data = reduced_tfidf.transpose();
		best_score = np.inf;
		self.actual_ntopics = -1;
		for ntopics in tqdm.tqdm(range(self.min_ntopics, self.max_ntopics+1), desc="Determining ntopics", unit="topics"):
			temp_classifier = GaussianMixture(n_components=ntopics, covariance_type="full");
			temp_classifier.fit(em_input_data);
			score = temp_classifier.bic(em_input_data);
			if score < best_score:
				best_score = score;
				self.actual_ntopics = ntopics;
				self._classifier = temp_classifier;

		# organize docs
		self.docj_to_class = self._classifier.predict(em_input_data);
		for j in range(len(self.docj_to_class)):
			try:
				self.class_to_docs[self.docj_to_class[j]].append(self.doc_list[j]);
			except:
				self.class_to_docs[self.docj_to_class[j]] = [self.doc_list[j]];

def test2_topic_extraction():
	max_num_art = 1000;
	min_ntopics = min(10, max_num_art);
	max_ntopics = min(20, max_num_art);

	e = DocCollection(min_ntopics, max_ntopics, use_syn=True);

	conn = sqlite3.connect("../app.db");
	c = conn.cursor();
	full_texts = c.execute("select id,article_title,article_fulltext from article where id > 1 and source_name != 'Twitter' and article_title is not null;");
	full_texts = list(full_texts);
	conn.close();

	for i in tqdm.tqdm(range(len(full_texts[:min(max_num_art, len(full_texts))])), desc="reading articles", unit="articles"):
		t = full_texts[:min(max_num_art, len(full_texts))][i];
		content = t[2];
		if content == None:
			continue;
		if len(content) == 0:
			continue;
		d = Document(t[1], content);
		e.add_doc(d);

	print("computing tfidf...");
	e.compute_tfidf();

	print("clustering...");
	e.cluster();

	for c in range(e.actual_ntopics):
		print("\n\n\n\n\n=== CLASS %d ===" % c);
		doc_list = e.class_to_docs[c]
		for d in doc_list:
			print("\t* %s" % d.title);
	print("\n\nntopics: %d" % e.actual_ntopics);
	print("\n\nnuniquewords: %d" % len(e.unique_words));

test2_topic_extraction();
