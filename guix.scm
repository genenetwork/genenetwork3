;;; guix.scm --- genenetwork3 rest Api guix bootstrapping file.
;;;
;;; Copyright © 2021 Bonface Munyoki Kilyungi <me@bonfacemunyoki.com>
;;;
;;; This file is part of genenetwork3.
;;;
;;; genenetwork3 is free software: you can redistribute it and/or
;;; modify it under the terms of the GNU General Public License as
;;; published by the Free Software Foundation; either version 3 of the
;;; License, or (at your option) any later version.
;;;
;;; sheepdog is distributed in the hope that it will be useful, but
;;; WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
;;; General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with genenetwork3. If not, see https://www.gnu.org/licenses/.

;; Make sure you have the
;; https://git.genenetwork.org/guix-bioinformatics/guix-bioinformatics channel
;; set up.
;;
;; To get a development container (e.g., run in emacs shell).
;;
;;   guix environment -C -l guix.scm

(use-modules (gn packages gemma)
             (gn packages python)
             (gnu packages base)
             (gnu packages check)
             (gnu packages graph)
             (gnu packages cran)
             (gnu packages databases)
             (gnu packages statistics)
             (gnu packages bioconductor)
             (gnu packages golang)
             (gn packages genenetwork)
             (gnu packages python)
             (gnu packages python-check)
             (gnu packages python-crypto)
             (gnu packages python-web)
             (gnu packages python-xyz)
             (gnu packages python-science)
             ((guix build utils) #:select (with-directory-excursion))
             (guix build-system python)
             (guix gexp)
             (guix git-download)
             (guix licenses)
             (guix packages))

(define %source-dir (dirname (current-filename)))


(package
  (name "genenetwork3.git")
  (version "0.1.0")
  (source (local-file %source-dir "genenetwork3-checkout"
                      #:recursive? #t
                      #:select? (git-predicate %source-dir)))
  (propagated-inputs `(("coreutils" ,coreutils)
                       ("gemma-wrapper" ,gemma-wrapper)
                       ("gunicorn" ,gunicorn)
                       ("python" ,python-wrapper)
                       ("python-bcrypt" ,python-bcrypt)
                       ("python-flask" ,python-flask)
                       ("python-flask-cors" ,python-flask-cors)
                       ("python-flask-socketio" ,python-flask-socketio)
                       ("python-ipfshttpclient" ,python-ipfshttpclient)
                       ("python-mypy" ,python-mypy)
                       ("python-mypy-extensions" ,python-mypy-extensions)
                       ("python-mysqlclient" ,python-mysqlclient)
                       ("python-numpy" ,python-numpy)
                       ("python-pandas" ,python-pandas)
                       ("python-pingouin" ,python-pingouin)
                       ("python-plotly" ,python-plotly)
                       ("python-pylint" ,python-pylint)
                       ("python-redis" ,python-redis)
                       ("python-requests" ,python-requests)
                       ("python-scipy" ,python-scipy)
                       ("r-optparse" ,r-optparse)
                       ("r-qtl" ,r-qtl)
                       ("r-rjson" ,r-rjson)
                       ("r-stringi" ,r-stringi)
                       ("r-wgcna" ,r-wgcna)
                       ("rust-qtlreaper" ,rust-qtlreaper)))
  (build-system python-build-system)
  (home-page "https://github.com/genenetwork/genenetwork3")
  (synopsis "GeneNetwork3 API for data science and machine learning.")
  (description "GeneNetwork3 API for data science and machine learning.")
  (license agpl3+))
