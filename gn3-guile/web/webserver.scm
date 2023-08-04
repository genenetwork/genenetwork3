#!/usr/bin/env guile \
-e main -s
!#
;; Minimal web server can be started from command line. Current example routes:
;;
;;    localhost:8080/
;;

(use-modules
 (json)
 (ice-9 match)
 (ice-9 format)
 (ice-9 iconv)
 (ice-9 receive)
 (ice-9 string-fun)
 ;; (ice-9 debugger)
 ;; (ice-9 breakpoints)
 ;; (ice-9 source)
 (srfi srfi-1)
 (srfi srfi-13) ; hash table for memoize
 (srfi srfi-26)
 (web http)
 (web client)
 (web request)
 (web response)
 (web uri)
 (fibers web server))

(define (memoize function) 
   (let ((table (make-hash-table))) 
     (lambda args
       (apply values (hash-ref table args 
                       ;; If the entry isn't there, call the function.    
			      (lambda () 
				(call-with-values 
				    (lambda () (apply function args)) 
				  (lambda results 
				    (hash-set! table args results) 
				    results)))))))) 

(define get-version
  "2.0")

(define (base-url)
  "https://genenetwork.org")

(define (gn-sparql-endpoint-url)
  "https://sparql.genenetwork.org/sparql")

(define (wd-sparql-endpoint-url)
  "https://query.wikidata.org/sparql")

(define (prefix)
  "Build the API URL including version"
  (string-append (base-url) "/api/" get-version))

