(use-modules (gnu)
             (gn services databases)
             (gnu packages admin)
             (gnu services shepherd)
             (guix derivations)
             (guix monads)
             (guix profiles)
             (guix search-paths)
             (guix records)
             (guix store)
             (ice-9 match))

(define genenetwork3
  (load "guix.scm"))

(define (packages->profile packages)
  "Return profile with PACKAGES."
  (with-store store
    (run-with-store store
      (mlet* %store-monad ((prof-drv (profile-derivation
                                      (packages->manifest packages)))
                           (profile -> (derivation->output-path prof-drv)))
        (mbegin %store-monad
          (built-derivations (list prof-drv))
          (return profile))))))

(define (packages->environment-variables packages)
  "Return environment variables of a profile with PACKAGES. Return value is an
association list mapping the names of environment variables to their values."
  (map (match-lambda
         ((search-path . value)
          (cons (search-path-specification-variable search-path)
                value)))
       (profile-search-paths (packages->profile packages))))

(define (packages->profile-environment packages)
  "Return environment of a profile with PACKAGES. Return value is a
list of environment variables suitable as input to the environ
function."
  (map (match-lambda
         ((search-path . value)
          (string-append (search-path-specification-variable search-path)
                         "=" value)))
       (profile-search-paths (packages->profile packages))))

(define-record-type* <genenetwork3-configuration>
  genenetwork3-configuration make-genenetwork3-configuration
  genenetwork3-configuration?
  (package genenetwork3-configuration-package
           (default genenetwork3))
  (port genenetwork3-configuration-port
        (default 5000)))

(define %genenetwork3-accounts
  (list (user-group (name "genenetwork3")
                    (system? #t))
        (user-account
         (name "genenetwork3")
         (group "genenetwork3")
         (system? #t)
         (comment "GeneNetwork 3 user")
         (home-directory "/var/empty")
         (shell (file-append shadow "/sbin/nologin")))))

;; FIXME: Factorize this service into two. We should have a gunicorn
;; service that is extended by the genenetwork service. This way, the
;; app is better decoupled from the deployment.
(define genenetwork3-shepherd-service
  (match-lambda
    (($ <genenetwork3-configuration> package port)
     (shepherd-service
      (documentation "Run GeneNetwork 3.")
      (provision '(genenetwork3))
      (requirement '(networking virtuoso))
      (start #~(begin
                 ;; Reference the profile.
                 #$(packages->profile (list package))
                 ;; Start the gunicorn process.
                 (make-forkexec-constructor
                  (list #$(file-append gunicorn "/bin/gunicorn")
                        "-b" #$(string-append "127.0.0.1:" (number->string port))
                        "gn3.app:create_app()")
                  #:user "genenetwork3"
                  #:group "genenetwork3"
                  #:environment-variables
                  '#$(packages->profile-environment (list package)))))
      (stop #~(make-kill-destructor))))))

(define genenetwork3-service-type
  (service-type
   (name 'genenetwork3)
   (description "Run GeneNetwork 3.")
   (extensions
    (list (service-extension account-service-type
                             (const %genenetwork3-accounts))
          (service-extension shepherd-root-service-type
                             (compose list genenetwork3-shepherd-service))))
   (default-value (genenetwork3-configuration))))

(operating-system
  (host-name "genenetwork3")
  (timezone "UTC")
  (locale "en_US.utf8")
  (bootloader (bootloader-configuration
               (bootloader grub-bootloader)
               (targets (list "/dev/sdX"))))
  (file-systems (cons (file-system
                        (device "root")
                        (mount-point "/")
                        (type "ext4"))
                      %base-file-systems))
  (users %base-user-accounts)
  (packages %base-packages)
  (services (cons*
             ;; (service virtuoso-service-type
             ;;          (virtuoso-configuration
             ;;           (http-server-port 8891)))
             (service genenetwork3-service-type
                      (genenetwork3-configuration
                       (port 5000)))
             %base-services)))
