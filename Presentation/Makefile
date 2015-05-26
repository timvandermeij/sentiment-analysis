NAME = Presentation

all: $(NAME).pdf
pdf: $(NAME).pdf

$(NAME).pdf: $(NAME).tex
	pdflatex $(NAME)
	pdflatex $(NAME)

clean:
	rm -f $(NAME).log
	rm -f $(NAME).aux
	rm -f $(NAME).ps
	rm -f $(NAME).dvi
	rm -f $(NAME).bbl
	rm -f $(NAME).blg
	rm -f $(NAME).log
	rm -f $(NAME).toc
	rm -f $(NAME).synctex.gz
	rm -f $(NAME).out
	rm -f $(NAME).nav
	rm -f $(NAME).vrb
	rm -f $(NAME).snm
	rm -f $(NAME).pdf