(define* (mk-url postfix #:optional (ext ""))
  "Add the path to the API URL"
  (string-append (prefix) "/" postfix ext))

(define (mk-html path)
  "Create a pointer to HTML documentation"
  (string-append (base-url) "/" path ".html"))

(define (mk-doc path)
  "Create a pointer to HTML documentation"
  (mk-html (string-append "doc/" path)))

(define (mk-meta path)
  "Create a meta URL for the API path"
  (mk-url path ".meta.json"))

(define (mk-rec path)
  "Create a JSON URL for the API path"
  (mk-url path ".json"))

(define (mk-term postfix)
  (mk-html (string-append "term" "/" postfix)))

(define (mk-id postfix)
  (mk-html (string-append "id" "/" postfix)))

(define (mk-predicate postfix)
  (mk-html (string-append "predicate" "/" postfix)))

(define (wdt-taxon-name) "wdt:P225")

(define info `(
  ("name" . "GeneNetwork REST API")
  ("version" . ,get-version)
  ("comment" . "This is the official REST API for the GeneNetwork service hosted at https://genenetwork.org/")
  ("license" . (("source code" . "AGPL")))
  ("note" . "work in progress (WIP)")
  ("prefix" . ,(prefix))
  ("links". (("species" . ,(mk-meta "species"))))))

(define info-meta `(		    
   ("doc" . ,(mk-html "info"))
   ("API" .
    ((,(mk-url "species")."Get a list of all species")
     (,(mk-url "mouse")."Get information on mouse")
     (,(mk-url "datasets")."Get a list of datasets")))))


(define (sparql-exec endpoint-url query)
  "Execute raw SPARQL query returning response as a UTF8 string"
  (bytevector->string (receive (response-status response-body)
                          (http-request (string-append endpoint-url "?default-graph-uri=&query=" (uri-encode query) "&format=application%2Fsparql-results%2Bjson"))
                         
                         response-body) "UTF-8"))

(define (sparql-tsv endpoint-url query)
  "Execute raw SPARQL query returning response as a UTF8 string, e.g.
(tsv->scm (sparql-tsv (wd-sparql-endpoint-url) \"wd:Q158695\"))
"
  ; GET /sparql?query=SELECT%20DISTINCT%20%2A%20where%20%7B%0A%20%20wd%3AQ158695%20wdt%3AP225%20%3Fo%20.%0A%7D%20limit%205 HTTP/2
  (receive (response-status response-body)
                          (http-get (pk (string-append endpoint-url "?query=" (uri-encode query))) #:headers '((Accept . "text/tab-separated-values")(user-agent . "curl/7.74.0")))
                         response-body))

(define (unpack field response)
  "Helper to get nested JSON field from SPARQL response"
  (cdr (assoc field response)))

(define (sparql-names response)
  "Helper to get the names part of a SPARQL query"
  (unpack "vars" (unpack "head" response)))

(define (sparql-results response)
  "Helper to get the results part of a SPARQL query"
  (unpack "bindings" (unpack "results" response)))

(define (sparql-scm endpoint-url query)
  "Return dual S-exp 'resultset' of varnames and results"
  (let ((response (json-string->scm (sparql-exec endpoint-url query))))
   (values (sparql-names response) (sparql-results response))))

(define (tsv->scm text)
  "Split a TSV string into a list of fields. Returns list of names header) and rows"
  (let ([lst (map (lambda (f) (string-split f #\tab) ) (delete "" (string-split text #\newline)))])
    (values (car lst) (cdr lst))
  ))

#!
(define-values (names res) (sparql-species-meta))
(define table (get-rows names res))
(define recs '())
(define h (compile-species recs table))
(assoc "http://genenetwork.org/species_drosophila_melanogaster" h)
(assoc-ref h "http://genenetwork.org/species_drosophila_melanogaster") ;; note switch!
(define d (car h))
(assoc-ref (list d) "http://genenetwork.org/species_drosophila_melanogaster")

(scm->json #(1  (("2" . 3))))
;; [1,{"2":3}]
(scm->json #("http://genenetwork.org/species_drosophila_melanogaster" (("http://genenetwork.org/menuName" . "Drosophila") ("http://genenetwork.org/binomialName" . "Drosophila melanogaster") )))
;; ["http://genenetwork.org/species_drosophila_melanogaster",{"http://genenetwork.org/menuName":"Drosophila","http://genenetwork.org/binomialName":"Drosophila melanogaster"}]
l
;; (("http://genenetwork.org/menuName" "Drosophila") ("http://genenetwork.org/name" "Drosophila") ("http://genenetwork.org/binomialName" "Drosophila melanogaster"))
(scm->json (map (lambda (i) (cons (car i) (car (cdr i)))) l))
;; {"http://genenetwork.org/menuName":"Drosophila","http://genenetwork.org/name":"Drosophila","http://genenetwork.org/binomialName":"Drosophila melanogaster"}


curl -G https://query.wikidata.org/sparql -H "Accept: application/json; charset=utf-8" --data-urlencode query="SELECT DISTINCT * where {
  wd:Q158695 wdt:P225 ?o .
} limit 5"
{
  "head" : {
    "vars" : [ "o" ]
  },
  "results" : {
    "bindings" : [ {
      "o" : {
        "type" : "literal",
        "value" : "Arabidopsis thaliana"
      }
    } ]
  }
}
!#

(define (sparql-wd-species-info species)
  "Returns wikidata entry for species, e.g.:

   (sparql-wd-species-info \"Q158695\") generates something like

SELECT DISTINCT * where {  wd:Q158695 wdt:P225 ?o . } limit 10

"
  (sparql-tsv (wd-sparql-endpoint-url) (string-append "
SELECT DISTINCT ?taxon ?ncbi ?descr where {  
    wd:" species " " (wdt-taxon-name) " ?taxon ;
               wdt:P685 ?ncbi ;
      schema:description ?descr .
    ?species wdt:P685 ?ncbi .
    FILTER (lang(?descr)='en')
} limit 5

")))

#!
gn:Mus_musculus rdf:type gnc:species .
gn:Mus_musculus gnt:name "Mouse" .
gn:Mus_musculus rdfs:label "Mouse (Mus musculus, mm10)" .
gn:Mus_musculus gnt:binomialName "Mus musculus" .
gn:Mus_musculus gnt:family "Vertebrates" .
gn:Mus_musculus gnt:organism taxon:10090 .
!#

(define (sparql-species)
  (sparql-scm (gn-sparql-endpoint-url) "
PREFIX gn: <http://genenetwork.org/id/>
PREFIX gnc: <http://genenetwork.org/category/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?species WHERE {
    ?species rdf:type gnc:species .
}"))

(define (sparql-species-meta)
  (sparql-scm (gn-sparql-endpoint-url) "
PREFIX gn: <http://genenetwork.org/id/>
PREFIX gnc: <http://genenetwork.org/category/>
PREFIX gnt: <http://genenetwork.org/term/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?species ?p ?o WHERE {
   MINUS { ?species rdf:type ?o . }
{
  SELECT DISTINCT ?species ?p ?o WHERE {
    ?species rdf:type gnc:species .
    ?species ?p ?o .
   }}}"))

(define (get-values names row)
  "Get values by name from a resultset row"
  (map (lambda (n) (unpack "value" (unpack n row))) (array->list names)))

(define (get-rows names results)
  "Format results as a list of values ordered by names"
  (map (lambda (row) (get-values names row)) (array->list results)))
  
;; from the triples first harvest the species URIs, followed by creating records of information

(define (compile-species recs rows)
  "Compile a matrix of species triples into records"
  (for-each (lambda (r)
		(let* ([s (car r)]
		       [v (cdr (cdr r))]
		       [p (car (cdr r))]
		       [nrec '()]
		       [kv (assoc s recs)]) ; find record to fill based on subject
		  (if (not kv)
		      (set! nrec '())
		      (set! nrec (cdr kv))
		      )
		  (set! nrec (assoc-set! nrec p v))
		  (set! recs (assoc-set! recs s nrec))
		  ))
		rows)
  recs)

;; result should be a vector of list of pair
(define (species-digest recs)
  (map (lambda (r)
	 (let* ([k (car r)]
		[v (cdr r)])
	   ; with key use (cons k (map (lambda (i) (cons (car i) (car (cdr i)))) v))
	   (map (lambda (i) (cons (url-parse-id (car i)) (car (cdr i)))) v)
	   ))
	 recs  )
  )

(define (get-species)
  (receive (names res) (sparql-species-meta)
    (let* ([table (get-rows names res)]
           [recs '()]
           [h (compile-species recs table)])
      (species-digest h))
    ))

; (define (wd-species-info wd)
;  )

(define (url-parse-id uri)
  (if uri
      (car (reverse (string-split uri #\057)))
      "unknown"
      ))

(define (strip-lang s)
  "Strip quotes and language tag (@en) from RDF entries"
  (list->string (match (string->list s)
		  [(#\"rest ... #\") rest]
		  [(#\"rest ... #\" #\@ #\e #\n) rest]
		  [rest rest]))
  )

(define (normalize-id str)
  ;; (string-replace-substring (string-downcase str) " " "_")
  (string-replace-substring str " " "_")
  )

(define (get-expanded-species)
  "Here we add information related to each species"
  (map (lambda (rec)
	 (let ([wd-id (url-parse-id (assoc-ref rec "22-rdf-syntax-ns#isDefinedBy"))]
	       [short-name (normalize-id (assoc-ref rec "name"))])
	   (if (string=? wd-id "unknown")
	       rec
	       ; wikidata query:
	       (receive (names row) (tsv->scm (sparql-wd-species-info wd-id))
		 (match (pk (car row))
		   ((taxonomy-name ncbi descr)
		    (let ([ncbi-id (strip-lang ncbi)]
			  [taxonomy-lnk (string-replace-substring (strip-lang taxonomy-name) " " "_")])
		      (cons `("id" . ,short-name)
		      (cons `("wikidata" . ,wd-id)
		      (cons `("taxonomy-id" . ,ncbi-id)
		      (cons `("ncbi-url" . ,(string-append "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=" ncbi-id))
		      (cons `("uniprot-url" . ,(string-append "https://www.uniprot.org/taxonomy/" ncbi-id))
		      (cons `("wikidata-url" . ,(string-append "http://www.wikidata.org/entity/" wd-id))
		      (cons `("wikispecies-url" . ,(string-append "https://species.wikimedia.org/wiki/" taxonomy-lnk))
		      (cons `("taxonomy-name" . ,(strip-lang taxonomy-name))
		      ; (cons `("shortname" . ,shortname) - problematic
		      (cons `("description" . ,(strip-lang descr))
			    rec)))))))))))
		      )
	   )))
	 ) (get-species)
))

(define (get-species-api-str)
  (scm->json-string #("https://genenetwork.org/api/v2/mouse/"
                      "https://genenetwork.org/api/v2/rat/")))

(define (get-species-shortnames recs)
  (map (lambda r (assoc-ref (car r) "shortName")) recs))

(define (get-species-links recs)
  "Return a list of short names and expand them to URIs"
  (map (lambda r
	 (let ([shortname (assoc-ref (car r) "shortName")])
	   (cons shortname (mk-rec shortname)))) recs)
  )

(define (get-species-rec)
  (list->vector (get-expanded-species)))

(define (get-species-meta)
  (let ([recs (get-expanded-species)])
    `(("comment" . "Get information on species")
      ("doc" . ,(mk-doc "species"))
      ("meta" . ,(mk-meta "species"))
      ("rec" . ,(mk-rec "species"))
      ("links" . ,(get-species-links recs)))))

;; ---- REST API web server handler

(define (not-found2 request)
  (values (build-response #:code 404)
          (string-append "Resource X not found: "
                         (uri->string (request-uri request)))))

(define (not-found uri)
  (list (build-response #:code 404)
        (string-append "Resource not found: " (uri->string uri))))

(define (render-json json)
  (list '((content-type . (application/json)))
        (lambda (port)
          (scm->json json port))))

(define (render-json-string2 json)
  (list '((content-type . (text/plain)))
	(lambda (port)
	  ;; (display "ThthxST" port)
	  (format port "~a" "foo")
	  )))
  
(define (controller request body)
  (match-lambda
    (('GET)
     (render-json info))
    (('GET "version")
     (render-json get-version))
    (('GET "species.json")
     (render-json (get-species-rec)))
    (('GET "species.meta.json")
     (render-json (get-species-meta)))
    (('GET "species")
     (render-json (get-species-meta)))
    (('GET id)
     (let ([names (get-species-shortnames (get-expanded-species))])
       (match (string->list id)
	 [(name ... #\. #\j #\s #\o #\n) (render-json (list->string name))]
	 [rest (render-json "WIP")])))
    (_ (not-found (request-uri request)))
    ))

(define (request-path-components request)
  (split-and-decode-uri-path (uri-path (request-uri request))))

(define (handler request body)
  (format #t "~a ~a\n"
          (request-method request)
          (uri-path (request-uri request)))
  (apply values
         ((controller request body)
          (cons (request-method request)
                (request-path-components request)))))

(define (start-web-server address port)
  (format (current-error-port)
          "GN REST API web server listening on http://~a:~a/~%"
          address port)
  ;; Wrap handler in another function to support live hacking via the
  ;; REPL. If handler is passed as is and is then redefined via the
  ;; REPL, the web server will still be using the old handler. The
  ;; only way to update the handler reference held by the web server
  ;; would be to restart the web server.
  (run-server (cut handler <> <>)
              #:addr (inet-pton AF_INET address)
              #:port port))

(define (main args)
  (write (string-append "Starting Guile REST API " get-version " server!"))
  (write args)
  (newline)
  (let ((listen (inexact->exact (string->number (car (cdr args))))))
    (display `("listening on" ,listen))
    ;; (write listen)
    ;; (run-server hello-world-handler 'http `(#:port ,listen))))
    (start-web-server  "127.0.0.1" listen)))
