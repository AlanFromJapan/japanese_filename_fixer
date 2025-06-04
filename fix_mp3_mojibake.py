import sys
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError
import ftfy
import re
import os

# Regular expression to match the filename format
REGEX_FILENAME_TITLE = r'^(?P<tracknum>\d{0,2})(.*- )?(?P<title>[^-]+)\.mp3$'
verbose = False


def verbose_print(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def fix_title_from_filename(audio, filename):
    match = re.search(REGEX_FILENAME_TITLE, filename)
    if match:
        verbose_print(f"Found match for title in filename: {match.groups()}")
        title = match.group("title").strip()
        if 'title' in audio and audio['title'][0] != title:
            print(f"▶ Updating title from '{audio['title'][0]}' to '{title}'")
            audio['title'] = title
            return True
    return False

def fix_tracknum_from_filename(audio, filename):
    match = re.search(REGEX_FILENAME_TITLE, filename)
    if match:
        verbose_print(f"Found match for tracknum in filename: {match.groups()}")
        tracknum = match.group("tracknum").strip()
        tracknum = str(int(tracknum)) if tracknum.isdigit() else None
        if tracknum is None:
            verbose_print(f"Track number '{tracknum}' is not a valid number, skipping update.")
            return False
        if 'tracknumber' in audio and audio['tracknumber'][0] != tracknum:
            print(f"▶ Updating tracknumber from '{audio['tracknumber'][0]}' to '{tracknum}'")
            audio['tracknumber'] = tracknum
            return True
    return False


def fix_album_from_filename(audio, filename):
    album = os.path.basename(os.path.dirname(filename))
    if 'album' in audio and audio['album'][0] != album:
        print(f"▶ Updating album from '{audio['album'][0]}' to '{album}'")
        audio['album'] = album
        return True
    return False


def fix_artist_from_filename(audio, filename):
    artist = os.path.basename(os.path.dirname(os.path.dirname(filename)))
    if 'artist' in audio and audio['artist'][0] != artist:
        print(f"▶ Updating artist from '{audio['artist'][0]}' to '{artist}'")
        audio['artist'] = artist
        return True
    return False


def fix_mp3_tags(filename, dry_run=False):
    try:
        audio = EasyID3(filename)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(filename)
        audio = EasyID3(filename)

    changed = False

    #ORDER MATTERS as python optimizes the boolean evaluation from the left
    filename_only = os.path.basename(filename)
    changed = fix_title_from_filename(audio, filename_only) or changed
    changed = fix_tracknum_from_filename(audio, filename_only) or changed
    changed = fix_album_from_filename(audio, filename) or changed
    changed = fix_artist_from_filename(audio, filename) or changed

    updating = changed and not dry_run
    if updating:
        audio.save()
        print(f"▶ Tags fixed and saved for {filename}")
    else:
        verbose_print(f"No changes needed for {filename}")
    
    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - ")

    return 1 if updating else 0




def process_folder(folder, dry_run=False):
    count = 0
    update_count = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.mp3'):
                full_path = os.path.join(root, file)
                print(f"\nProcessing: {full_path}")
                update_count += fix_mp3_tags(full_path, dry_run=dry_run)
                count += 1
        for dir in dirs:
            c, u = process_folder(os.path.join(root, dir), dry_run=dry_run)
            count += c
            update_count += u
    return count, update_count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
"""Usage: python fix_mp3_mojibake.py [options] <FOLDER>
options:
    -dry-run: Do not save changes, just print what would be done.
                            """)
        sys.exit(1)

    dry_run = False
    if  '-dry-run' in sys.argv:
        print("Dry run mode: no changes will be saved.")
        dry_run = True
    if '-v' in sys.argv:
        verbose = True
        print("Verbose mode enabled.")
    count, updated = process_folder(sys.argv[-1], dry_run=dry_run)
    print(f"\nProcessed {count} MP3 files, updated {updated}.")