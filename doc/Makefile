ALL: diag-disk.1 diag-modem.1 diag-cd.1 fgdiag.1

fgdiag.1: fgdiag.man.txt
	txt2man -t fgdiag -s 1 -r fgdiag -v "Free Geek" fgdiag.man.txt > fgdiag.1

diag-disk.1 diag-modem.1 diag-cd.1: fgdiag.1
	ln -s fgdiag.1 $@

clean:
	rm diag-disk.1 diag-modem.1 diag-cd.1 fgdiag.1

.PHONY: ALL clean
