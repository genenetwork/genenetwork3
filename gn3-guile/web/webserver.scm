#!/usr/bin/env guile \
-e main -s
!#
;; Minimal web server can be started from command line. Current example routes:
;;
;;    localhost:8080/version.json
;;
;; Note that this is a single blocking thread server right now.

(use-modules (json)
             (web server)
             (web request)
             (web response)
             (web uri))

(define (get-version-str)
  "2.0")

(define info-list (scm->json-string `(
                                      ("name" . "GeneNetwork REST API")
                                      ("version" . ,(get-version-str))
                                      ("comment" . "This is the official REST API for the GeneNetwork service hosted at https://genenetwork.org/")
                                      ("license" . (("source code" . "AGPL")))
                                      ("note" . "work in progress (WIP)")
                                      ("api". #(
                                                    "https://genenetwork.org/api/v2/species/"
                                                    "https://genenetwork.org/api/v2/populations/"
                                                    "https://genenetwork.org/api/v2/datasets/"
                                                    )
                                      ))))

(define (get-gn-info-str)
  info-list
  )

(define (get-species-str)
  (scm->json-string '(("Mus_musculus" . (("id" . "mouse" )
                                         ("api" . "https://genenetwork.org/api/v2/mouse/")))
                      ("Rattus_norvegicus" . (("id" . "rat")
                                         ("api" . "https://genenetwork.org/api/v2/rat/")))
                                              )))


;; ---- REST API web server handler

(define (hello-world-handler request body)
  (let ((path (uri-path (request-uri request))))
    (cond
     ((member path (list "/version.json"))
      (values '((content-type . (application/json)))
              (get-version-str)
              ))
     ((member path (list "/species/"))
      (values '((content-type . (application/json)))
              (get-species-str)
              ))
     ((member path (list "/"))
      (values '((content-type . (application/json)))
              (get-gn-info-str)
              ))
     (else
      (not-found request)))))

(define (not-found request)
  (values (build-response #:code 404)
          (string-append "Resource not found: "
                         (uri->string (request-uri request)))))

(define (main args)
  (write (string-append "Starting Guile REST API " (get-version-str) " server!"))
  (write args)
  (newline)
  (let ((listen (inexact->exact (string->number (car (cdr args))))))
    (display `("listening on" ,listen))
    ;; (write listen)
    (run-server hello-world-handler 'http `(#:port ,listen))))
