# GN3 Guile Webservice

This directory provides a Guile endpoint for the REST API. It is used in conjunction with the Python REST API and WIP.

GNU Guile allows you to develop against a live running web server using emacs-geiser. To try this fire up the web server as

```
. .guix-shell -- guile --listen=1970 -e main ./webserver.scm 8091
```

Note the leading dot. The .guix-shell is defined in `genenetwork3/gn3-guile/web` and loads required packages using GNU Guix. 

Next fire up emacs with `emacs-geiser-guile` and connect to the running web server with `M-x geiser-connect` and the port `1970`. Now you can not only inspect procedures, but also update any prodedure on the live server using `C-M-x` and get updated output from the webserver!


