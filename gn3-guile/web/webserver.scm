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
 (srfi srfi-1)
 (srfi srfi-26)
 (web http)
 (web request)
 (web response)
 (web uri)
 (fibers web server))

(define (get-version)
  "2.0")

(define (base-url)
  "https://genenetwork.org")

(define (prefix)
  "Build the API URL including version"
  (string-append (base-url) "/api/" (get-version)))

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
  ("version" . ,(get-version))
  ("comment" . "This is the official REST API for the GeneNetwork service hosted at https://genenetwork.org/")
  ("license" . (("source code" . "AGPL")))
  ("note" . "work in progress (WIP)")
  ("see also". ,(meta (prefix)))
  ))

(define info-meta `(		    
   ("doc" . ,(mk-doc "info"))
   ("API" .
    ((,(mk-url "species")."Get a list of all species")
     (,(mk-url "mouse")."Get information on mouse")
     (,(mk-url "datasets")."Get a list of datasets")))))

(define (get-species)
  '(("Mus_musculus" . (("id" . "mouse" )
      ("api" . "https://genenetwork.org/api/v2/mouse/")))
    ("Rattus_norvegicus" . (("id" . "rat")
      ("api" . "https://genenetwork.org/api/v2/rat/")))
    ))

(define (get-species-api-str)
  (scm->json-string #("https://genenetwork.org/api/v2/mouse/"
                      "https://genenetwork.org/api/v2/rat/")))

;; ---- REST API web server handler

(define (not-found request)
  (values (build-response #:code 404)
          (string-append "Resource not found: "
                         (uri->string (request-uri request)))))

(define (render-json json)
  (list '((content-type . (application/json)))
        (lambda (port)
          (scm->json json port))))

(define (controller request body)
  (match-lambda
    (('GET)
     (render-json info))
    (('GET "meta")
     (render-json info-meta))
    (('GET "version")
     (render-json (get-version)))
    (('GET "species")
     (render-json (get-species)))
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
  (write (string-append "Starting Guile REST API " (get-version) " server!"))
  (write args)
  (newline)
  (let ((listen (inexact->exact (string->number (car (cdr args))))))
    (display `("listening on" ,listen))
    ;; (write listen)
    ;; (run-server hello-world-handler 'http `(#:port ,listen))))
    (start-web-server  "127.0.0.1" listen)))
