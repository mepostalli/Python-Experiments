import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from tkinter import *
import tkinter as tk
from tkinter import filedialog as fd
import tkinter.scrolledtext as tkst
import os
import shelve
import re
from django.utils.encoding import smart_str
import urllib.request as urllib2
from bs4 import BeautifulSoup
from urllib.parse import urljoin


ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])
pagelist=['URL']
folder_name = os.path.join(os.getcwd())
dbtables = {'urllist': os.path.join(folder_name, 'urllist2.db'),
            'wordlocation': os.path.join(folder_name, 'wordlocation2.db'),
            'link': os.path.join(folder_name, 'link2.db'),
            'linkwords': os.path.join(folder_name, 'linkwords2.db'),
            'pagerank': os.path.join(folder_name, 'pagerank3.db')}

class crawler:
    
    def __init__(self, dbtables):
        ''' dbtables bir sozluk olmali:
        
            'urllist': 'urllist.db',
            'wordlocation':'wordlocation.db',
            'link':'link.db',
            'linkwords':'linkwords.db'}
        '''
        self.dbtables = dbtables
    
    def gettextonly(self, soup):
        v = soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext + '\n'
            return resulttext
        else:
            return v.strip()


    def separatewords(self, text):
        splitter = re.compile('\\W+')
        return [s.lower() for s in splitter.split(text) if s != '']

    def createindextables(self):
        # {url:outgoing_link_count}
        self.urllist = shelve.open(self.dbtables['urllist'], writeback=True, flag='c')

        #{word:{url:[loc1, loc2, ..., locN]}}
        self.wordlocation = shelve.open(self.dbtables['wordlocation'], writeback=True, flag='c')

        #{tourl:{fromUrl:None}}
        self.link = shelve.open(self.dbtables['link'], writeback=True, flag='c')

        #{word:[(urlFrom, urlTo), (urlFrom, urlTo), ..., (urlFrom, urlTo)]}
        self.linkwords = shelve.open(self.dbtables['linkwords'], writeback=True, flag='c')
        
    def close(self):
        try:
            if hasattr(self, 'urllist'): self.urllist.close()
            if hasattr(self, 'wordlocation'): self.wordlocation.close()
            if hasattr(self, 'link'): self.link.close()
            if hasattr(self, 'linkwords'): self.linkwords.close()
            if hasattr(self, 'pagerank'): self.pagerank.close()
        except OSError:
            pass

        
    def isindexed(self, url):
    
        if not self.urllist.get(smart_str(url, None)):
            return False
        else:
            return True
    
    def addtoindex(self, url, soup):
        if self.isindexed(url):
            print ('skip', url + ' already indexed')
            return False

        print ('Indexing ' + url)
        url = smart_str(url)
        text = self.gettextonly(soup)
        words = self.separatewords(text)

        for i in range(len(words)):
            word = smart_str(words[i])

            if word in ignorewords:
                continue

            self.wordlocation.setdefault(word, {})

            self.wordlocation[word].setdefault(url, [])
            self.wordlocation[word][url].append(i)

        return True
    
    def addlinkref(self, urlFrom, urlTo, linkText):
        fromUrl = smart_str(urlFrom)
        toUrl = smart_str(urlTo)

        if fromUrl == toUrl: return False

        self.link.setdefault(toUrl, {})
        self.link[toUrl][fromUrl] = None

        words=self.separatewords(linkText)
        for word in words:
            word = smart_str(word)

            if word in ignorewords: continue

            self.linkwords.setdefault(word, [])

            self.linkwords[word].append((fromUrl, toUrl))

        return True  
    
    def crawl(self, pages=pagelist, depth=2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                           'Accept-Encoding': 'none',
                           'Accept-Language': 'en-US,en;q=0.8',
                           'Connection': 'keep-alive'}
                    req = urllib2.Request(page, headers=hdr)
                    c = urllib2.urlopen(req)
                except Exception as e:
                    print ("Could not open {}, {}".format(page, e))
                    continue
                soup = BeautifulSoup(c.read(), 'html.parser')
                added = self.addtoindex(page, soup)

                if not added:
                    continue

                outgoingLinkCount = 0
                links = soup('a')
                for link in links:
                    if 'href' in link.attrs:
                        url = urljoin(page, link['href'])
                        
                        if url.find("'") != -1:
                            continue
                        
                        if url[0:4] == 'http' and not self.isindexed(url):
                            newpages.add(url)
                        linkText = self.gettextonly(link)
                        added = self.addlinkref(page, url, linkText)
                        if added:
                            outgoingLinkCount += 1

                self.urllist[smart_str(page)] = outgoingLinkCount
            pages = newpages

