(define-module (genenetwork3-package)
  #:use-module ((gn packages genenetwork)
                #:select (genenetwork3) #:prefix gn:)
  #:use-module (guix gexp)
  #:use-module (guix utils)
  #:use-module (guix git-download)
  #:use-module (guix packages))

(define-public genenetwork3
  (package
    (inherit gn:genenetwork3)
    (version (string-append (package-version gn:genenetwork3) "-git"))
    (source (local-file ".."
                        "genenetwork3-checkout"
                        #:recursive? #t
                        #:select? (or (git-predicate (dirname (current-source-directory)))
                                      (const #t))))))

genenetwork3
