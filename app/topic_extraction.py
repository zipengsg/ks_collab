print("importing");
import numpy as np
import scipy.sparse as sparse
import re
import nltk
import collections
from sklearn.mixture import GaussianMixture
import sqlite3
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
		filtered = [w for w in tokens if not w in nltk.corpus.stopwords.words("english") and not w.startswith("http")];
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
			doc_total_words = sum([doc_wc[w] for w in doc_wc]);
			for w in doc_wc:
				result[w] = doc_wc[w] / doc_total_words;
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
		ndim = 30;

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

		ndim = min(min(normed_tfidf.shape)-1, ndim);
		[_, s, vt] = sparse.linalg.svds(normed_tfidf, k=ndim, which="LM");
		s = np.diag(s);
		reduced_tfidf = s @ vt;

		# one vector per row
		em_input_data = reduced_tfidf.transpose();
		ntopics = int(ndim / 2);
		self.classifier = GaussianMixture(n_components=ntopics, covariance_type="full");
		self.classifier.fit(em_input_data);

		self.doc_class = self.classifier.predict(em_input_data);

# test code
def test1_topic_extraction():
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

def test2_topic_extraction():
	max_num_art = 1000;

	e = Everything();

	conn = sqlite3.connect("../app.db");
	c = conn.cursor();

	full_texts = c.execute("select article_fulltext,id,article_title from article where id > 1 and source_name != 'Twitter' and article_title is not null;");
	for t in list(full_texts)[:max_num_art]:
		cont = t[0];
		if cont == None:
			continue;
		if len(cont) == 0:
			continue;
		print("processing docid %s..." % t[1]);
		d = Document(t[2], cont);
		e.add(d);
	conn.close();

	print("computing tfidf...");
	e.compute_tfidf();

	print("clustering...");
	e.cluster();

	# test
	grouped_docs = {};
	class_top_words = {};
	class_titles = {};
	max_c = -1;
	for i in range(len(e.dl)):
		c = e.doc_class[i];
		doc_tfidf = e.tfidf_list[i];
		sorted_doc_tfidf = sorted(doc_tfidf.items(), key=lambda x: x[1], reverse=True);
		top_words = [t[0] for t in sorted_doc_tfidf[:2]];
		if c in grouped_docs:
			grouped_docs[c].append(i);
		else:
			grouped_docs[c] = [i];
		if c in class_top_words:
			class_top_words[c] += (top_words);
		else:
			class_top_words[c] = top_words;
		if c in class_titles:
			class_titles[c].append(e.dl[i].name);
		else:
			class_titles[c] = [e.dl[i].name];
		if c > max_c:
			max_c = c;

	for c in range(max_c+1):
		dl = grouped_docs[c];
		print("\n=== CLASS %d ===" % c);
		for i in dl:
			doc_tfidf = e.tfidf_list[i];
			sorted_doc_tfidf = sorted(doc_tfidf.items(), key=lambda x: x[1], reverse=True);
			top_words = [t[0] for t in sorted_doc_tfidf[:8]];
			print("\n\nTop words: %s\n\nContent: %s" % (" ".join(top_words), e.dl[i].content[:280]));
			print("\ncluster: %d" % e.doc_class[i]);
		print("\n");

	for c in range(max_c+1):
		print("\n=== CLASS %d ===" % c);
		for title in class_titles[c]:
			print(" * %s" % title);
		#print(" ".join(list(set(class_top_words[c]))));

test2_topic_extraction();
