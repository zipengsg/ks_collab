import numpy as np
import re
import nltk

# this stuff should be replaced by nltk things
class Document:
	def __init__(self, name, content):
		self.name = name;
		self.content = content;

		temp = content.lower();
		temp = re.sub("[^a-zA-Z\s]", "", temp);
		self.wl = temp.split(); # word list
		self.wc = {}; # word count

	def count_words(self):
		for w in self.wl:
			if w in self.wc:
				self.wc[w] += 1;
			else:
				self.wc[w] = 1;
		return self.wc;

# all the documents
class Everything:
	def __init__(self):
		self.dl = []; # document list
		self.wc = {}; # word count across all docs
		self.tf = []; # self.tf[1]["the"] means doc1, "the" count
		self.idf = {};
		self.tfidf = [];
	
	def add(self, d):
		self.dl.append(d);

	def compute_tf(self):
		for d in self.dl:
			doc_wc = d.count_words();
			self.tf.append(doc_wc);

			# total word count across all docs (not needed)
			for w in doc_wc:
				if w in self.wc:
					self.wc[w] += doc_wc[w];
				else:
					self.wc[w] = doc_wc[w];
	
	def compute_idf(self):
		N = len(self.dl);
		for w in self.wc:
			docs_containing = [d for d in self.dl if w in d.wc ];
			self.idf[w] = np.log(N / len(docs_containing));

	def compute_tfidf(self):
		self.compute_tf();
		self.compute_idf();
		for i in range(len(self.dl)):
			doc_tfidf = {};
			for w in self.dl[i].wc:
				doc_tfidf[w] = self.tf[i][w] * self.idf[w];
			self.tfidf.append(doc_tfidf);

e = Everything();

doc_names = ["tfidf", "word embedding", "china", "occurence matrix", "Vector space", "DDay"];
for i in range(6):
	f = open("example_documents/%d" % i, "r");
	content = f.read();
	if len(content) == 0:
		continue;
	d = Document(doc_names[i], content);
	e.add(d);

e.compute_tfidf();

# test
for i in range(len(e.dl)):
	doc_tfidf = e.tfidf[i];
	sorted_doc_tfidf = sorted(doc_tfidf.items(), key=lambda x: x[1], reverse=True);
	print("\nDocument: %s" % e.dl[i].name);
	print(sorted_doc_tfidf[:20]);
	print("\n");