class searcher:
    def __init__(self,dbtables):
        self.dbtables = dbtables
        self.opendb()

    def __del__(self):
        self.close()

    # Open the database tables
    def opendb(self):
        # {url:outgoing_link_count}
        self.urllist = shelve.open(self.dbtables['urllist'], writeback=True, flag='r')
        #{word:{url:[loc1, loc2, ..., locN]}}
        self.wordlocation = shelve.open(self.dbtables['wordlocation'], writeback=True, flag='r')
        #{tourl:{fromUrl:None}}
        self.link = shelve.open(self.dbtables['link'], writeback=True, flag='r')
        #{word:[(urlFrom, urlTo), (urlFrom, urlTo), ..., (urlFrom, urlTo)]}
        self.linkwords = shelve.open(self.dbtables['linkwords'], writeback=True, flag='r')
        #{url: rank}
        self.pagerank = shelve.open(self.dbtables['pagerank'], writeback=True, flag='c')
        
    def close(self):
        try:
            if hasattr(self, 'urllist'): self.urllist.close()
            if hasattr(self, 'wordlocation'): self.wordlocation.close()
            if hasattr(self, 'link'): self.link.close()
            if hasattr(self, 'linkwords'): self.linkwords.close()
            if hasattr(self, 'pagerank'): self.pagerank.close()
        except OSError:
            pass


    def getmatchingpages(self,q):
        results = {}
        # Split the words by spaces
        words = [(smart_str(word).lower()) for word in q.split()]
        if words[0] not in self.wordlocation:
                return results, words

        url_set = set(self.wordlocation[words[0]].keys())

        for word in words[1:]:
            if word not in self.wordlocation:
                return results, words
            url_set = url_set.intersection(self.wordlocation[word].keys())

        for url in url_set:
            results[url] = []
            for word in words:
                results[url].append(self.wordlocation[word][url])

        return results, words

    def getscoredlist(self, results, words,weights):

        totalscores = dict([(url, 0) for url in results])


        for (weight,scores) in weights:
            for url in totalscores:
                totalscores[url] += weight*scores.get(url, 0)

        return totalscores

    def query(self,q,choice):
        results, words = self.getmatchingpages(q)
        if len(results) == 0:
            print ('No matching pages found!')
            return
        weights = choice
        scores = self.getscoredlist(results,words,weights)
        rankedscores = sorted([(score,url) for (url,score) in scores.items()],reverse=True)
        liste = []
        for (score,url) in rankedscores[0:10]:
            liste.append('{}\t {}--{}'.format(score,self.get_linkwords_from_url(url),url))

            
        return liste 

    def normalizescores(self,scores,smallIsBetter=0):
        vsmall = 0.00001
        if smallIsBetter:
            minscore=min(scores.values())
            minscore=max(minscore, vsmall)
            return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) \
                         in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u,float(c)/maxscore) for (u,c) in scores.items()])

    def frequencyscore(self, results):
        counts = {}
        for url in results:
            score = 1
            for wordlocations in results[url]:
                score *= len(wordlocations)
            counts[url] = score
        return self.normalizescores(counts, smallIsBetter=False)

    def locationscore(self, results):
        locations=dict([(url, 1000000) for url in results])
        for url in results:
            score = 0
            for wordlocations in results[url]:
                score += min(wordlocations)
            locations[url] = score
        return self.normalizescores(locations, smallIsBetter=True)

    def worddistancescore(self, result):
        urller = result.keys()
        listoflist = result.values()
        counts = {}
        mesafe = 1000000
        if (len(listoflist)) < 2 or (len(urller)) < 2:
            for url in result:
                counts[url] = 1.0
            return counts

        for url in urller:
            for i in range(len(result[url])-1):
                for j in range(len(result[url][i])):
                    for k in range(len(result[url][i+1])):
                        if mesafe > abs(result[url][i][j]-result[url][i+1][k]):
                            mesafe = abs(result[url][i][j]-result[url][i+1][k])

            counts[url]=mesafe

        return self.normalizescores(counts, smallIsBetter=1)
    
    def inboundlinkscore(self, results):
        inboundcount=dict([(url, len(self.link[url])) for url in results if url in self.link])
        return self.normalizescores(inboundcount)

    def pagerankscore(self, results):
        self.pageranks = dict([(url, self.pagerank[url]) for url in results if url in self.pagerank])
        maxrank = max(self.pageranks.values())
        normalizedscores = dict([(url,float(score)/maxrank) for (url,score) in self.pagerank.items()])
        #return self.normalizescores(self.pageranks)
        return normalizedscores

    def calculatepagerank(self,iterations=20):
        # clear out the current page rank table
        # {url:pagerank_score}
        

        # initialize every url with a page rank of 1
        for url in self.urllist.keys():
            self.pagerank[smart_str(url)] = 1.0

        for i in range(iterations):
            print ("Iteration {}".format(i))
            for url in self.urllist.keys():
                if url not in self.link.keys():
                    continue
                print (smart_str(url) , self.pagerank[smart_str(url)])
                pr=0.15
                # Loop through all the pages that link to this one
                for linker in self.link[smart_str(url)]:
                    linkingpr = self.pagerank[linker]
    
                    # Get the total number of links from the linker
                    linkingcount = self.urllist[linker]
                
                    pr += 0.85*(linkingpr/linkingcount)

                self.pagerank[url] = pr
    def get_linkwords_from_url(self, url):
        for word, url_tuple_listesi in self.linkwords.items():
            for url_tuples in url_tuple_listesi:
                if url == url_tuples[1]:
                    return word
        return 'AnaSayfa'



