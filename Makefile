CWD := $(shell readlink -en $(dir $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))))

.PHONY: all
all: fetch_docker build_from_docker

.PHONY: build_from_docker
build_from_docker:
	docker run --rm -v $(CWD):/work jamrizzi/centos-dev:latest make build_centos
	docker run --rm -v $(CWD):/work jamrizzi/ubuntu-dev:latest make build_ubuntu
	$(info built from docker)
.PHONY: build_centos
build_centos: fetch_dependancies build rancher-ident-centos.tar.gz sweep
	$(info built for centos)
.PHONY: build_ubuntu
build_ubuntu: fetch_dependancies build rancher-ident-ubuntu.tar.gz sweep
	$(info built for ubuntu)

.PHONY: build
build: dist/rancher-ident
	$(info built)
dist/rancher-ident:
	pyinstaller --onefile --noupx rancher-ident.py

rancher-ident-centos.tar.gz:
	@cp dist/rancher-ident ./
	@tar -zcvf rancher-ident-centos.tar.gz rancher-ident
	@rm -f rancher-ident
rancher-ident-ubuntu.tar.gz:
	@cp dist/rancher-ident ./
	@tar -zcvf rancher-ident-ubuntu.tar.gz rancher-ident
	@rm -f rancher-ident

.PHONY: clean
clean: sweep bleach
	$(info cleaned)
.PHONY: sweep
sweep:
	@rm -rf build dist *.spec */*.spec *.pyc */*.pyc get-pip.py
	$(info swept)
.PHONY: bleach
bleach:
	@rm -rf rancher-ident rancher-ident-*
	$(info bleached)

.PHONY: fetch_dependancies
fetch_dependancies: pip future pyinstaller
	$(info fetched dependancies)
.PHONY: pip
pip:
ifeq ($(shell whereis pip), $(shell echo pip:))
	curl -O https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
endif
.PHONY: future
future:
	pip install future
.PHONY: pyinstaller
pyinstaller:
ifeq ($(shell whereis pyinstaller), $(shell echo pyinstaller:))
	pip install pyinstaller
endif
.PHONY: fetch_docker
fetch_docker:
ifeq ($(shell whereis docker), $(shell echo docker:))
	curl -L https://get.docker.com/ | bash
endif
	docker run hello-world
	$(info fetched docker)
