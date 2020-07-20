#!/usr/bin/env bash

echo "Starting Pipeline"
echo ""
echo ""
echo ""
# for dir in /Users/tannon/switchdrive/Horizonte/Tannon/XML_article_boundaries/*; do lang="$(basename $dir)"
# python3 correctXML/correct_xml.py -i $dir -o /Users/tannon/switchdrive/Horizonte/Tannon/XML_corrected/$lang/
# done
echo "Starting Content Extraction..."
for dir in /Users/tannon/switchdrive/Horizonte/Tannon/XML_corrected/*; do lang="$(basename $dir)"
python3 content_extraction/text_extractor.py -i $dir -o /Users/tannon/switchdrive/Horizonte/Tannon/XML_extracted/$lang/
done
wait
echo "Starting Corpus XML construction..."
for dir in /Users/tannon/switchdrive/Horizonte/Tannon/XML_extracted/*; do lang="$(basename $dir)"
python3 constructCorpusXML/corpusXML.py -i $dir -o /Users/tannon/switchdrive/Horizonte/Tannon/XML_corpus/$lang/
done
wait
echo "Pipeline Finished"
