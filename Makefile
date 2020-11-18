.PHONY: books/librivox.org/%.split_paragraphs
.SECONDARY:

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
		-vf subtitles=f="$*".ass \
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
		-vf subtitles=f="$*"_furi.ass \
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

books/librivox.org/all.json: $(foreach i,$(shell seq 0 15),books/librivox.org/1000_books_starting_from_$(i)000.json)
	code/librivox_concat_book_lists.py $^ > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/librivox.json:
	mkdir -p "$(dir $@)"
	ID=$$(curl 'https://librivox.org/'"$*"'/' |\
		grep -o -e '"https://librivox.org/rss/[0-9]*"' |\
		grep -o -e'[0-9]*' \
	) && \
	curl 'https://librivox.org/api/feed/audiobooks/?id='$$ID'&format=json&extended=1' \
		> "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/files/: books/librivox.org/%/librivox.json
	ARCHIVE_ZIP=$$(code/librivox_archive_zip.py "$<") && \
	wget --no-clobber $$ARCHIVE_ZIP \
		--directory-prefix=$(dir $<)
	unzip $(dir $<)*.zip -d "$@"

books/librivox.org/%/text.txt: books/librivox.org/%/librivox.json
	code/librivox_plain_text.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/youtube-description.txt: books/librivox.org/%/librivox.json
	code/youtube-description.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%/joined.txt: books/librivox.org/%/files/*.txt
	cat $(sort $^) > "$@" \
	|| (rm "$@" && false) # delete in case of failure

null  :=
space := $(null) # The variable reference prevents the space from stripping
pipe  := |

books/librivox.org/%/joined.mp3: books/librivox.org/%/files/*.mp3
	ffmpeg -y -i concat:"$(subst $(space),$(pipe),$(sort $(filter-out %.dynaudnorm.mp3, $^)))" "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.dynaudnorm.mp3: books/librivox.org/%.mp3
	ffmpeg -y -i "$<" -af dynaudnorm=g=5 "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.align.json: books/librivox.org/%.dynaudnorm.mp3 books/librivox.org/%.txt
	LANGUAGE=$$(code/librivox_language.py $(dir $@)) && \
	ascanius $^ 'task_language='$$LANGUAGE'|is_text_type=ruby|dtw_margin=30|mfcc_window_shift=0.02|os_task_file_format=json' "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.ass: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py $(dir $@)) && \
	code/ass.py --language="$$LANGUAGE" "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%_furi.ass: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py $(dir $@)) && \
	code/ass.py --language="$$LANGUAGE" --furigana "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure
	@echo "Press 'Automation' > 'Apply karaoke template'"
	aegisub "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.srt: books/librivox.org/%.align.json
	code/srt.py "$<" > "$@" \
	|| (rm "$@" && false) # delete in case of failure

books/librivox.org/%.split_paragraphs: books/librivox.org/%.align.json
	LANGUAGE=$$(code/librivox_language.py $(dir $@)) && \
	code/find_splits.py --language="$$LANGUAGE" "$<" books/librivox.org/"$*".txt
