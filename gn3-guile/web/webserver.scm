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
 ;; (ice-9 debugger)
 ;; (ice-9 breakpoints)
 ;; (ice-9 source)
 (srfi srfi-1)
 (srfi srfi-26)
 (web http)
 (web client)
 (web request)
 (web response)
 (web uri)
 (fibers web server))

(define get-version
  "2.0")

(define (base-url)
  "https://genenetwork.org")

(define (prefix)
  "Build the API URL including version"
  (string-append (base-url) "/api/" get-version))

(define (mk-url postfix)
  "Add the path to the API URL"
  (string-append (prefix) "/" postfix))

(define (mk-doc postfix)
  "Create a pointer to HTML documentation"
  (string-append (base-url) "/" postfix ".html"))

(define (meta url)
  "Adds /meta to the URL"
  (string-append url "/meta"))

(define info `(
  ("name" . "GeneNetwork REST API")
  ("version" . ,get-version)
  ("comment" . "This is the official REST API for the GeneNetwork service hosted at https://genenetwork.org/")
  ("license" . (("source code" . "AGPL")))
  ("note" . "work in progress (WIP)")
  ("see also". ,(meta (prefix)))))

(define info-meta `(		    
   ("doc" . ,(mk-doc "info"))
   ("API" .
    ((,(mk-url "species")."Get a list of all species")
     (,(mk-url "mouse")."Get information on mouse")
     (,(mk-url "datasets")."Get a list of datasets")))))


(define (sparql-exec query)
  "Execute raw SPARQL query returning response as a UTF8 string"
  (bytevector->string (receive (response-status response-body)
                           (http-request (string-append "https://sparql.genenetwork.org/sparql?default-graph-uri=&query=" (uri-encode query) "&format=application%2Fsparql-results%2Bjson"))
                         
                         response-body) "UTF-8"))

(define (unpack field response)
  "Helper to get nested JSON field from SPARQL response"
  (cdr (assoc field response)))

(define (sparql-names response)
  "Helper to get the names part of a SPARQL query"
  (unpack "vars" (unpack "head" response)))

(define (sparql-results response)
  "Helper to get the results part of a SPARQL query"
  (unpack "bindings" (unpack "results" response)))

(define (sparql-scm query)
  "Return dual S-exp 'resultset' of varnames and results"
  (let ((response (json-string->scm (sparql-exec query))))
   (values (sparql-names response) (sparql-results response))))

(define (sparql-species)
  (sparql-scm "
PREFIX gn: <http://genenetwork.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?species WHERE {
    ?species rdf:type gn:species .
}"))

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
!#

(define (sparql-species-meta)
  (sparql-scm "
PREFIX gn: <http://genenetwork.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?species ?p ?o WHERE {
   MINUS { ?species rdf:type ?o . }
{
  SELECT DISTINCT ?species ?p ?o WHERE {
    ?species rdf:type gn:species .
    ?species ?p ?o .
   }}}"))


(define (get-species)
  (receive (names result) (sparql-species-meta)
   result))

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
(define (tojson recs)
  (map (lambda (r)
	 (let* ([k (car r)]
		[v (cdr r)])
	   ; (display k)
	   ; (display v)
	   ; (newline)
	   (scm->json (map (lambda (i) (cons (car i) (car (cdr i)))) v))
	   ))
	 recs  )
  )

(define (get-species-api-str)
  (scm->json-string #("https://genenetwork.org/api/v2/mouse/"
                      "https://genenetwork.org/api/v2/rat/")))

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
    (('GET "meh")
     (render-json-string2 "ITEST"))
    (('HEAD "meh")
     (render-json-string2 "ITEST"))
    (('GET "meta")
     (render-json info-meta))
    (('GET "version")
     (render-json get-version))
    (('GET "species")
     (render-json (get-species)))
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
