.PHONY: setup books/librivox.org/%.split_paragraphs
.SECONDARY:

VENV_PY := virtualenv/bin/python
VENV_PIP := $(VENV_PY) -m pip

$(VENV_PY):
	python3 -m venv virtualenv
	$(VENV_PIP) install wheel

setup: $(VENV_PY)
	$(VENV_PIP) install -r requirements.txt

requirements.lock: requirements.txt $(VENV_PY)
	echo > "$@" # empty constraints
	$(VENV_PIP) install --upgrade -r "$<"
	$(VENV_PIP) freeze > "$@"

assets/background_full_hd.png: assets/CC0_button.png assets/logo.png
	convert -size 1920x1080 xc:black \
		-gravity Northeast -draw "image over 0,0 0,0 'assets/CC0_button.png'" \
		-gravity Southwest -draw "image over 0,0 0,0 'assets/logo.png'" \
		"$@"

assets/background_tiny.png: assets/background_full_hd.png
	convert "$<" -resize 10% "$@"

%_full_hd.mkv: assets/background_full_hd.png %.mp3 %.ass
	ffmpeg -y \
		-loop 1 -i "$<" \
		-i "$*".mp3 \
		-vf ass=f="$*".ass \
		-shortest \
		-pix_fmt yuvj420p \
		"$@" \
	|| (rm "$@" && false) # delete in case of failure

%_tiny.mkv: assets/background_tiny.png %.mp3 %.ass
	RUNTIME=$$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$*".mp3) && \
	ffmpeg -y \
		-loop 1 -i "$<" \
		-i "$*".mp3 \
		-i "$*".ass \
		-t "$$RUNTIME" \
		-pix_fmt yuvj420p \
		"$@" \
	|| (rm "$@" && false) # delete in case of failure

%_full_hd_furi.mkv: assets/background_full_hd.png %.mp3 %_furi.ass
	ffmpeg -y \
		-loop 1 -i "$<" \
		-i "$*".mp3 \
		-vf ass=f="$*"_furi.ass \
		-shortest \
		-pix_fmt yuvj420p \
		"$@" \
	|| (rm "$@" && false) # delete in case of failure

%_tiny_furi.mkv: assets/background_tiny.png %.mp3 %_furi.ass
	RUNTIME=$$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$*".mp3) && \
	ffmpeg -y \
		-loop 1 -i "$<" \
		-i "$*".mp3 \
		-i "$*"_furi.ass \
		-t "$$RUNTIME" \
		-pix_fmt yuvj420p \
		"$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/1000_books_starting_from_%.json:
	curl 'https://librivox.org/api/feed/audiobooks/?limit=1000&offset='$*'&format=json&fields=\{id,language,url_librivox,url_text_source,totaltimesecs\}' \
		> "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/all.json: $(foreach i,$(shell seq 0 16),books/librivox.org/1000_books_starting_from_$(i)000.json)
	code/librivox_concat_book_lists.py $^ > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/multilingual_ids.txt: books/librivox.org/all.json
	code/librivox_multilingual_ids.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/all_with_multilingual_sections.json: books/librivox.org/all.json books/librivox.org/multilingual_ids.txt
	cat books/librivox.org/multilingual_ids.txt | while read ID; do \
		curl 'https://librivox.org/api/feed/audiobooks/?id='$$ID'&format=json&extended=1' \
			> books/librivox.org/multilingual_"$$ID".json; \
	done; \
	code/librivox_concat_book_lists.py books/librivox.org/all.json books/librivox.org/multilingual_*.json > "$@" \
	|| (rm "$@" && false) # delete in case of failure
	rm books/librivox.org/multilingual_*.json

books/librivox.org/%/librivox.json:
	mkdir -p "$(dir $@)"
	ID=$$(curl 'https://librivox.org/'"$*"'/' |\
		grep -o -e '"https://librivox.org/rss/[0-9]*"' |\
		grep -o -e'[0-9]*' \
	) && \
	curl 'https://librivox.org/api/feed/audiobooks/?id='$$ID'&format=json&extended=1' \
		> "$@" && \
	code/librivox_json.py "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/files/: books/librivox.org/%/librivox.json
	ARCHIVE_ZIP=$$(code/librivox_archive_zip.py "$<") && \
	wget --no-clobber $$ARCHIVE_ZIP \
		--directory-prefix=$(dir $<)
	unzip $(dir $<)*.zip -d "$@"

books/librivox.org/%/text.txt: books/librivox.org/%/librivox.json
	code/librivox_plain_text.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.text.txt:
	code/librivox_plain_text.py "$@" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.youtube-description:
	code/youtube-description.py "$@"

books/librivox.org/%/joined.txt: books/librivox.org/%/files/*.txt
	cat $(sort $^) > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.cmn-Hans.txt: books/librivox.org/%.txt data/cc-cedict.txt
	code/transliterate.py cmn-Hans "$<" "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/joined.cmn-Hans.mp3: books/librivox.org/%/joined.mp3
	cp "$<" "$@"

null  :=
space := $(null) # The variable reference prevents the space from stripping
pipe  := |

books/librivox.org/%/joined.mp3: books/librivox.org/%/files/*.mp3
	ffmpeg -y -i concat:"$(subst $(space),$(pipe),$(sort $(filter-out %.dynaudnorm.mp3, $^)))" "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.dynaudnorm.mp3: books/librivox.org/%.mp3
	# setting framelen and gausssize
	ffmpeg -y -i "$<" -af dynaudnorm=f=300:g=3 "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.align.json: books/librivox.org/%.dynaudnorm.mp3 books/librivox.org/%.txt
	LANGUAGE=$$(code/librivox_language.py "$<") && \
	ascanius $^ 'task_language='$$LANGUAGE'|is_text_type=ruby|dtw_margin=30|mfcc_window_shift=0.02|os_task_file_format=json' "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.ass: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py "$@") && \
	code/ass.py --language="$$LANGUAGE" "$<" "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%_furi.ass: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py "$@") && \
	code/ass.py --language="$$LANGUAGE" --furigana "$<" "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.srt: books/librivox.org/%.align.json
	code/srt.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.split_paragraphs: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py "$@") && \
	code/find_splits.py --language="$$LANGUAGE" "$<" books/librivox.org/"$*".txt

data/cc-cedict.txt:
	mkdir -p data/
	curl 'https://cc-cedict.org/editor/editor_export_cedict.php' > "$@" \
	|| (rm "$@" && false) # delete in case of failure
