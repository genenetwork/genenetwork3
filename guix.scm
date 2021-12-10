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
;;   guix shell -C -Df guix.scm

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
             (gnu packages rdf)
             ((guix build utils) #:select (with-directory-excursion))
             (guix build-system python)
             (guix gexp)
             (guix git-download)
             (guix licenses)
             (guix packages))

(define %source-dir (dirname (current-filename)))

(package
  (inherit genenetwork3)
  (source (local-file %source-dir "genenetwork3-checkout"
                      #:recursive? #t
                      #:select? (git-predicate %source-dir))))
