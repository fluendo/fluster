check:
	scripts/check.sh

h265_reference_decoder:
	git clone https://vcgit.hhi.fraunhofer.de/jct-vc/HM.git | true
	cd HM && git pull
	cd HM && cmake .
	cd HM %% make TAppDecoder -j
	find HM/bin/* -name 'TAppDecoder' -exec cp "{}" HM/bin/  \;