class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self , parent)
        self.parent = parent
        self.initUI()
    
    def initUI(self):
        self.pack()
        #ana başlık
        baslik1_label =Label(self, text="Emekleme Ve Arama Sistemi Ekranı", font="Helvetica 15 bold",height=2)
        baslik1_label.grid(column=1, row=0, sticky=EW)

        #birinci çerçeve 
        cerceve_1 = LabelFrame(self,bd=3, relief=SUNKEN,width=100)
        cerceve_1.grid(column=1,row=1)

        #emeklemeyi başlatıcak buton 
        self.emeklme=Button(cerceve_1, text= "Emeklemeyi Başlat", relief=RAISED,bd=3,width=18, command= self.emekleme_butonu)
        self.emeklme.grid(column=0, row=1)
        
        #arama çubuğunun olduğu çerçeve
        cerceve_2 = LabelFrame(self,bd=3, relief=SUNKEN)
        cerceve_2.grid(column=1,row=2)

        #arama yapılacak kelimelerin girilmesi için entry 
        kelimeler_label =Label(cerceve_2, text="Arama yapılacak kelime(ler)i giriniz:")
        kelimeler_label.grid(column=1, row=2)
        self.var_kelimeler = StringVar()
        kelimeler_entry = Entry(cerceve_2,textvariable= self.var_kelimeler,relief=RIDGE,bd=3,width=70)
        kelimeler_entry.grid(column=1, row=3)

        #Checkbutton çerçevesi
        cerceve_3 = LabelFrame(self,bd=3, relief=SUNKEN)
        cerceve_3.grid(column=1,row=3)
        
        #Checkbutton'lar
        self.checkbutton1 = IntVar()  
        self.checkbutton2 = IntVar()  
        self.checkbutton3 = IntVar()
  
        
        button1 = Checkbutton(cerceve_3, text = "Kelime Frekansı", variable = self.checkbutton1,height = 2)
        button2 = Checkbutton(cerceve_3, text = "Inbound Link",variable = self.checkbutton2,height = 2)
        button3 = Checkbutton(cerceve_3, text = "PageRank",variable = self.checkbutton3,height = 2)
    
        button1.grid(column=0, row=4,sticky=W)
        button2.grid(column=0, row=5,sticky=W)
        button3.grid(column=0, row=6,sticky=W)
  
        #ara butonu
        self.ara=Button(cerceve_3, text= "Ara", relief=RAISED,bd=3,width=5,command=self.kullanici_kelimesi)
        self.ara.grid(column=1, row=5,sticky=E)

        #text widget çerçevesi
        cerceve_4 = LabelFrame(self,bd=3, relief=SUNKEN)
        cerceve_4.grid(column=1,row=4)
        
        #text widget
        self.textbox = Listbox(cerceve_4, width=95,height=20)
        self.textbox.grid(sticky=EW)


    def emekleme_butonu(self):
        #"Emeklemeyi Başlat" butonuna basıldığında crawler sınıfı çalıştırılır ve emekleme işlemi yapılır
        # emekleme bittiğinde ekrana "Emekleme işlemi başarıyla gerçekleştirilmiştir" yazısı bastırılır 
        crawler_ = crawler(dbtables)
        crawler_.createindextables()
        crawler_.crawl()
        crawler_.close()
        self.textbox.insert(0,"Emekleme işlemi başarıyla gerçekleştirilmiştir")
        

    def choice(self):
        
        mysearchengine = searcher(dbtables)
        results, words = mysearchengine.getmatchingpages(self.var_kelimeler.get())
        button1=self.checkbutton1.get()
        button2=self.checkbutton2.get()
        button3=self.checkbutton3.get()
        

        if button1==1 and button2==0 and button3==0:  
            weights = [(1.0, mysearchengine.frequencyscore(results))]
            return weights
        if button1==1 and button2==1 and button3==0:
            weights = [(1.0, mysearchengine.frequencyscore(results)), (1.0,mysearchengine.inboundlinkscore(results))]
            return weights
        if button1==1 and button2==1 and button3==1:
            mysearchengine.calculatepagerank()
            weights = [(1.0, mysearchengine.frequencyscore(results)), (1.0,mysearchengine.inboundlinkscore(results)),(1.0,mysearchengine.pagerankscore(results))]
            return weights
        if button1==1 and button2==0 and button3==1:  
            mysearchengine.calculatepagerank()
            weights = [(1.0, mysearchengine.frequencyscore(results)),(1.0,mysearchengine.pagerankscore(results))]
            return weights
        if button1==0 and button2==1 and button3==0:
            weights = [(1.0,mysearchengine.inboundlinkscore(results))]
            return weights
        if button1==0 and button2==1 and button3==1:
            mysearchengine.calculatepagerank()
            weights = [(1.0,mysearchengine.inboundlinkscore(results)),(1.0,mysearchengine.pagerankscore(results))]
            return weights
        if button1==0 and button2==0 and button3==1:
            mysearchengine.calculatepagerank()  
            weights = [(1.0,mysearchengine.pagerankscore(results))]
            return weights

    def kullanici_kelimesi(self):
        try:
            self.kelimeler=self.var_kelimeler.get()
            mysearchengine = searcher(dbtables)
            tmp = mysearchengine.query(self.kelimeler,self.choice())
            mysearchengine.close()
            self.textbox.delete(0,END)
            for satir in tmp:
                self.textbox.insert(END,satir)
        except IndexError:
            self.textbox.insert(END,"önce aradığınız kelimeyi girmelisiniz")

            


        
        

def main():
    
    root = Tk()
    root.title("Endeksleme Ve Arama")
    app = Example(root)
    root.mainloop()
    
main()
