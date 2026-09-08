# Kettlebell guide

`kettlebell_guide.md` covers 19 kettlebell exercises ranked S down to
E, with technique cues, common mistakes, photographs and links to a
tutorial video for each one. `kettlebell_guide.pdf` is the same
document laid out for US Letter with 0.7 inch margins.

## Rebuilding it

Three scripts, run in order from this directory:

```bash
python3 s1_download_images.py    # fetch photos and thumbnails
python3 s2_clean_images.py       # crop, resize, standardize
python3 s3_make_pdf.py           # markdown -> PDF
```

`s1` pulls technique photographs from Wikimedia Commons and video
thumbnails from YouTube into `images/`. It skips files it already
has, so re-running is cheap. Use `--force` to refetch everything.
Wikimedia throttles bursts, so the script waits between photos and
backs off on a 429.

`s2` crops the wide gym shots down to the lifter, then puts every
image on the same 640x480 white canvas so the pictures line up down
the page. It backs `images/` up to `~/backups` first and keeps the
three most recent backups.

`s3` renders the Markdown with WeasyPrint. Page size and margins live
in `styles.css`, not in the Python.

Requirements: `pip install markdown weasyprint` and
`brew install imagemagick`.

## Sources and licensing

Technique photographs come from Wikimedia Commons, mostly CC BY-SA
4.0 by Taco Fleur of Cavemantraining. Credits are listed at the end
of the guide. The rest of the pictures are YouTube thumbnails used as
clickable links to the videos they belong to.
