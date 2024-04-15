((python-mode
  . ((flycheck-python-pylint-executable . "env PYTHONPATH=$HOME/.guix-extra-profiles/genenetwork3/lib/python3.10/site-packages/ $HOME/.guix-extra-profiles/genenetwork3/bin/pylint")
     (python-indent . 4)
     (show-trailing-whitespace . 1)
     (python-shell-interpreter . "$HOME/.guix-extra-profiles/genenetwork3/bin/python3")
     (eval .
	   (when
	       (require 'flycheck nil t')
	     (setq elpy-modules
		   (delq 'elpy-module-flymake elpy-modules))
	     (add-hook 'elpy-mode-hook 'flycheck-mode))))))
