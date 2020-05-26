PY_FILES=fluxion scripts fluxion.py
CONTRIB_DIR=contrib
DECODERS_DIR=decoders

help:
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

install_deps: ## install Python dependencies
	python3 -m pip install -r requirements.txt

check: ## check that very basic tests run
	@echo "Checking style with autopep8..."
	autopep8 --exit-code --diff -r $(PY_FILES)
	@echo "Running pylint..."
	PYTHONPATH=. pylint -j0 $(PY_FILES) --fail-under=10
	@echo "Running dummy test..."
	./fluxion.py list
	./fluxion.py list -ts dummy -tv
	./fluxion.py download dummy
	./fluxion.py run -ts dummy -d H.264Dummy -tv AUD_MW_E

format: ## format Python code using autopep8
	autopep8 -i -j0 -r $(PY_FILES)

lint: ## run static analysis using pylint
	PYTHONPATH=. pylint -j0 $(PY_FILES)

$(CONTRIB_DIR):
	mkdir -p $@

$(DECODERS_DIR):
	mkdir -p $@

decoders: h265_reference_decoder h264_reference_decoder ## build all reference decoders

h265_reference_decoder: $(CONTRIB_DIR) $(DECODERS_DIR) ## build H.265 reference decoder
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git --depth=1 | true
	cd $(CONTRIB_DIR)/HM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/HM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release && $(MAKE) -C build TAppDecoder
	find $(CONTRIB_DIR)/HM/bin/umake -name "TAppDecoder" -type f -exec cp "{}" $(DECODERS_DIR) \;

h264_reference_decoder: $(CONTRIB_DIR) ## build H.264 reference decoder
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/JM.git --depth=1 | true
	cd $(CONTRIB_DIR)/JM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/JM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build ldecod
	find $(CONTRIB_DIR)/JM/bin/umake -name "ldecod" -type f -exec cp "{}" $(DECODERS_DIR) \;

.PHONY: help decoders h264_reference_decoder h265_reference_decoder lint check format install_deps
