PY_FILES=fluster
CONTRIB_DIR=contrib
DECODERS_DIR=decoders
PYTHONPATH=.
FLUSTER=python3 ./fluster.py -tsd check
ifeq ($(OS),Windows_NT)
FLUSTER+=--no-emoji
endif

help:
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

install_deps: ## install Python dependencies
	python3 -m pip install -r requirements.txt

check: format-check lint ## check that very basic tests run
	@echo "Running dummy test..."
	$(FLUSTER) list
	$(FLUSTER) list -c
	$(FLUSTER) -ne list -c
	$(FLUSTER) list -ts dummy -tv
	$(FLUSTER) download dummy dummy_fail
	$(FLUSTER) run -ts dummy -tv one
	$(FLUSTER) reference Dummy dummy
	$(FLUSTER) run -ts dummy -tv one -j1
	$(FLUSTER) run -ts dummy -s
	$(FLUSTER) -ne run -ts dummy -s
	$(FLUSTER) run -ts dummy -so summary.log && cat summary.log && rm -rf summary.log
	$(FLUSTER) run -ts dummy -j1 -s
	$(FLUSTER) run -ts dummy -th 1
	$(FLUSTER) run -ts dummy -tth 10
ifneq ($(OS),Windows_NT)
	$(FLUSTER) run -ts dummy non_existing_test_suite; test $$? -ne 0
	$(FLUSTER) run -ts dummy -th 2; test $$? -eq 2
	$(FLUSTER) run -ts dummy -tth 0.000000001; test $$? -eq 3
	$(FLUSTER) run -ts dummy_fail -th 1
	$(FLUSTER) run -ts dummy_fail -th 2; test $$? -eq 2
	$(FLUSTER) run -ts dummy_fail -j1 -ff -s; test $$? -ne 0
	$(FLUSTER) download dummy non_existing_test_suite; test $$? -ne 0
	$(FLUSTER) download dummy dummy_download_fail; test $$? -ne 0
endif
	@echo "\nAll test finished succesfully!"

format: ## format Python code using black
	@echo "Formatting coding style with black..."
	black $(PY_FILES)

format-check:
	@echo "Checking coding style with black... Run '$(MAKE) format' to fix if needed"
	black --check $(PY_FILES)

lint: format-check ## run static analysis using pylint, flake8 and mypy
# ignore similar lines error: it's a bug when running parallel jobs - https://github.com/PyCQA/pylint/issues/4118
	@echo "Checking with pylint... Ignore similar lines warning. It's a bug in pylint"
	pylint -j0 $(PY_FILES) --fail-under=10
	@echo "Checking with flake8..."
	flake8 --max-line-length=120 $(PY_FILES)
	@echo "Checking with mypy..."
	mypy --strict $(PY_FILES)

create_dirs=mkdir -p $(CONTRIB_DIR) $(DECODERS_DIR)

all_reference_decoders: h265_reference_decoder h264_reference_decoder aac_reference_decoder ## build all reference decoders

h265_reference_decoder: ## build H.265 reference decoder
	$(create_dirs)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git --depth=1 | true
	cd $(CONTRIB_DIR)/HM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/HM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release && $(MAKE) -C build TAppDecoder
	find $(CONTRIB_DIR)/HM/bin/umake -name "TAppDecoder" -type f -exec cp {} $(DECODERS_DIR)/ \;

h264_reference_decoder: ## build H.264 reference decoder
	$(create_dirs)
	cd $(CONTRIB_DIR) && git clone https://vcgit.hhi.fraunhofer.de/jct-vc/JM.git --depth=1 | true
	cd $(CONTRIB_DIR)/JM && git stash && git pull && git stash apply | true
	cd $(CONTRIB_DIR)/JM && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-Wno-stringop-truncation -Wno-stringop-overflow" && $(MAKE) -C build ldecod
	find $(CONTRIB_DIR)/JM/bin/umake -name "ldecod" -type f -exec cp {} $(DECODERS_DIR)/ \;

aac_reference_decoder: ## build AAC reference decoder
	if ! test -d $(CONTRIB_DIR)/fdk-aac; \
	then \
		$(create_dirs) && \
		cd $(CONTRIB_DIR) && git clone https://github.com/mstorsjo/fdk-aac.git | true && \
		cd fdk-aac && git checkout -B decoder origin/decoder-example && git merge-base master decoder | true && \
		git rebase master || git checkout --ours .gitignore && git add .gitignore && \
		git rebase --continue || git checkout --ours .gitignore && git add .gitignore && \
		git rebase --continue && git checkout master && git merge decoder | true && \
		sed -i '586a\
		\
		## Program sources \
		\
		set(aac_dec_SOURCES \
			aac-dec.c \
			wavwriter.c \
			wavwriter.h) \
		\
		## Program target \
		add_executable(aac-dec $${aac_dec_SOURCES}) \
		\ \
		## Program target configuration \
		target_link_libraries(aac-dec PRIVATE fdk-aac) \
		target_compile_definitions(aac-dec PRIVATE $$<$$<BOOL:$${MSVC}>:_CRT_SECURE_NO_WARNINGS>) \
		if(WIN32) \
			target_sources(aac-dec PRIVATE win32/getopt.h) \
			target_include_directories(aac-dec PRIVATE win32) \
		endif() \
		\
		## Program target installation \
		install(TARGETS aac-dec RUNTIME DESTINATION $${CMAKE_INSTALL_BINDIR})' CMakeLists.txt; \
	fi
	cd $(CONTRIB_DIR)/fdk-aac && cmake -H. -Bbuild -DCMAKE_BUILD_TYPE=Release -DBUILD_PROGRAMS=1 && $(MAKE) -C build aac-dec
	find $(CONTRIB_DIR)/fdk-aac/build -name "aac-dec" -type f -exec cp {} $(DECODERS_DIR) \;

dbg-%:
	echo "Value of $* = $($*)"

.PHONY: help all_reference_decoders h264_reference_decoder h265_reference_decoder aac_reference_decoder lint check format install_deps
