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

(use-modules
 (srfi srfi-1)
 (srfi srfi-26)
 (ice-9 match)
 (ice-9 popen)
 (ice-9 rdelim)
 (gn packages gemma)
 (gn packages python)
 (gnu packages base)
 (gnu packages check)
 (gnu packages databases)
 (gnu packages statistics)
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

(define git-file?
  (let* ((pipe (with-directory-excursion %source-dir
                 (open-pipe* OPEN_READ "git" "ls-files")))
         (files (let loop ((lines '()))
                  (match (read-line pipe)
                    ((? eof-object?)
                     (reverse lines))
                    (line
                     (loop (cons line lines))))))
         (status (close-pipe pipe)))
    (lambda (file stat)
      (match (stat:type stat)
        ('directory #t)
        ((or 'regular 'symlink)
         (any (cut string-suffix? <> file) files))
        (_ #f)))))

(package
  (name "genenetwork3.git")
  (version "0.0.1")
  (source (local-file %source-dir
                      #:recursive? #t
                      #:select? git-file?))
  (propagated-inputs `(("coreutils" ,coreutils)
                       ("gemma-wrapper" ,gemma-wrapper)
                       ("python" ,python-wrapper)
                       ("python-bcrypt" ,python-bcrypt)
                       ("python-flask" ,python-flask)
                       ("python-ipfshttpclient" ,python-ipfshttpclient)
                       ("python-mypy" ,python-mypy)
                       ("python-mypy-extensions" ,python-mypy-extensions)
                       ("python-mysqlclient" ,python-mysqlclient)
                       ("python-numpy" ,python-numpy)
                       ("python-pylint" python-pylint)
                       ("python-redis" ,python-redis)
                       ("python-requests" ,python-requests)
                       ("python-scipy" ,python-scipy)
                       ("python-sqlalchemy-stubs" ,python-sqlalchemy-stubs)))
  (build-system python-build-system)
  (home-page "https://github.com/genenetwork/genenetwork3")
  (synopsis "GeneNetwork3 API for data science and machine learning.")
  (description "GeneNetwork3 API for data science and machine learning.")
  (license agpl3+))
