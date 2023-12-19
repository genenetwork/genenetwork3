(define-module (genenetwork3-package)
  #:use-module ((gn packages genenetwork)
                #:select (genenetwork3) #:prefix gn:)
  #:use-module ((gnu packages check) #:select (python-pylint))
  #:use-module ((gnu packages python-check) #:select (python-mypy))
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

(define-public genenetwork3-all-tests
  (package
    (inherit genenetwork3)
    (arguments
     (substitute-keyword-arguments (package-arguments genenetwork3)
       ((#:phases phases #~%standard-phases)
        #~(modify-phases #$phases
            (add-before 'build 'pylint
              (lambda _
                (invoke "pylint" "main.py" "setup.py" "wsgi.py" "setup_commands"
                        "tests" "gn3" "scripts" "sheepdog")))
            (add-after 'pylint 'mypy
              (lambda _
                (invoke "mypy" ".")))))))
    (native-inputs
     (modify-inputs (package-native-inputs genenetwork3)
       (prepend python-pylint)
       (prepend python-mypy)))))

genenetwork3
