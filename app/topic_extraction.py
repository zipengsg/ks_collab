print("importing");
import numpy as np
import scipy.sparse as sparse
import re
import nltk
import collections
from sklearn.mixture import GaussianMixture
print("done importing");

# this stuff should be replaced by nltk things
class Document:
	def __init__(self, name, content):
		self.name = name;
		self.content = content;
		self.wl = None; # word list
		self.wc = None; # word count

		self.tokenize();
		self.count_words();

	def tokenize(self):
		temp = self.content.lower();
		temp = re.sub("[^a-z\s]", "", temp); # remove non-abc
		tokens = nltk.word_tokenize(temp);
		self.doc_len = len(tokens);
		filtered = [w for w in tokens if not w in nltk.corpus.stopwords.words("english")];
		stemmed = [nltk.stem.porter.PorterStemmer().stem(w) for w in filtered];
		self.wl = stemmed;

	def count_words(self):
		self.wc = collections.Counter(self.wl);

# all the documents
class Everything:
	def __init__(self):
		# these word dict based things should probably be
		# replaced by sparse matrix

		self.dl = []; # document list
#		self.wc = {}; # word count across all docs
		self.word_set = set(); # all words in all docs
		self.i_w = [];
		self.w_i = {}; # word lookup: word -> matrix i
		self.tf = []; # self.tf[1]["the"] means doc1, "the" count
		self.idf = {};
		self.tfidf_list = []; # embedding property
		self.tdidf_matrix = None; # embedding property

		self.classifier = None;
		self.doc_class = [];

	def add(self, d):
		self.dl.append(d);

	def union_word_set(self):
		if len(self.word_set) == 0:
			for d in self.dl:
				doc_wl = d.wl;
				self.word_set.update(d.wl);

	def _compute_tf(self):
		def normed_tf(doc_wc):
			result = {};
			for w in doc_wc:
				result[w] = np.log(1. + doc_wc[w]);
			return result;

		for d in self.dl:
			doc_wc = d.wc;

			# this can be changed to be more sophisticated
			# norming by doc length for example
			self.tf.append(normed_tf(doc_wc));

			# total word count across all docs (not needed)
#			for w in doc_wc:
#				if w in self.wc:
#					self.wc[w] += doc_wc[w];
#				else:
#					self.wc[w] = doc_wc[w];

	def _compute_idf(self):
		N = len(self.dl);
		for w in self.word_set:
			docs_containing = [d for d in self.dl if w in d.wc];
			self.idf[w] = np.log(N / len(docs_containing));

	def _generate_word_lookup(self):
		if len(self.i_w) == 0:
			i = 0;
			for w in self.word_set:
				self.w_i[w] = i;
				self.i_w.append(w);
				i += 1;
			self.i_w = np.array(self.i_w);

	# should be able to optimize this to not for loop
	# perhaps use matrix operations
	def compute_tfidf(self):
		self.union_word_set();
		self._compute_tf();
		self._compute_idf();
		for i in range(len(self.dl)):
			doc_tfidf = {};
			for w in self.dl[i].wc:
				doc_tfidf[w] = self.tf[i][w] * self.idf[w];
			self.tfidf_list.append(doc_tfidf);

		# generate tfidf sparse matrix
		self._generate_word_lookup();
		data = [];
		row = [];
		col = [];
		# this should somehow be written without for loops
		# probably by using a matrix instead of word dictionary
		# from the get-go
		for j in range(len(self.dl)):
			doc_tfidf = self.tfidf_list[j];
			for w in doc_tfidf:
				i = self.w_i[w];
				row.append(i);
				col.append(j);
				data.append(doc_tfidf[w]);
		ndocs = len(self.dl);
		nwords = len(self.word_set);
		self.tfidf_matrix = sparse.coo_matrix((data, (row, col)), shape=(nwords, ndocs));

	def cluster(self):
		# this will also need some dimension reduction

		# this should later be inferred from data
		ntopics = 2;

		# now the question is: to normalize or not to normalize
		normalize = True;
		if normalize:
			tfidf_col = self.tfidf_matrix.tocsc();
			tfidf_col_T = self.tfidf_matrix.transpose().tocsc();
			inv_norms = 1.0 / np.sqrt((tfidf_col_T * tfidf_col).diagonal());
			N = len(self.dl);
			inv_norm_matrix = sparse.coo_matrix((N, N));
			inv_norm_matrix.setdiag(inv_norms);
			inv_norm_matrix = inv_norm_matrix.tocsc();
			normed_tfidf = tfidf_col * inv_norm_matrix;

		# one vector per row
		em_input_data = normed_tfidf.transpose().toarray();
		self.classifier = GaussianMixture(n_components=ntopics, covariance_type="full");
		self.classifier.fit(em_input_data);

		self.doc_class = self.classifier.predict(em_input_data);

# test code
def test_topic_extraction():
	e = Everything();

	doc_names = ["tfidf", "word embedding", "china", "occurence matrix", "Vector space", "DDay"];
	for i in range(6):
		print("reading doc %d..." % i);
		f = open("example_documents/%d" % i, "r");
		content = f.read();
		if len(content) == 0:
			continue;
		d = Document(doc_names[i], content);
		e.add(d);

	print("computing tfidf...");
	e.compute_tfidf();

	print("clustering...");
	e.cluster();

	# test
	for i in range(len(e.dl)):
		doc_tfidf = e.tfidf_list[i];
		sorted_doc_tfidf = sorted(doc_tfidf.items(), key=lambda x: x[1], reverse=True);
		print("\nDocument: %s, cluster: %d" % (e.dl[i].name, e.doc_class[i]));
		print(sorted_doc_tfidf[:10]);
		print("\n");

test_topic_extraction();
