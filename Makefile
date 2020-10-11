

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
		"$@"

%_tiny.mkv: assets/background_tiny.png %.mp3 %.ass
	ffmpeg -y \
		-loop 1 -i "$<" \
		-i "$*".mp3 \
		-i "$*".ass \
		-t "$(shell ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$*".mp3)" \
		-pix_fmt yuvj420p \
		"$@"
